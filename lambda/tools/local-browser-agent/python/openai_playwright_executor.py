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
from typing import Dict, Any, Optional, List, Literal
from pathlib import Path
import asyncio

import boto3
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from openai import OpenAI

# Import progressive escalation engine
from progressive_escalation_engine import ProgressiveEscalationEngine, EscalationExhaustedError

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
        self.escalation_engine: Optional[ProgressiveEscalationEngine] = None

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

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"OpenAI Playwright Executor", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Script: {name}", file=sys.stderr)
        print(f"Description: {description}", file=sys.stderr)
        print(f"LLM: {self.llm_provider} ({self.llm_model})", file=sys.stderr)
        print(f"Starting Page: {starting_page}", file=sys.stderr)
        print(f"Total Steps: {len(steps)}", file=sys.stderr)
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

            # Execute each step
            for idx, step in enumerate(steps):
                step_num = idx + 1
                step_type = step.get("type")
                step_desc = step.get("description", f"Step {step_num}")

                print(f"\n[Step {step_num}/{len(steps)}] {step_type}: {step_desc}", file=sys.stderr)

                try:
                    step_result = await self._execute_step(step, step_num)
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

            # Upload screenshots to S3 if configured
            if self.s3_bucket and self.screenshots:
                result["screenshots"] = await self._upload_screenshots(name)

        except Exception as e:
            result["success"] = False
            result["error"] = f"Script execution failed: {str(e)}"
            result["traceback"] = traceback.format_exc()
            print(f"\n✗ Script failed: {e}", file=sys.stderr)

        finally:
            # Clean up browser
            await self._cleanup_browser()

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

        # Configure browser arguments based on whether we're using a profile
        # When using a persistent profile, we DON'T want --disable-blink-features=AutomationControlled
        # because it ironically PREVENTS password managers from working (Edge detects automation and blocks PM)
        args = [
            '--disable-dev-shm-usage',  # Overcome limited resource problems
            '--no-sandbox',  # Disable sandbox for compatibility
        ]

        # Only add automation flag if NOT using persistent profile
        # (password managers work better without this flag when using profiles)
        if not self.user_data_dir:
            args.append('--disable-blink-features=AutomationControlled')

        launch_options = {
            "headless": self.headless,
            "channel": self.browser_channel if self.browser_channel != "chromium" else None,
            "args": args,
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

    async def _execute_step(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Execute a single step"""
        step_type = step.get("type")

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
        }

        handler = handlers.get(step_type)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown step type: {step_type}"
            }

        return await handler(step, step_num)

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

                    # If trigger_autofill, use real mouse click instead of programmatic click
                    if trigger_autofill:
                        print(f"🖱️  Using real mouse click for autofill (trigger_autofill=true)", file=sys.stderr)
                        await locator.scroll_into_view_if_needed()

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

                    # If trigger_autofill, use real mouse click
                    if trigger_autofill:
                        print(f"🖱️  Using real mouse click for autofill (trigger_autofill=true)", file=sys.stderr)
                        await locator.scroll_into_view_if_needed()

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

            await locator.click(timeout=10000)

            return {
                "success": True,
                "action": "click",
                "locator": locator_config,
            }

    async def _step_fill(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Fill input field (with optional escalation)"""
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
            # Traditional direct locator approach
            locator_config = step.get("locator", {})
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
        """Take screenshot"""
        screenshot_bytes = await self.page.screenshot(full_page=True)

        filename = step.get("save_to", f"step_{step_num}.png")
        self.screenshots.append({
            "filename": filename,
            "data": screenshot_bytes,
            "step": step_num,
        })

        return {
            "success": True,
            "action": "screenshot",
            "filename": filename,
        }

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

    # Execute script
    result = await executor.execute_script(script)

    # Print result
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
