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
        self.s3_bucket = s3_bucket
        self.aws_profile = aws_profile
        self.headless = headless
        self.browser_channel = browser_channel
        self.user_data_dir = user_data_dir
        self.navigation_timeout = navigation_timeout

        # Initialize LLM client
        self.llm_client = self._init_llm_client(llm_api_key)

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

    def _init_llm_client(self, api_key: Optional[str]):
        """Initialize LLM client based on provider"""
        if self.llm_provider == "openai":
            return OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        elif self.llm_provider == "claude":
            try:
                from anthropic import Anthropic
                return Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
            except ImportError:
                raise ValueError("Anthropic library not installed. Install with: pip install anthropic")
        elif self.llm_provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
                return genai
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

                    # Store extracted data as variables
                    if step_result.get("data"):
                        self.variables[f"step_{step_num}_data"] = step_result["data"]

                    if not step_result["success"] and abort_on_error:
                        result["success"] = False
                        result["error"] = f"Step {step_num} failed: {step_result.get('error')}"
                        break

                except Exception as e:
                    error_msg = f"Step {step_num} exception: {str(e)}"
                    print(f"✗ {error_msg}", file=sys.stderr)

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

        launch_options = {
            "headless": self.headless,
            "channel": self.browser_channel if self.browser_channel != "chromium" else None,
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
            "screenshot": self._step_screenshot,
            "extract": self._step_extract,
            "execute_js": self._step_execute_js,
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
        """Click element"""
        locator_config = step.get("locator", {})
        locator = self._get_locator(locator_config)

        await locator.click(timeout=10000)

        return {
            "success": True,
            "action": "click",
            "locator": locator_config,
        }

    async def _step_fill(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Fill input field"""
        locator_config = step.get("locator", {})
        value = self._substitute_variables(step.get("value", ""))

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
        """Extract data using LLM vision"""
        method = step.get("method", "vision")
        prompt = step.get("prompt", "")
        schema = step.get("schema", {})

        if method == "vision":
            # Take screenshot for vision analysis
            screenshot_bytes = await self.page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            # Call LLM with vision
            extracted_data = await self._call_llm_vision(prompt, screenshot_b64, schema)

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

    async def _step_execute_js(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Execute JavaScript"""
        script = step.get("script", "")
        result = await self.page.evaluate(script)

        return {
            "success": True,
            "action": "execute_js",
            "result": result,
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
