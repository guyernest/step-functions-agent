#!/usr/bin/env python3
"""
Progressive Escalation Engine

Intelligently escalates from fast/cheap methods to slower/expensive methods
only when needed. Maximizes performance and minimizes cost.

Escalation Chain:
  Playwright DOM (free, ~10ms)
  → Playwright Locators (free, ~100ms)
  → LLM Vision (~$0.01, ~1-2s)
  → Server Agent (~$0.05, ~3-5s)
"""

import sys
import json
import base64
from typing import Dict, Any, Optional, List
from playwright.async_api import Page


class EscalationExhaustedError(Exception):
    """Raised when all escalation methods fail"""
    pass


class ProgressiveEscalationEngine:
    """
    Engine for progressive escalation through multiple methods

    Features:
    - Try cheap methods first (DOM checks, locators)
    - Only escalate to expensive methods (vision, server) when needed
    - Track costs and execution times
    - Provide detailed execution traces
    """

    def __init__(self, page: Page, llm_client, llm_model: str):
        self.page = page
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.execution_stats = {
            "total_escalations": 0,
            "level_0_successes": 0,  # DOM
            "level_1_successes": 0,  # Playwright locators
            "level_2_successes": 0,  # Vision
            "level_3_successes": 0,  # Server
            "total_cost": 0.0,
            "total_vision_calls": 0
        }

    async def execute_with_escalation(
        self,
        escalation_chain: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute action with progressive escalation

        Args:
            escalation_chain: List of methods from cheapest to most expensive
            context: Additional context for execution

        Returns:
            Result from first successful method with metadata

        Raises:
            EscalationExhaustedError: If all methods fail
        """
        self.execution_stats["total_escalations"] += 1
        context = context or {}

        for idx, method_config in enumerate(escalation_chain):
            method_name = method_config.get("method")

            print(f"[Escalation {idx+1}/{len(escalation_chain)}] Trying: {method_name}",
                  file=sys.stderr)

            try:
                result = await self._execute_method(method_config, context)

                # Check if result meets success criteria
                if self._is_successful(result, method_config):
                    print(f"✓ Success with: {method_name} (confidence: {result.get('confidence', 'N/A')})",
                          file=sys.stderr)

                    # Track stats
                    self._track_success(idx, method_config)

                    # Add metadata to result
                    result["escalation_metadata"] = {
                        "level": idx,
                        "method_used": method_name,
                        "total_attempts": idx + 1,
                        "cost_estimate": self._estimate_cost(method_name)
                    }

                    return result
                else:
                    print(f"⚠ {method_name} returned low confidence or failed validation",
                          file=sys.stderr)

            except Exception as e:
                print(f"✗ {method_name} failed: {str(e)}", file=sys.stderr)
                # Continue to next method
                continue

        # All methods failed
        raise EscalationExhaustedError(
            f"All {len(escalation_chain)} escalation methods failed"
        )

    async def _execute_method(
        self,
        method_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single escalation method"""
        method = method_config.get("method")

        if method == "playwright_dom":
            return await self._playwright_dom_check(method_config, context)
        elif method == "playwright_locator":
            return await self._playwright_locator(method_config, context)
        elif method == "vision_llm":
            return await self._vision_llm_call(method_config, context)
        elif method == "vision_find_element":
            return await self._vision_find_element(method_config, context)
        else:
            raise ValueError(f"Unknown escalation method: {method}")

    def _is_successful(
        self,
        result: Dict[str, Any],
        method_config: Dict[str, Any]
    ) -> bool:
        """Check if result meets success criteria"""
        if not result.get("success", False):
            return False

        # Check confidence threshold if specified
        min_confidence = method_config.get("confidence_threshold", 0.7)
        confidence = result.get("confidence", 1.0)

        return confidence >= min_confidence

    async def _playwright_dom_check(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fast DOM-based checks using JavaScript execution

        Strategies:
        - Check page title/URL
        - Check for element existence
        - Execute custom JS
        """
        strategy = config.get("strategy")

        if strategy == "check_page_title":
            title = await self.page.title()
            title_lower = title.lower()

            matchers = config.get("matchers", {})
            for key, patterns in matchers.items():
                if any(pattern in title_lower for pattern in patterns):
                    return {
                        "success": True,
                        "matched_key": key,
                        "matched_value": title,
                        "confidence": 0.9,
                        "method": "playwright_dom_title"
                    }

        elif strategy == "check_url_path":
            url = self.page.url
            url_lower = url.lower()

            matchers = config.get("matchers", {})
            for key, patterns in matchers.items():
                if any(pattern in url_lower for pattern in patterns):
                    return {
                        "success": True,
                        "matched_key": key,
                        "matched_value": url,
                        "confidence": 0.85,
                        "method": "playwright_dom_url"
                    }

        elif strategy == "check_key_elements":
            checks = config.get("checks", [])
            for check in checks:
                selector = check.get("selector")
                indicates = check.get("indicates")

                element = await self.page.query_selector(selector)
                if element:
                    return {
                        "success": True,
                        "matched_key": indicates,
                        "selector": selector,
                        "confidence": 0.8,
                        "method": "playwright_dom_element"
                    }

        elif strategy == "execute_script":
            script = config.get("script")
            result = await self.page.evaluate(script)

            return {
                "success": True,
                "result": result,
                "confidence": 1.0,
                "method": "playwright_dom_script"
            }

        return {"success": False}

    async def _playwright_locator(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Try to find element using Playwright locators

        Returns:
        - success: bool
        - locator: Playwright locator object (if found)
        - confidence: 0.0-1.0
        """
        locator_config = config.get("locator", {})
        strategy = locator_config.get("strategy", "selector")
        value = locator_config.get("value", "")
        nth = locator_config.get("nth")

        print(f"[DEBUG] Trying playwright_{strategy} locator: '{value}'", file=sys.stderr)

        try:
            # Get locator based on strategy
            if strategy == "selector":
                locator = self.page.locator(value)
            elif strategy == "text":
                # Use exact=False to allow partial matching, which is more forgiving
                locator = self.page.get_by_text(value, exact=False)
            elif strategy == "role":
                # Parse role locator format
                locator = self.page.locator(value)
            else:
                locator = self.page.locator(value)

            # Apply nth if specified
            if nth is not None:
                locator = locator.nth(nth)

            # Check if element exists
            count = await locator.count()

            print(f"[DEBUG] Found {count} element(s) matching '{value}'", file=sys.stderr)

            if count > 0:
                return {
                    "success": True,
                    "locator": locator,
                    "count": count,
                    "confidence": 0.95,
                    "method": f"playwright_{strategy}"
                }
            else:
                return {
                    "success": False,
                    "error": "Element not found",
                    "locator_tried": value
                }

        except Exception as e:
            print(f"[DEBUG] Exception during locator attempt: {str(e)}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e),
                "locator_tried": value
            }

    async def _vision_llm_call(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make LLM vision call for analysis/decision

        Cost: ~$0.01 per call
        Time: ~1-2s
        """
        self.execution_stats["total_vision_calls"] += 1
        self.execution_stats["total_cost"] += 0.01

        prompt = config.get("prompt", "")
        schema = config.get("schema")

        # Substitute context variables in prompt
        prompt = self._substitute_context(prompt, context)

        # Take screenshot
        screenshot = await self.page.screenshot()
        screenshot_b64 = base64.b64encode(screenshot).decode()

        # Prepare messages
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                }
            ]
        }]

        # Call LLM with JSON mode if schema provided
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
            parsed = json.loads(content)
            return {
                "success": True,
                "data": parsed,
                "confidence": parsed.get("confidence", 0.8),
                "method": "vision_llm",
                "raw_response": content
            }
        else:
            return {
                "success": True,
                "data": content,
                "confidence": 0.8,
                "method": "vision_llm"
            }

    async def _vision_find_element(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use vision to find element and return best locator

        Preference order: selector > text > coordinates

        Returns:
        {
          "method": "selector" | "text" | "coordinates",
          "value": "..." | {"x": 123, "y": 456},
          "confidence": 0.0-1.0,
          "reasoning": "..."
        }
        """
        print(f"[DEBUG] vision_find_element starting...", file=sys.stderr)

        # Check if LLM client is available
        if self.llm_client is None:
            print(f"[DEBUG] ERROR: LLM client is None! Cannot call vision API.", file=sys.stderr)
            return {
                "success": False,
                "error": "LLM client not initialized",
                "confidence": 0.0
            }

        print(f"[DEBUG] LLM client available: {type(self.llm_client).__name__}", file=sys.stderr)

        self.execution_stats["total_vision_calls"] += 1
        self.execution_stats["total_cost"] += 0.01

        prompt_base = config.get("prompt", "")
        prefer = config.get("prefer", "selector")
        fallback = config.get("fallback", "coordinates")

        # Enhance prompt with instructions
        prompt = f"""{prompt_base}

IMPORTANT: Return your response in this exact JSON format:
{{
  "method": "selector" | "text" | "coordinates",
  "value": "CSS selector" | "button text" | {{"x": 123, "y": 456}},
  "confidence": 0.0-1.0,
  "reasoning": "explain your choice"
}}

Preference: Try to return a '{prefer}' if possible. Only use '{fallback}' as last resort.
"""

        print(f"[DEBUG] Taking screenshot for vision analysis...", file=sys.stderr)
        # Take screenshot
        screenshot = await self.page.screenshot()
        screenshot_b64 = base64.b64encode(screenshot).decode()
        print(f"[DEBUG] Screenshot captured ({len(screenshot)} bytes)", file=sys.stderr)

        # Call LLM
        print(f"[DEBUG] Calling OpenAI Vision API (model: {self.llm_model})...", file=sys.stderr)
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                        }
                    ]
                }],
                response_format={"type": "json_object"},
                max_tokens=500
            )
            print(f"[DEBUG] OpenAI API call successful!", file=sys.stderr)
        except Exception as e:
            print(f"[DEBUG] OpenAI API call FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            raise

        result = json.loads(response.choices[0].message.content)
        print(f"[DEBUG] Vision result: method={result.get('method')}, confidence={result.get('confidence')}, value={result.get('value')[:50] if isinstance(result.get('value'), str) else result.get('value')}", file=sys.stderr)

        result["success"] = result.get("confidence", 0) > 0.7
        result["method_type"] = "vision_find_element"

        return result

    def _substitute_context(self, text: str, context: Dict[str, Any]) -> str:
        """Substitute {{variable}} patterns with context values"""
        import re

        def replacer(match):
            var_name = match.group(1)
            return str(context.get(var_name, match.group(0)))

        return re.sub(r'\{\{(\w+)\}\}', replacer, text)

    def _estimate_cost(self, method: str) -> float:
        """Estimate cost for method"""
        cost_map = {
            "playwright_dom": 0.0,
            "playwright_locator": 0.0,
            "vision_llm": 0.01,
            "vision_find_element": 0.01,
            "server_agent": 0.05
        }

        for key in cost_map:
            if key in method:
                return cost_map[key]

        return 0.0

    def _track_success(self, level: int, method_config: Dict[str, Any]):
        """Track success statistics"""
        if level == 0:
            self.execution_stats["level_0_successes"] += 1
        elif level == 1:
            self.execution_stats["level_1_successes"] += 1
        elif level == 2:
            self.execution_stats["level_2_successes"] += 1
        elif level >= 3:
            self.execution_stats["level_3_successes"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        total = self.execution_stats["total_escalations"]

        if total == 0:
            return self.execution_stats

        return {
            **self.execution_stats,
            "avg_escalation_level": (
                (0 * self.execution_stats["level_0_successes"] +
                 1 * self.execution_stats["level_1_successes"] +
                 2 * self.execution_stats["level_2_successes"] +
                 3 * self.execution_stats["level_3_successes"]) / total
            ),
            "level_0_percentage": self.execution_stats["level_0_successes"] / total * 100,
            "level_1_percentage": self.execution_stats["level_1_successes"] / total * 100,
            "level_2_percentage": self.execution_stats["level_2_successes"] / total * 100,
            "avg_cost_per_escalation": self.execution_stats["total_cost"] / total
        }

    def print_stats(self):
        """Print execution statistics"""
        stats = self.get_stats()

        print("\n" + "="*60, file=sys.stderr)
        print("Progressive Escalation Statistics", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"Total escalations: {stats['total_escalations']}", file=sys.stderr)
        print(f"Level 0 (DOM): {stats['level_0_successes']} ({stats.get('level_0_percentage', 0):.1f}%)",
              file=sys.stderr)
        print(f"Level 1 (Playwright): {stats['level_1_successes']} ({stats.get('level_1_percentage', 0):.1f}%)",
              file=sys.stderr)
        print(f"Level 2 (Vision): {stats['level_2_successes']} ({stats.get('level_2_percentage', 0):.1f}%)",
              file=sys.stderr)
        print(f"Total vision calls: {stats['total_vision_calls']}", file=sys.stderr)
        print(f"Total cost: ${stats['total_cost']:.3f}", file=sys.stderr)
        print(f"Avg cost per escalation: ${stats.get('avg_cost_per_escalation', 0):.3f}",
              file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
