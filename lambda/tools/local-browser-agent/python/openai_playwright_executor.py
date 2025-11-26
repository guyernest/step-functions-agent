#!/usr/bin/env python3
"""
OpenAI + Playwright Direct Executor

A purpose-built browser automation executor that combines:
- Playwright for explicit, reliable browser control
- OpenAI Vision API for intelligent screenshot analysis and extraction
- Full control over prompts and responses
- Support for multiple LLM providers (OpenAI, Claude, Gemini)

Template Format:
{
  "name": "Script name",
  "description": "What the script does",
  "starting_page": "https://example.com",
  "llm_provider": "openai",  // "openai", "claude", "gemini"
  "llm_model": "gpt-4o-mini",  // Model name
  "abort_on_error": false,
  "session": {
    "profile_name": "my-profile",
    "clone_for_parallel": false
  },
  "steps": [
    {
      "type": "navigate",
      "description": "Go to page",
      "url": "https://example.com/path"
    },
    {
      "type": "click",
      "description": "Click button",
      "locator": {
        "strategy": "role",  // "role", "selector", "text", "xpath", "coordinates"
        "value": "button[name='Submit']",
        "nth": 0  // Optional: disambiguate multiple matches
      }
    },
    {
      "type": "fill",
      "description": "Enter text",
      "locator": {"strategy": "selector", "value": "#input-field"},
      "value": "{{variable_name}}"  // Supports template variables
    },
    {
      "type": "wait",
      "description": "Wait for element",
      "locator": {"strategy": "selector", "value": ".result"},
      "timeout": 5000
    },
    {
      "type": "screenshot",
      "description": "Take screenshot",
      "save_to": "step_1_screenshot.png"  // Optional
    },
    {
      "type": "extract",
      "description": "Extract data using vision",
      "method": "vision",  // "vision" or "dom"
      "prompt": "Extract the price and availability from this page",
      "schema": {
        "type": "object",
        "properties": {
          "price": {"type": "number"},
          "available": {"type": "boolean"}
        }
      }
    },
    {
      "type": "execute_js",
      "description": "Run custom JavaScript",
      "script": "return document.title;"
    }
  ]
}
"""

import os
import sys
import json
import base64
import traceback
import random
from typing import Dict, Any, Optional, List, Literal, Union
from pathlib import Path
import asyncio

import boto3
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from openai import OpenAI

# Import progressive escalation engine
from progressive_escalation_engine import ProgressiveEscalationEngine, EscalationExhaustedError
from workflow_executor import WorkflowExecutor, WorkflowError

# Import workflow executor
from workflow_executor import WorkflowExecutor

# Flag for optional LLM providers (imported on-demand)
ANTHROPIC_AVAILABLE = False
GEMINI_AVAILABLE = False


