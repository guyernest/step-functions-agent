#!/usr/bin/env python3
"""
Script Executor for Navigation Studio

Executes automation scripts step-by-step with real-time feedback.
Integrates with the existing workflow_executor from local-browser-agent.
"""

import sys
import asyncio
import traceback
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path

# Add local-browser-agent to path
BROWSER_AGENT_PATH = Path(__file__).parent.parent.parent / "lambda/tools/local-browser-agent/python"
sys.path.insert(0, str(BROWSER_AGENT_PATH))

try:
    from workflow_executor import WorkflowExecutor, WorkflowError
    from openai_playwright_executor import OpenAIPlaywrightExecutor
    WORKFLOW_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Workflow modules not available: {e}")
    WORKFLOW_AVAILABLE = False


class StudioScriptExecutor:
    """
    Executes scripts with real-time progress callbacks for the studio UI.

    Wraps the existing OpenAIPlaywrightExecutor and WorkflowExecutor
    to provide step-by-step execution with callbacks.
    """

    def __init__(
        self,
        page,  # Playwright page from BrowserSession
        on_step_start: Optional[Callable] = None,
        on_step_complete: Optional[Callable] = None,
        on_screenshot: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        self.page = page
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete
        self.on_screenshot = on_screenshot
        self.on_error = on_error

        # Execution state
        self.is_running = False
        self.is_paused = False
        self.current_step_index = 0
        self.step_results = []

    async def execute_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete script.

        Args:
            script: Script definition with steps array

        Returns:
            Execution result with step results and screenshots
        """
        self.is_running = True
        self.is_paused = False
        self.current_step_index = 0
        self.step_results = []

        steps = script.get("steps", [])
        script_name = script.get("name", "Unnamed Script")

        try:
            # Navigate to starting page if specified
            starting_page = script.get("starting_page")
            if starting_page:
                await self._emit_step_start(-1, {
                    "action": "navigate",
                    "description": f"Navigate to starting page",
                    "url": starting_page
                })
                await self.page.goto(starting_page, wait_until="domcontentloaded")
                await self._emit_step_complete(-1, {"status": "success", "url": starting_page})

            # Execute each step
            for idx, step in enumerate(steps):
                if not self.is_running:
                    break

                # Wait if paused
                while self.is_paused and self.is_running:
                    await asyncio.sleep(0.1)

                self.current_step_index = idx
                await self._execute_step(idx, step)

            return {
                "status": "completed",
                "script_name": script_name,
                "steps_executed": len(self.step_results),
                "results": self.step_results
            }

        except Exception as e:
            error_msg = str(e)
            traceback.print_exc()
            if self.on_error:
                await self.on_error({
                    "step_index": self.current_step_index,
                    "error": error_msg
                })
            return {
                "status": "error",
                "error": error_msg,
                "step_index": self.current_step_index,
                "results": self.step_results
            }
        finally:
            self.is_running = False

    async def _execute_step(self, index: int, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step."""
        action = step.get("action", step.get("type", "unknown"))
        description = step.get("description", f"Step {index + 1}")

        await self._emit_step_start(index, step)

        result = {"action": action, "step_index": index}

        try:
            if action == "navigate":
                url = step.get("url", "")
                await self.page.goto(url, wait_until="domcontentloaded")
                result["status"] = "success"
                result["url"] = url

            elif action == "click":
                locator = step.get("locator", {})
                selector = self._build_selector(locator)
                await self.page.click(selector)
                result["status"] = "success"
                result["selector"] = selector

            elif action == "fill":
                locator = step.get("locator", {})
                selector = self._build_selector(locator)
                value = step.get("value", "")
                await self.page.fill(selector, value)
                result["status"] = "success"
                result["selector"] = selector

            elif action == "wait":
                locator = step.get("locator", {})
                timeout = step.get("timeout", 5000)
                if locator:
                    selector = self._build_selector(locator)
                    await self.page.wait_for_selector(selector, timeout=timeout)
                    result["selector"] = selector
                else:
                    # Simple delay
                    delay = step.get("delay", 1000)
                    await asyncio.sleep(delay / 1000)
                result["status"] = "success"

            elif action == "screenshot":
                screenshot_bytes = await self.page.screenshot(type="png")
                import base64
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                result["status"] = "success"
                result["screenshot"] = screenshot_b64
                if self.on_screenshot:
                    await self.on_screenshot(screenshot_b64)

            elif action == "extract":
                # Vision-based extraction would go here
                # For now, do DOM-based extraction
                locator = step.get("locator", {})
                if locator:
                    selector = self._build_selector(locator)
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        result["data"] = {"text": text}
                result["status"] = "success"

            elif action == "execute_js":
                script_code = step.get("script", "")
                js_result = await self.page.evaluate(script_code)
                result["status"] = "success"
                result["data"] = js_result

            elif action == "select":
                locator = step.get("locator", {})
                selector = self._build_selector(locator)
                value = step.get("value", "")
                await self.page.select_option(selector, value)
                result["status"] = "success"

            elif action == "hover":
                locator = step.get("locator", {})
                selector = self._build_selector(locator)
                await self.page.hover(selector)
                result["status"] = "success"

            elif action == "press":
                key = step.get("key", "Enter")
                await self.page.keyboard.press(key)
                result["status"] = "success"

            else:
                result["status"] = "skipped"
                result["message"] = f"Unknown action: {action}"

            # Take screenshot after step if configured
            if step.get("screenshot_after", False):
                screenshot_bytes = await self.page.screenshot(type="png")
                import base64
                result["screenshot"] = base64.b64encode(screenshot_bytes).decode("utf-8")
                if self.on_screenshot:
                    await self.on_screenshot(result["screenshot"])

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        self.step_results.append(result)
        await self._emit_step_complete(index, result)

        return result

    def _build_selector(self, locator: Dict[str, Any]) -> str:
        """Build a Playwright selector from locator specification."""
        strategy = locator.get("strategy", "selector")
        value = locator.get("value", "")

        if strategy == "selector":
            return value
        elif strategy == "xpath":
            return f"xpath={value}"
        elif strategy == "text":
            return f"text={value}"
        elif strategy == "role":
            return value  # Playwright role selectors like "button[name='Submit']"
        elif strategy == "id":
            return f"#{value}"
        elif strategy == "class":
            return f".{value}"
        else:
            return value

    async def _emit_step_start(self, index: int, step: Dict[str, Any]):
        """Emit step start event."""
        if self.on_step_start:
            await self.on_step_start({
                "step_index": index,
                "action": step.get("action", step.get("type")),
                "description": step.get("description", f"Step {index + 1}"),
                "timestamp": datetime.now().isoformat()
            })

    async def _emit_step_complete(self, index: int, result: Dict[str, Any]):
        """Emit step complete event."""
        if self.on_step_complete:
            await self.on_step_complete({
                "step_index": index,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

    def pause(self):
        """Pause script execution."""
        self.is_paused = True

    def resume(self):
        """Resume script execution."""
        self.is_paused = False

    def stop(self):
        """Stop script execution."""
        self.is_running = False
        self.is_paused = False


async def execute_step_standalone(page, step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single step without full script context.
    Useful for testing individual steps.
    """
    executor = StudioScriptExecutor(page)
    return await executor._execute_step(0, step)