class OpenAIPlaywrightExecutor:
    """
    Direct OpenAI + Playwright executor for intelligent browser automation

    Features:
    - Explicit Playwright locators (reliable, fast)
    - OpenAI vision for intelligent extraction
    - Multiple LLM provider support
    - Coordinate-based fallback
    - Full prompt control
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-mini",
        llm_api_key: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        aws_profile: str = "browser-agent",
        headless: bool = False,
        browser_channel: Optional[str] = None,
        user_data_dir: Optional[Path] = None,
        navigation_timeout: int = 60000,
    ):
        self.llm_provider = llm_provider.lower()
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.s3_bucket = s3_bucket
        self.aws_profile = aws_profile
        self.headless = headless
        self.browser_channel = browser_channel
        self.user_data_dir = user_data_dir
        self.navigation_timeout = navigation_timeout

        # LLM client (lazy-initialized when needed)
        self.llm_client = None

        # Initialize AWS session if S3 bucket provided
        if s3_bucket:
            self.boto_session = boto3.Session(profile_name=aws_profile)

        # Playwright objects (initialized in execute_script)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Execution state
        self.variables = {}  # For template variable substitution
        self.screenshots = []
        self.verification_screenshots = []  # Screenshots marked for inclusion in result
        self.escalation_engine: Optional[ProgressiveEscalationEngine] = None
        # Internal counter for externally-driven workflow steps
        self._workflow_step_counter = 0

        # Default delay between actions (can be overridden per-step or at script level)
        self.default_delay = 0

        # Screenshot upload configuration
        self.s3_prefix = "verification"  # Default S3 prefix for screenshots
        self.execution_id = None  # Will be set from variables or generated
        self.local_screenshot_dir = None  # For local testing mode

    def _compute_delay(self, delay_config: Union[int, Dict[str, int], None], script_default: int = 0) -> int:
        """
        Compute delay in milliseconds from various config formats.

        Supports:
        - None: Use script default
        - int: Fixed delay in ms
        - {"min": 100, "max": 500}: Random delay in range

        Args:
            delay_config: Delay configuration from step
            script_default: Default delay from script level

        Returns:
            Delay in milliseconds
        """
        if delay_config is None:
            return script_default

        if isinstance(delay_config, int):
            return delay_config

        if isinstance(delay_config, dict):
            min_delay = delay_config.get("min", 0)
            max_delay = delay_config.get("max", min_delay)
            return random.randint(min_delay, max_delay)

        return script_default

    async def _check_retry_condition(self, retry_if: Dict[str, Any]) -> bool:
        """
        Check if retry condition is met.

        Supports:
        - element_visible: "selector" - retry if element is visible
        - element_not_visible: "selector" - retry if element is NOT visible
        - text_visible: "text" - retry if text is visible on page
        - text_not_visible: "text" - retry if text is NOT visible

        Returns:
            True if should retry, False otherwise
        """
        if not retry_if:
            return True  # No condition = always retry

        try:
            if "element_visible" in retry_if:
                selector = retry_if["element_visible"]
                locator = self.page.locator(selector)
                is_visible = await locator.is_visible()
                print(f"  ↳ Retry condition: element_visible('{selector}') = {is_visible}", file=sys.stderr)
                return is_visible

            if "element_not_visible" in retry_if:
                selector = retry_if["element_not_visible"]
                locator = self.page.locator(selector)
                is_visible = await locator.is_visible()
                print(f"  ↳ Retry condition: element_not_visible('{selector}') = {not is_visible}", file=sys.stderr)
                return not is_visible

            if "text_visible" in retry_if:
                text = retry_if["text_visible"]
                locator = self.page.get_by_text(text, exact=False)
                is_visible = await locator.first.is_visible()
                print(f"  ↳ Retry condition: text_visible('{text}') = {is_visible}", file=sys.stderr)
                return is_visible

            if "text_not_visible" in retry_if:
                text = retry_if["text_not_visible"]
                locator = self.page.get_by_text(text, exact=False)
                try:
                    is_visible = await locator.first.is_visible()
                except:
                    is_visible = False
                print(f"  ↳ Retry condition: text_not_visible('{text}') = {not is_visible}", file=sys.stderr)
                return not is_visible

        except Exception as e:
            print(f"  ↳ Retry condition check failed: {e}", file=sys.stderr)
            return True  # On error, allow retry

        return True  # Default: retry

    async def _find_form_field(self, label: str, field_type: str = "input") -> Any:
        """
        Smart form field finder that handles modern CSS frameworks.

        Tries multiple strategies in order of specificity:
        1. ID match (normalized label)
        2. Name attribute match
        3. Placeholder text match
        4. Angular Material pattern
        5. MUI (Material UI) pattern
        6. Generic label association
        7. Aria-label match
        8. Has-text proximity

        Args:
            label: The label text to search for (e.g., "PostCode", "Email Address")
            field_type: Type of field to find ("input", "textarea", "select")

        Returns:
            Playwright locator for the found field

        Raises:
            Exception if no field found after all strategies
        """
        # Normalize label for ID/name matching
        normalized = label.lower().replace(' ', '').replace('*', '').replace(':', '').strip()
        # Also try with underscores and hyphens
        normalized_underscore = label.lower().replace(' ', '_').replace('*', '').replace(':', '').strip()
        normalized_hyphen = label.lower().replace(' ', '-').replace('*', '').replace(':', '').strip()

        # Strategy chain - ordered by specificity and reliability
        strategies = [
            # 1. Direct ID match (most reliable if present)
            (f"#{normalized}", f"ID #{normalized}"),
            (f"#{normalized_underscore}", f"ID #{normalized_underscore}"),
            (f"#{normalized_hyphen}", f"ID #{normalized_hyphen}"),

            # 2. Name attribute match
            (f"{field_type}[name='{normalized}']", f"name='{normalized}'"),
            (f"{field_type}[name='{normalized_underscore}']", f"name='{normalized_underscore}'"),
            (f"{field_type}[name*='{normalized}' i]", f"name contains '{normalized}'"),

            # 3. Placeholder text match
            (f"{field_type}[placeholder*='{label}' i]", f"placeholder contains '{label}'"),

            # 4. Angular Material patterns
            (f".mat-form-field:has-text('{label}') {field_type}", f"Angular Material .mat-form-field"),
            (f"mat-form-field:has-text('{label}') {field_type}", f"Angular Material mat-form-field"),
            (f".mat-form-field-infix:has-text('{label}') {field_type}", f"Angular Material .mat-form-field-infix"),

            # 5. MUI (Material UI) patterns
            (f".MuiFormControl-root:has-text('{label}') {field_type}", f"MUI .MuiFormControl-root"),
            (f".MuiTextField-root:has-text('{label}') {field_type}", f"MUI .MuiTextField-root"),

            # 6. Generic label association patterns
            (f"label:has-text('{label}') + {field_type}", f"label sibling (+)"),
            (f"label:has-text('{label}') ~ {field_type}", f"label sibling (~)"),
            (f"label[for]:has-text('{label}')", f"label with for attribute"),  # Will resolve via for->id

            # 7. Aria-label match
            (f"{field_type}[aria-label*='{label}' i]", f"aria-label contains '{label}'"),

            # 8. Common form wrapper patterns
            (f".form-field:has-text('{label}') {field_type}", f".form-field wrapper"),
            (f".form-group:has-text('{label}') {field_type}", f".form-group wrapper"),
            (f".field:has-text('{label}') {field_type}", f".field wrapper"),
            (f"div:has-text('{label}') > {field_type}", f"direct child of div"),

            # 9. Broader proximity search (last resort before vision)
            (f":has-text('{label}') >> {field_type}:visible", f"proximity search"),
        ]

        for selector, strategy_name in strategies:
            try:
                locator = self.page.locator(selector).first
                # Quick visibility check with short timeout
                is_visible = await locator.is_visible()
                if is_visible:
                    print(f"  ✓ Found form field '{label}' using: {strategy_name}", file=sys.stderr)
                    return locator
            except Exception:
                continue

        # Special handling for label[for] - resolve the for attribute to find input by ID
        try:
            for_value = await self.page.locator(f"label:has-text('{label}')").first.get_attribute("for")
            if for_value:
                locator = self.page.locator(f"#{for_value}")
                if await locator.is_visible():
                    print(f"  ✓ Found form field '{label}' using: label[for='{for_value}'] -> #{for_value}", file=sys.stderr)
                    return locator
        except Exception:
            pass

        raise Exception(f"Could not find form field with label '{label}' using any strategy")

    async def _upload_single_screenshot(self, filename: str, screenshot_bytes: bytes, step: Dict[str, Any] = None) -> str:
        """
        Upload a single screenshot to S3 and return the URI.

        Args:
            filename: Name of the screenshot file
            screenshot_bytes: PNG image data
            step: Optional step config for custom S3 prefix

        Returns:
            S3 URI of the uploaded screenshot
        """
        if not self.s3_bucket:
            raise Exception("S3 bucket not configured for screenshot upload")

        s3_client = self.boto_session.client('s3')

        # Get S3 prefix from step config or use default
        s3_prefix = self.s3_prefix
        if step and step.get("s3_prefix"):
            s3_prefix = step["s3_prefix"]

        # Generate execution ID if not set
        if not self.execution_id:
            import time
            self.execution_id = f"exec_{int(time.time())}"

        # Build S3 key
        s3_key = f"{s3_prefix}/{self.execution_id}/{filename}"

        print(f"  📤 Uploading screenshot to s3://{self.s3_bucket}/{s3_key}", file=sys.stderr)

        s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Body=screenshot_bytes,
            ContentType='image/png',
        )

        s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
        print(f"  ✓ Screenshot uploaded: {s3_uri}", file=sys.stderr)

        return s3_uri

    async def _save_screenshot_locally(self, filename: str, screenshot_bytes: bytes) -> str:
        """
        Save a screenshot to the local filesystem (for testing without S3).

        Args:
            filename: Name of the screenshot file
            screenshot_bytes: PNG image data

        Returns:
            Local file path of the saved screenshot
        """
        from pathlib import Path

        # Use configured directory or default to ./screenshots
        local_dir = Path(self.local_screenshot_dir) if self.local_screenshot_dir else Path("./screenshots")
        local_dir.mkdir(parents=True, exist_ok=True)

        # Generate execution ID subdirectory
        if not self.execution_id:
            import time
            self.execution_id = f"exec_{int(time.time())}"

        exec_dir = local_dir / self.execution_id
        exec_dir.mkdir(parents=True, exist_ok=True)

        local_path = exec_dir / filename
        local_path.write_bytes(screenshot_bytes)

        print(f"  💾 Screenshot saved locally: {local_path}", file=sys.stderr)

        return str(local_path)

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Public step executor used by WorkflowExecutor.

        Maintains an internal step counter for logging and result consistency.

        Supports:
        - delay: Wait before executing (int ms or {"min": x, "max": y})
        - retry: Retry configuration with optional conditions
          - attempts: Number of retry attempts
          - delay_ms: Delay between retries
          - retry_if: Conditional retry (element_visible, text_visible, etc.)
        """
        self._workflow_step_counter += 1

        # Apply pre-action delay (human-like timing)
        step_delay = self._compute_delay(step.get("delay"), self.default_delay)
        if step_delay > 0:
            print(f"  ⏳ Waiting {step_delay}ms before action...", file=sys.stderr)
            await asyncio.sleep(step_delay / 1000.0)

        # Support per-step retry with optional conditions
        retry_cfg = step.get("retry", {}) or {}
        attempts = int(retry_cfg.get("attempts", 1))
        retry_delay_ms = int(retry_cfg.get("delay_ms", 500))
        retry_if = retry_cfg.get("retry_if", {})

        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                res = await self._execute_step(step, self._workflow_step_counter)
            except Exception as e:
                last_exc = e
                res = {"success": False, "error": str(e), "exception": True}

            if res.get("success"):
                return res

            # Check if we should retry based on conditions
            if attempt < attempts:
                should_retry = await self._check_retry_condition(retry_if)
                if should_retry:
                    print(f"  ↻ Step failed (attempt {attempt}/{attempts}). Retrying after {retry_delay_ms}ms...", file=sys.stderr)
                    await asyncio.sleep(retry_delay_ms / 1000.0)
                else:
                    print(f"  ✗ Retry condition not met, stopping retries", file=sys.stderr)
                    break

        if last_exc:
            res["traceback"] = traceback.format_exc()
        return res

    def _ensure_llm_client(self):
        """Ensure LLM client is initialized (lazy initialization)"""
        if self.llm_client is not None:
            return self.llm_client

        return self._init_llm_client(self.llm_api_key)

    def _init_llm_client(self, api_key: Optional[str]):
        """Initialize LLM client based on provider"""
        if self.llm_provider == "openai":
            self.llm_client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
            return self.llm_client
        elif self.llm_provider == "claude":
            try:
                from anthropic import Anthropic
                self.llm_client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
                return self.llm_client
            except ImportError:
                raise ValueError("Anthropic library not installed. Install with: pip install anthropic")
        elif self.llm_provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
                self.llm_client = genai
                return self.llm_client
            except ImportError:
                raise ValueError("Google Generative AI library not installed. Install with: pip install google-generativeai")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    async def execute_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a browser automation script

        Args:
            script: Script dictionary with steps

        Returns:
            Execution result with step outputs
        """
        name = script.get("name", "Unnamed Script")
        description = script.get("description", "")
        starting_page = script.get("starting_page")
        abort_on_error = script.get("abort_on_error", False)
        steps = script.get("steps", [])

        # Override LLM settings if specified in script
        if "llm_provider" in script:
            self.llm_provider = script["llm_provider"]
        if "llm_model" in script:
            self.llm_model = script["llm_model"]

        # Set default delay between actions (human-like timing)
        # Can be overridden per-step with "delay" field
        self.default_delay = script.get("default_delay", 0)

        # Screenshot configuration
        screenshot_config = script.get("screenshot_config", {})
        self.s3_prefix = screenshot_config.get("s3_prefix", "verification")
        self.local_screenshot_dir = screenshot_config.get("local_dir", None)

        # Set execution ID from variables, script, or generate one
        import time
        self.execution_id = (
            self.variables.get("execution_id") or
            script.get("execution_id") or
            f"exec_{name.replace(' ', '_').lower()}_{int(time.time())}"
        )

        # Reset verification screenshots for this execution
        self.verification_screenshots = []

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"OpenAI Playwright Executor", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Script: {name}", file=sys.stderr)
        print(f"Description: {description}", file=sys.stderr)
        print(f"LLM: {self.llm_provider} ({self.llm_model})", file=sys.stderr)
        print(f"Starting Page: {starting_page}", file=sys.stderr)
        print(f"Total Steps: {len(steps)}", file=sys.stderr)
        print(f"Execution ID: {self.execution_id}", file=sys.stderr)
        if self.s3_bucket:
            print(f"Screenshots: s3://{self.s3_bucket}/{self.s3_prefix}/{self.execution_id}/", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        result = {
            "success": True,
            "script_name": name,
            "steps_executed": 0,
            "steps_total": len(steps),
            "step_results": [],
            "screenshots": [],
            "error": None,
        }

        try:
            # Initialize Playwright
            await self._init_browser()

            # Navigate to starting page
            if starting_page:
                print(f"→ Navigating to {starting_page}", file=sys.stderr)
                await self.page.goto(starting_page, wait_until="networkidle", timeout=self.navigation_timeout)

            # Check if this is a workflow script (contains control flow steps)
            workflow_step_types = {"if", "try", "sequence", "goto", "switch"}
            has_workflow = any(step.get("type") in workflow_step_types for step in steps)

            if has_workflow:
                # Use WorkflowExecutor for scripts with control flow
                print(f"→ Detected workflow script - using WorkflowExecutor", file=sys.stderr)
                workflow_executor = WorkflowExecutor(script, self)
                await workflow_executor.run()

                # Update result with workflow execution stats and results
                result["steps_executed"] = workflow_executor.total_steps_executed
                result["execution_mode"] = "workflow"
                result["step_results"] = workflow_executor.step_results
                result["screenshots"] = workflow_executor.screenshots
                print(f"→ Workflow collected {len(workflow_executor.step_results)} step results", file=sys.stderr)
                print(f"→ Workflow collected {len(workflow_executor.screenshots)} screenshots", file=sys.stderr)
                if self.escalation_engine is not None:
                    try:
                        result["escalation_stats"] = self.escalation_engine.get_stats()
                    except Exception:
                        pass
            else:
                # Use traditional linear execution for backward compatibility
                await self._execute_linear_steps(steps, result, abort_on_error, name)
                if self.escalation_engine is not None:
                    try:
                        result["escalation_stats"] = self.escalation_engine.get_stats()
                    except Exception:
                        pass

        except Exception as e:
            print(f"\n✗ Script Execution Failed: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            result["success"] = False
            result["error"] = str(e)
        finally:
            # Cleanup
            await self._cleanup_browser()

        return result

    async def _execute_linear_steps(self, steps: List[Dict[str, Any]], result: Dict[str, Any], abort_on_error: bool, name: str):
        """Execute steps linearly without workflow control flow (backward compatible)."""
        for idx, step in enumerate(steps):
                step_num = idx + 1
                step_type = step.get("type")
                step_desc = step.get("description", f"Step {step_num}")

                print(f"\n[Step {step_num}/{len(steps)}] {step_type}: {step_desc}", file=sys.stderr)

                try:
                    # Apply pre-action delay (human-like timing)
                    step_delay = self._compute_delay(step.get("delay"), self.default_delay)
                    if step_delay > 0:
                        print(f"  ⏳ Waiting {step_delay}ms before action...", file=sys.stderr)
                        await asyncio.sleep(step_delay / 1000.0)

                    # Optional per-step retry policy with conditions
                    retry_cfg = step.get("retry", {}) or {}
                    attempts = int(retry_cfg.get("attempts", 1))
                    retry_delay_ms = int(retry_cfg.get("delay_ms", 500))
                    retry_if = retry_cfg.get("retry_if", {})

                    last_exc = None
                    for attempt in range(1, attempts + 1):
                        try:
                            step_result = await self._execute_step(step, step_num)
                        except Exception as e:
                            last_exc = e
                            step_result = {"success": False, "error": str(e), "exception": True}

                        if step_result.get("success"):
                            break

                        # Check if we should retry based on conditions
                        if attempt < attempts:
                            should_retry = await self._check_retry_condition(retry_if)
                            if should_retry:
                                print(f"  ↻ Step failed (attempt {attempt}/{attempts}). Retrying after {retry_delay_ms}ms...", file=sys.stderr)
                                await asyncio.sleep(retry_delay_ms / 1000.0)
                            else:
                                print(f"  ✗ Retry condition not met, stopping retries", file=sys.stderr)
                                break

                    if not step_result.get("success") and last_exc:
                        step_result["traceback"] = traceback.format_exc()
                    step_result["step_number"] = step_num
                    step_result["description"] = step_desc
                    result["step_results"].append(step_result)
                    result["steps_executed"] += 1

                    # Log step completion with status and key details
                    if step_result["success"]:
                        status_icon = "✓"
                        status_text = "SUCCESS"

                        # Add step-specific details to logging
                        details = []
                        if step_type == "click" and step_result.get("method"):
                            details.append(f"method={step_result['method']}")
                        if step_type == "fill" and step_result.get("value"):
                            details.append(f"filled={len(step_result['value'])} chars")
                        if step_type == "press" and step_result.get("keys"):
                            details.append(f"keys={step_result['keys']}")
                            if step_result.get("delay_ms"):
                                details.append(f"delay={step_result['delay_ms']}ms")
                        if step_type == "wait" and step_result.get("duration"):
                            details.append(f"duration={step_result['duration']}ms")
                        if step_type == "execute_js" and step_result.get("result"):
                            js_result = step_result['result']
                            if isinstance(js_result, dict):
                                # Show boolean values for important checks
                                bool_values = {k: v for k, v in js_result.items() if isinstance(v, bool)}
                                if bool_values:
                                    bool_str = ", ".join([f"{k}={v}" for k, v in bool_values.items()])
                                    details.append(bool_str)
                                # Show numeric values
                                num_values = {k: v for k, v in js_result.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
                                if num_values:
                                    num_str = ", ".join([f"{k}={v}" for k, v in num_values.items()])
                                    details.append(num_str)
                                # Always show keys for reference
                                details.append(f"result={list(js_result.keys())}")
                            else:
                                details.append(f"result={type(js_result).__name__}")
                        if step_type == "extract" and step_result.get("data"):
                            details.append(f"extracted={len(step_result['data'])} fields")

                        detail_str = f" ({', '.join(details)})" if details else ""
                        print(f"  {status_icon} {status_text}{detail_str}", file=sys.stderr)
                    else:
                        status_icon = "✗"
                        status_text = "FAILED"
                        error_msg = step_result.get("error", "Unknown error")
                        print(f"  {status_icon} {status_text}: {error_msg}", file=sys.stderr)

                    # Store extracted data as variables
                    if step_result.get("data"):
                        self.variables[f"step_{step_num}_data"] = step_result["data"]

                    if not step_result["success"] and abort_on_error:
                        result["success"] = False
                        result["error"] = f"Step {step_num} failed: {step_result.get('error')}"
                        break

                except Exception as e:
                    error_msg = f"Step {step_num} exception: {str(e)}"
                    print(f"  ✗ EXCEPTION: {error_msg}", file=sys.stderr)

                    result["step_results"].append({
                        "step_number": step_num,
                        "description": step_desc,
                        "success": False,
                        "error": error_msg,
                        "traceback": traceback.format_exc()
                    })

                    if abort_on_error:
                        result["success"] = False
                        result["error"] = error_msg
                        break

                # Upload screenshots to S3 if configured (batch upload for non-immediate screenshots)
                if self.s3_bucket and self.screenshots:
                    result["screenshots"] = await self._upload_screenshots(name)

        # Include verification screenshots in result (for user verification)
        if self.verification_screenshots:
            result["verification_screenshots"] = self.verification_screenshots
            print(f"\n📸 Verification screenshots: {len(self.verification_screenshots)}", file=sys.stderr)
            for vs in self.verification_screenshots:
                loc = vs.get("s3_uri") or vs.get("local_path", "unknown")
                print(f"   • {vs['filename']}: {loc}", file=sys.stderr)

        # Add execution metadata
        result["execution_id"] = self.execution_id

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Execution {'✓ Complete' if result['success'] else '✗ Failed'}", file=sys.stderr)
        print(f"Steps executed: {result['steps_executed']}/{result['steps_total']}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        return result

    async def _init_browser(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()

        browser_type = self.playwright.chromium
        if self.browser_channel == "msedge":
            browser_type = self.playwright.chromium
        elif self.browser_channel == "firefox":
            browser_type = self.playwright.firefox

        # Configure browser arguments and default-arg overrides to allow password manager UI
        # Key points:
        # - Remove --enable-automation so Chromium doesn't suppress sensitive UX (password manager bubbles)
        # - Remove --disable-component-extensions-with-background-pages (password manager UI uses a component extension)
        # - Keep headful mode for password manager prompts
        args = [
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]

        # Some sites check AutomationControlled; keep this flag only in ephemeral sessions
        if not self.user_data_dir:
            args.append("--disable-blink-features=AutomationControlled")

        ignore_default_args = [
            "--enable-automation",
            "--disable-component-extensions-with-background-pages",
        ]

        launch_options = {
            "headless": self.headless,
            "channel": self.browser_channel if self.browser_channel != "chromium" else None,
            "args": args,
            "ignore_default_args": ignore_default_args,
        }

        if self.user_data_dir:
            # Use persistent context with user data directory
            self.context = await browser_type.launch_persistent_context(
                str(self.user_data_dir),
                **launch_options
            )
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        else:
            # Use regular browser
            self.browser = await browser_type.launch(**launch_options)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

        # Set default navigation timeout
        self.page.set_default_navigation_timeout(self.navigation_timeout)

        # Progressive escalation engine will be initialized lazily when needed
        # (to avoid requiring LLM client for non-vision workflows)

    def _ensure_escalation_engine(self):
        """Ensure escalation engine is initialized (lazy initialization)"""
        if self.escalation_engine is not None:
            return self.escalation_engine

        # Ensure LLM client is initialized first
        llm_client = self._ensure_llm_client()

        self.escalation_engine = ProgressiveEscalationEngine(
            self.page,
            llm_client,
            self.llm_model
        )
        return self.escalation_engine

    async def _cleanup_browser(self):
        """Clean up Playwright resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Public interface for WorkflowExecutor to execute individual steps.

        Returns the result dict so WorkflowExecutor can collect step results and screenshots.
        """
        # Delegate to the internal execute method
        result = await self._execute_step(step, step_num=0)

        # Raise exception if step failed (WorkflowExecutor handles failures)
        if not result.get("success"):
            raise Exception(result.get("error", "Step execution failed"))

        # Return result for WorkflowExecutor to collect
        return result

    async def _execute_step(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Execute a single step (internal method)"""
        # Action steps use "action" field, workflow steps use "type" field
        step_type = step.get("action") or step.get("type")

        handlers = {
            "navigate": self._step_navigate,
            "click": self._step_click,
            "fill": self._step_fill,
            "wait": self._step_wait,
            "wait_for_load_state": self._step_wait_for_load_state,
            "screenshot": self._step_screenshot,
            "extract": self._step_extract,
            "execute_js": self._step_execute_js,
            "press": self._step_press,
            "error": self._step_error,
        }

        handler = handlers.get(step_type)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown step type: {step_type}"
            }

        return await handler(step, step_num)

    async def _step_error(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Raise an error with message."""
        message = step.get("message", "Error action triggered")
        raise Exception(message)

    async def _step_navigate(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Navigate to URL"""
        url = self._substitute_variables(step.get("url", ""))

        await self.page.goto(url, wait_until="networkidle", timeout=self.navigation_timeout)

        return {
            "success": True,
            "action": "navigate",
            "url": url,
        }

    async def _step_click(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Click element (with optional escalation)"""
        # Check if this click should trigger autofill (e.g., password managers)
        trigger_autofill = step.get("trigger_autofill", False)

        # Check if escalation chain is provided
        if "escalation_chain" in step:
            # Use progressive escalation to find and click element
            try:
                engine = self._ensure_escalation_engine()
                result = await engine.execute_with_escalation(
                    escalation_chain=step["escalation_chain"],
                    context=self.variables
                )

                # Result contains the locator found by escalation
                # Now click using that locator
                if result.get("method") == "coordinates":
                    # Click by coordinates
                    coords = result.get("value", {})
                    await self.page.mouse.click(coords["x"], coords["y"])
                    click_method = "coordinates"
                elif result.get("locator"):
                    # Click using Playwright locator object (from playwright_locator method)
                    locator = result["locator"]

                    # Heuristic: auto-trigger trusted click for inputs likely to open password manager
                    try:
                        trigger_autofill = trigger_autofill or await self._should_trigger_autofill(locator)
                    except Exception:
                        pass

                    # If trigger_autofill, use real mouse click instead of programmatic click
                    if trigger_autofill:
                        print(f"🖱️  Using real mouse click for autofill (trigger_autofill=true)", file=sys.stderr)
                        await locator.scroll_into_view_if_needed()
                        try:
                            await self.page.bring_to_front()
                        except Exception:
                            pass
                        try:
                            await locator.focus()
                        except Exception:
                            pass

                        # Get element position
                        box = await locator.bounding_box()
                        if box:
                            # Calculate center of element
                            center_x = box["x"] + box["width"] / 2
                            center_y = box["y"] + box["height"] / 2

                            import time
                            t1 = time.time()
                            print(f"🖱️  Moving mouse to ({center_x:.1f}, {center_y:.1f})", file=sys.stderr, flush=True)
                            # Move mouse to element (this triggers hover events)
                            await self.page.mouse.move(center_x, center_y)
                            t2 = time.time()
                            print(f"🖱️  Mouse moved (took {(t2-t1)*1000:.1f}ms)", file=sys.stderr, flush=True)

                            # Wait for hover to register (critical for password managers)
                            print(f"🖱️  Waiting 500ms for hover to register", file=sys.stderr, flush=True)
                            await asyncio.sleep(0.5)
                            t3 = time.time()
                            print(f"🖱️  Hover wait complete (took {(t3-t2)*1000:.1f}ms)", file=sys.stderr, flush=True)

                            # Perform real mouse click with proper press duration
                            # Real clicks have: down -> delay -> up (not instant)
                            print(f"🖱️  Pressing mouse button down", file=sys.stderr, flush=True)
                            await self.page.mouse.down()

                            # Button press duration - real clicks aren't instant
                            await asyncio.sleep(0.1)
                            t4 = time.time()
                            print(f"🖱️  Button held (took {(t4-t3)*1000:.1f}ms)", file=sys.stderr, flush=True)

                            print(f"🖱️  Releasing mouse button", file=sys.stderr, flush=True)
                            await self.page.mouse.up()
                            t5 = time.time()
                            print(f"🖱️  Click complete - total time: {(t5-t1)*1000:.1f}ms", file=sys.stderr, flush=True)

                            click_method = "mouse_click (autofill)"
                        else:
                            print(f"⚠ Could not get bounding box, falling back to locator.click()", file=sys.stderr)
                            await locator.click(timeout=30000)
                            click_method = "locator (fallback)"
                    else:
                        # Use force=True if modal overlays are blocking, and increase timeout
                        try:
                            await locator.click(timeout=30000)
                            click_method = "locator"
                        except Exception as e:
                            # If click fails due to overlays, try force click
                            if "intercepts pointer events" in str(e):
                                print(f"⚠ Modal overlay detected, trying force click", file=sys.stderr)
                                await locator.click(timeout=30000, force=True)
                                click_method = "locator (forced)"
                            else:
                                raise
                elif result.get("method") in ["selector", "text"]:
                    # Click using selector/text from vision_find_element
                    value = result.get("value")
                    if result.get("method") == "selector":
                        locator = self.page.locator(value)
                    else:  # text
                        locator = self.page.get_by_text(value, exact=False)

                    # Heuristic: auto-trigger trusted click for inputs likely to open password manager
                    try:
                        trigger_autofill = trigger_autofill or await self._should_trigger_autofill(locator)
                    except Exception:
                        pass

                    # If trigger_autofill, use real mouse click
                    if trigger_autofill:
                        print(f"🖱️  Using real mouse click for autofill (trigger_autofill=true)", file=sys.stderr)
                        await locator.scroll_into_view_if_needed()
                        try:
                            await self.page.bring_to_front()
                        except Exception:
                            pass
                        try:
                            await locator.focus()
                        except Exception:
                            pass

                        # Get element position
                        box = await locator.bounding_box()
                        if box:
                            # Calculate center of element
                            center_x = box["x"] + box["width"] / 2
                            center_y = box["y"] + box["height"] / 2

                            import time
                            t1 = time.time()
                            print(f"🖱️  Moving mouse to ({center_x:.1f}, {center_y:.1f})", file=sys.stderr, flush=True)
                            # Move mouse to element
                            await self.page.mouse.move(center_x, center_y)
                            t2 = time.time()
                            print(f"🖱️  Mouse moved (took {(t2-t1)*1000:.1f}ms)", file=sys.stderr, flush=True)

                            # Wait for hover to register
                            print(f"🖱️  Waiting 500ms for hover to register", file=sys.stderr, flush=True)
                            await asyncio.sleep(0.5)
                            t3 = time.time()
                            print(f"🖱️  Hover wait complete (took {(t3-t2)*1000:.1f}ms)", file=sys.stderr, flush=True)

                            # Perform real mouse click with proper press duration
                            print(f"🖱️  Pressing mouse button down", file=sys.stderr, flush=True)
                            await self.page.mouse.down()
                            await asyncio.sleep(0.1)  # Button press duration
                            t4 = time.time()
                            print(f"🖱️  Button held (took {(t4-t3)*1000:.1f}ms)", file=sys.stderr, flush=True)
                            print(f"🖱️  Releasing mouse button", file=sys.stderr, flush=True)
                            await self.page.mouse.up()
                            t5 = time.time()
                            print(f"🖱️  Click complete - total time: {(t5-t1)*1000:.1f}ms", file=sys.stderr, flush=True)

                            click_method = f"{result.get('method')}_mouse (autofill)"
                        else:
                            print(f"⚠ Could not get bounding box, falling back to locator.click()", file=sys.stderr)
                            await locator.click(timeout=30000)
                            click_method = f"{result.get('method')} (fallback)"
                    else:
                        try:
                            await locator.click(timeout=30000)
                            click_method = result.get("method")
                        except Exception as e:
                            if "intercepts pointer events" in str(e):
                                print(f"⚠ Modal overlay detected, trying force click", file=sys.stderr)
                                await locator.click(timeout=30000, force=True)
                                click_method = f"{result.get('method')} (forced)"
                            else:
                                raise
                else:
                    raise ValueError("Escalation did not return valid click target")

                return {
                    "success": True,
                    "action": "click",
                    "click_method": click_method,
                    "trigger_autofill": trigger_autofill,
                    "escalation_metadata": result.get("escalation_metadata", {}),
                }

            except EscalationExhaustedError as e:
                return {
                    "success": False,
                    "action": "click",
                    "error": str(e),
                }
        else:
            # Traditional direct locator approach
            locator_config = step.get("locator", {})
            locator = self._get_locator(locator_config)

            # Heuristic: auto-trigger trusted click for inputs likely to open password manager
            try:
                trigger_autofill = trigger_autofill or await self._should_trigger_autofill(locator)
            except Exception:
                pass

            if trigger_autofill:
                await locator.scroll_into_view_if_needed()
                try:
                    await self.page.bring_to_front()
                except Exception:
                    pass
                try:
                    await locator.focus()
                except Exception:
                    pass
                box = await locator.bounding_box()
                if box:
                    center_x = box["x"] + box["width"] / 2
                    center_y = box["y"] + box["height"] / 2
                    await self.page.mouse.move(center_x, center_y)
                    await asyncio.sleep(0.5)
                    await self.page.mouse.down()
                    await asyncio.sleep(0.1)
                    await self.page.mouse.up()
                    click_method = "mouse_click (autofill)"
                else:
                    await locator.click(timeout=30000)
                    click_method = "locator (fallback)"
            else:
                try:
                    await locator.click(timeout=10000)
                    click_method = "locator"
                except Exception as e:
                    if "intercepts pointer events" in str(e):
                        await locator.click(timeout=10000, force=True)
                        click_method = "locator (forced)"
                    else:
                        raise

            return {
                "success": True,
                "action": "click",
                "locator": locator_config,
            }

    async def _should_trigger_autofill(self, locator) -> bool:
        """Determine if clicking this element should be a trusted mouse click.

        Heuristics:
        - input[type=password]
        - input with autocomplete indicating username/email/password
        - input[type=text|email] with name/id hints (user, email, login)
        """
        try:
            element_info = await locator.evaluate("(el) => ({\n                tag: el.tagName.toLowerCase(),\n                type: (el.getAttribute('type') || '').toLowerCase(),\n                autocomplete: (el.getAttribute('autocomplete') || '').toLowerCase(),\n                name: (el.getAttribute('name') || '').toLowerCase(),\n                id: (el.getAttribute('id') || '').toLowerCase(),\n                role: (el.getAttribute('role') || '').toLowerCase()\n            })")
        except Exception:
            return False

        tag = element_info.get("tag")
        if tag != "input":
            return False

        el_type = element_info.get("type", "")
        if el_type == "password":
            return True

        ac = element_info.get("autocomplete", "")
        if any(k in ac for k in ["username", "email", "current-password", "new-password", "one-time-code"]):
            return True

        name_id = (element_info.get("name", "") + " " + element_info.get("id", "")).strip()
        if any(hint in name_id for hint in ["user", "email", "login", "identifier"]):
            return True

        return False

    async def _step_fill(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Fill input field (with optional escalation or smart form_field strategy)"""
        value = self._substitute_variables(step.get("value", ""))

        # Check if escalation chain is provided
        if "escalation_chain" in step:
            # Use progressive escalation to find element
            try:
                engine = self._ensure_escalation_engine()
                result = await engine.execute_with_escalation(
                    escalation_chain=step["escalation_chain"],
                    context=self.variables
                )

                # Get the locator found by escalation and fill it
                if result.get("locator"):
                    # Playwright locator object
                    await result["locator"].fill(value, timeout=10000)
                elif result.get("method") in ["selector", "text"]:
                    # Vision result - convert to Playwright locator
                    result_value = result.get("value")
                    if result.get("method") == "selector":
                        locator = self.page.locator(result_value)
                    else:  # text
                        locator = self.page.get_by_text(result_value, exact=False)
                    await locator.fill(value, timeout=10000)
                else:
                    raise ValueError("Escalation did not return valid locator for fill")

                return {
                    "success": True,
                    "action": "fill",
                    "value": value,
                    "escalation_metadata": result.get("escalation_metadata", {}),
                }

            except EscalationExhaustedError as e:
                return {
                    "success": False,
                    "action": "fill",
                    "error": str(e),
                }
        else:
            locator_config = step.get("locator", {})
            strategy = locator_config.get("strategy", "selector")

            # Smart form_field strategy - tries multiple patterns for modern CSS frameworks
            if strategy == "form_field":
                label = locator_config.get("label", "")
                field_type = locator_config.get("field_type", "input")

                try:
                    locator = await self._find_form_field(label, field_type)
                    await locator.fill(value, timeout=10000)

                    return {
                        "success": True,
                        "action": "fill",
                        "locator": locator_config,
                        "value": value,
                        "method": "form_field",
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "action": "fill",
                        "error": f"form_field strategy failed for '{label}': {e}",
                    }
            else:
                # Traditional direct locator approach
                locator = self._get_locator(locator_config)
                await locator.fill(value, timeout=10000)

                return {
                    "success": True,
                    "action": "fill",
                    "locator": locator_config,
                    "value": value,
                }

    async def _step_wait(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Wait for element or timeout"""
        if "locator" in step:
            locator_config = step["locator"]
            timeout = step.get("timeout", 5000)

            locator = self._get_locator(locator_config)
            await locator.wait_for(state="visible", timeout=timeout)

            return {
                "success": True,
                "action": "wait",
                "locator": locator_config,
            }
        else:
            # Simple timeout
            duration = step.get("duration", 1000)
            await asyncio.sleep(duration / 1000)

            return {
                "success": True,
                "action": "wait",
                "duration": duration,
            }

    async def _step_wait_for_load_state(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """
        Wait for page load state using Playwright's built-in mechanisms

        Supported states:
        - "load": Page has fired the load event (default)
        - "domcontentloaded": Page has fired DOMContentLoaded event
        - "networkidle": No network activity for at least 500ms (recommended for SPAs)

        Usage in script:
        {
          "type": "wait_for_load_state",
          "description": "Wait for page to fully load",
          "state": "networkidle",  // optional, defaults to "load"
          "timeout": 30000  // optional, defaults to navigation_timeout
        }
        """
        state = step.get("state", "load")
        timeout = step.get("timeout", self.navigation_timeout)

        valid_states = ["load", "domcontentloaded", "networkidle"]
        if state not in valid_states:
            return {
                "success": False,
                "error": f"Invalid load state '{state}'. Must be one of: {valid_states}"
            }

        print(f"⏳ Waiting for load state: {state} (timeout: {timeout}ms)", file=sys.stderr)

        try:
            await self.page.wait_for_load_state(state, timeout=timeout)
            print(f"✓ Page reached load state: {state}", file=sys.stderr)

            return {
                "success": True,
                "action": "wait_for_load_state",
                "state": state,
                "timeout": timeout,
            }
        except Exception as e:
            print(f"✗ Timeout waiting for load state '{state}': {e}", file=sys.stderr)
            return {
                "success": False,
                "error": f"Timeout waiting for load state '{state}': {str(e)}"
            }

    async def _step_screenshot(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """
        Take screenshot with optional S3 upload.

        Supports:
        - save_to: Filename for the screenshot (default: step_{num}.png)
        - upload_to_s3: Immediately upload to S3 (default: False)
        - include_in_result: Include S3 URI in final result for verification (default: False)
        - s3_prefix: Custom S3 prefix (default: uses self.s3_prefix)
        - full_page: Take full page screenshot (default: True)
        """
        full_page = step.get("full_page", True)
        screenshot_bytes = await self.page.screenshot(full_page=full_page)

        filename = step.get("save_to", f"step_{step_num}.png")
        upload_to_s3 = step.get("upload_to_s3", False)
        include_in_result = step.get("include_in_result", False)

        # Store screenshot data in memory
        screenshot_data = {
            "filename": filename,
            "data": screenshot_bytes,
            "step": step_num,
            "upload_to_s3": upload_to_s3,
            "include_in_result": include_in_result,
        }
        self.screenshots.append(screenshot_data)

        result = {
            "success": True,
            "action": "screenshot",
            "filename": filename,
        }

        # Immediate upload if requested
        if upload_to_s3:
            if self.s3_bucket:
                try:
                    s3_uri = await self._upload_single_screenshot(filename, screenshot_bytes, step)
                    result["screenshot_s3_uri"] = s3_uri

                    # Track for inclusion in final result
                    if include_in_result:
                        self.verification_screenshots.append({
                            "filename": filename,
                            "s3_uri": s3_uri,
                            "step": step_num,
                            "step_name": step.get("description", f"Step {step_num}"),
                        })
                except Exception as e:
                    print(f"  ⚠ Failed to upload screenshot: {e}", file=sys.stderr)
                    result["upload_error"] = str(e)
            else:
                # Local fallback when S3 not configured
                try:
                    local_path = await self._save_screenshot_locally(filename, screenshot_bytes)
                    result["local_path"] = local_path

                    if include_in_result:
                        self.verification_screenshots.append({
                            "filename": filename,
                            "local_path": local_path,
                            "step": step_num,
                            "step_name": step.get("description", f"Step {step_num}"),
                        })
                except Exception as e:
                    print(f"  ⚠ Failed to save screenshot locally: {e}", file=sys.stderr)
                    result["save_error"] = str(e)

        return result

    async def _step_extract(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Extract data using LLM vision and optionally execute action"""
        method = step.get("method", "vision")
        prompt = step.get("prompt", "")
        schema = step.get("schema", {})
        execute_action = step.get("execute_action", False)

        print(f"[EXTRACT] Starting extraction with method: {method}", file=sys.stderr)
        print(f"[EXTRACT] Prompt: {prompt[:100]}...", file=sys.stderr)

        if method == "vision":
            # Take screenshot for vision analysis
            print(f"[EXTRACT] Taking screenshot for vision analysis...", file=sys.stderr)
            screenshot_bytes = await self.page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            print(f"[EXTRACT] Screenshot captured ({len(screenshot_bytes)} bytes)", file=sys.stderr)

            # Call LLM with vision
            print(f"[EXTRACT] Calling LLM vision API...", file=sys.stderr)
            extracted_data = await self._call_llm_vision(prompt, screenshot_b64, schema)
            print(f"[EXTRACT] Vision API response: {json.dumps(extracted_data, indent=2)}", file=sys.stderr)

            # Execute action if requested and data indicates we should
            if execute_action and extracted_data.get("match_found"):
                print(f"[EXTRACT] Executing action based on extracted data...", file=sys.stderr)
                action_result = await self._execute_extracted_action(extracted_data)
                return {
                    "success": True,
                    "action": "extract_and_execute",
                    "method": "vision",
                    "data": extracted_data,
                    "action_result": action_result,
                }

            return {
                "success": True,
                "action": "extract",
                "method": "vision",
                "data": extracted_data,
            }
        elif method == "dom":
            # Extract from DOM using JavaScript
            # TODO: Implement DOM-based extraction
            return {
                "success": False,
                "error": "DOM extraction not yet implemented"
            }
        else:
            return {
                "success": False,
                "error": f"Unknown extraction method: {method}"
            }

    async def _execute_extracted_action(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute action based on extracted data

        Supports:
        - Click based on match_method (selector, text, index, coordinates)
        - Scroll based on should_scroll
        """
        match_method = extracted_data.get("match_method", "none")
        match_value = extracted_data.get("match_value", "")
        match_coordinates = extracted_data.get("match_coordinates", {})
        should_scroll = extracted_data.get("should_scroll", False)

        print(f"[EXTRACT_ACTION] Method: {match_method}, Value: {match_value}", file=sys.stderr)

        # Handle scrolling first if needed
        if should_scroll:
            scroll_direction = extracted_data.get("scroll_direction", "down")
            print(f"[EXTRACT_ACTION] Scrolling {scroll_direction}...", file=sys.stderr)

            if scroll_direction == "down":
                await self.page.evaluate("window.scrollBy(0, 500)")
            elif scroll_direction == "up":
                await self.page.evaluate("window.scrollBy(0, -500)")

            await self.page.wait_for_load_state("networkidle", timeout=5000)

            return {
                "success": True,
                "action": "scroll",
                "direction": scroll_direction
            }

        # Execute click based on match method
        if match_method == "selector":
            print(f"[EXTRACT_ACTION] Clicking element with selector: {match_value}", file=sys.stderr)
            locator = self.page.locator(match_value)
            await locator.click(timeout=10000)
            return {"success": True, "action": "click", "method": "selector", "value": match_value}

        elif match_method == "text":
            print(f"[EXTRACT_ACTION] Clicking element with text: {match_value}", file=sys.stderr)
            locator = self.page.get_by_text(match_value, exact=False)
            await locator.click(timeout=10000)
            return {"success": True, "action": "click", "method": "text", "value": match_value}

        elif match_method == "index":
            # Assume list items with a common selector
            index = int(match_value)
            print(f"[EXTRACT_ACTION] Clicking list item at index: {index}", file=sys.stderr)
            # Try common list item selectors
            for selector in ["li", "div.list-item", "tr", "div[role='listitem']"]:
                locator = self.page.locator(selector).nth(index)
                count = await locator.count()
                if count > 0:
                    await locator.click(timeout=10000)
                    return {"success": True, "action": "click", "method": "index", "value": index}

            raise Exception(f"Could not find list item at index {index}")

        elif match_method == "coordinates":
            x = match_coordinates.get("x", 0)
            y = match_coordinates.get("y", 0)
            print(f"[EXTRACT_ACTION] Clicking at coordinates: ({x}, {y})", file=sys.stderr)
            await self.page.mouse.click(x, y)
            return {"success": True, "action": "click", "method": "coordinates", "x": x, "y": y}

        else:
            return {
                "success": False,
                "error": f"Unknown or unsupported match_method: {match_method}"
            }

    async def _step_execute_js(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Execute JavaScript"""
        script = step.get("script", "")
        result = await self.page.evaluate(script)

        return {
            "success": True,
            "action": "execute_js",
            "result": result,
        }

    async def _step_press(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Press keyboard key(s) with configurable delay"""
        # Support either single key or array of keys
        key = step.get("key")
        keys = step.get("keys", [])
        # Configurable delay in milliseconds (default 100ms)
        delay_ms = step.get("delay", 100)

        # Convert single key to array
        if key and not keys:
            keys = [key]

        if not keys:
            return {
                "success": False,
                "error": "No key(s) specified for press action"
            }

        # Press each key in sequence with configurable delay
        for i, k in enumerate(keys):
            await self.page.keyboard.press(k)
            # Apply delay after each key (including the last one)
            # This gives UI time to respond to the key press
            await asyncio.sleep(delay_ms / 1000.0)

        return {
            "success": True,
            "action": "press",
            "keys": keys,
            "delay_ms": delay_ms,
        }

    def _get_locator(self, locator_config: Dict[str, Any]):
        """Get Playwright locator from config"""
        strategy = locator_config.get("strategy", "selector")
        value = locator_config.get("value", "")
        nth = locator_config.get("nth")

        if strategy == "role":
            # Parse role locator: "button[name='Submit']"
            # TODO: Implement proper role parsing
            locator = self.page.locator(value)
        elif strategy == "selector":
            locator = self.page.locator(value)
        elif strategy == "text":
            locator = self.page.get_by_text(value)
        elif strategy == "xpath":
            locator = self.page.locator(f"xpath={value}")
        elif strategy == "coordinates":
            # Coordinate-based clicking
            x = locator_config.get("x", 0)
            y = locator_config.get("y", 0)
            # TODO: Implement coordinate clicking
            locator = self.page.locator("body")  # Placeholder
        else:
            locator = self.page.locator(value)

        # Disambiguate if nth specified
        if nth is not None:
            locator = locator.nth(nth)

        return locator

    def _substitute_variables(self, text: str) -> str:
        """Substitute template variables like {{variable_name}}"""
        import re

        def replacer(match):
            var_name = match.group(1)
            return str(self.variables.get(var_name, match.group(0)))

        return re.sub(r'\{\{(\w+)\}\}', replacer, text)

    async def _call_llm_vision(
        self,
        prompt: str,
        screenshot_b64: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call LLM with vision capabilities"""
        # Ensure LLM client is initialized
        self._ensure_llm_client()

        if self.llm_provider == "openai":
            return await self._call_openai_vision(prompt, screenshot_b64, schema)
        elif self.llm_provider == "claude":
            return await self._call_claude_vision(prompt, screenshot_b64, schema)
        elif self.llm_provider == "gemini":
            return await self._call_gemini_vision(prompt, screenshot_b64, schema)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    async def _call_openai_vision(
        self,
        prompt: str,
        screenshot_b64: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call OpenAI vision API with JSON mode"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt + "\n\nRespond with valid JSON matching the provided schema."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{screenshot_b64}"
                        }
                    }
                ]
            }
        ]

        # Use JSON mode if schema provided
        call_params = {
            "model": self.llm_model,
            "messages": messages,
            "max_tokens": 1000,
        }

        if schema:
            call_params["response_format"] = {"type": "json_object"}

        response = self.llm_client.chat.completions.create(**call_params)

        content = response.choices[0].message.content

        # Parse JSON if schema provided
        if schema:
            return json.loads(content)
        else:
            return content

    async def _call_claude_vision(
        self,
        prompt: str,
        screenshot_b64: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call Claude (Anthropic) vision API"""
        # TODO: Implement Claude vision
        raise NotImplementedError("Claude vision support coming soon")

    async def _call_gemini_vision(
        self,
        prompt: str,
        screenshot_b64: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call Google Gemini vision API"""
        # TODO: Implement Gemini vision
        raise NotImplementedError("Gemini vision support coming soon")

    async def _upload_screenshots(self, script_name: str) -> List[str]:
        """Upload screenshots to S3"""
        s3_uris = []

        try:
            s3_client = self.boto_session.client('s3')
            session_id = f"script_{script_name.replace(' ', '_').lower()}"

            for screenshot in self.screenshots:
                s3_key = f"browser-scripts/{session_id}/{screenshot['filename']}"

                s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=screenshot['data'],
                    ContentType='image/png',
                )

                s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
                s3_uris.append(s3_uri)

        except Exception as e:
            print(f"Warning: Failed to upload screenshots: {e}", file=sys.stderr)

        return s3_uris


async def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="OpenAI Playwright Executor")
    parser.add_argument("--script", required=True, help="Path to script JSON file")
    parser.add_argument("--llm-provider", default="openai", help="LLM provider (openai, claude, gemini)")
    parser.add_argument("--llm-model", default="gpt-4o-mini", help="LLM model name")
    parser.add_argument("--aws-profile", default="browser-agent", help="AWS profile")
    parser.add_argument("--s3-bucket", help="S3 bucket for screenshots")
    parser.add_argument("--local-screenshots", help="Local directory for screenshots (for testing without S3)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--browser-channel", help="Browser channel (chrome, msedge, firefox)")
    parser.add_argument("--user-data-dir", help="User data directory for profile")

    args = parser.parse_args()

    # Load script
    with open(args.script, 'r') as f:
        script = json.load(f)

    # Create executor
    executor = OpenAIPlaywrightExecutor(
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        s3_bucket=args.s3_bucket,
        aws_profile=args.aws_profile,
        headless=args.headless,
        browser_channel=args.browser_channel,
        user_data_dir=Path(args.user_data_dir) if args.user_data_dir else None,
    )

    # Set local screenshot directory for testing
    if args.local_screenshots:
        executor.local_screenshot_dir = args.local_screenshots

    # Execute script
    result = await executor.execute_script(script)

    # Print result
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
