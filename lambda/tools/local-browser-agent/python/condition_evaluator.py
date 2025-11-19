"""
Condition Evaluator for Workflow Engine

Evaluates conditions on browser state to enable conditional logic in workflows.
Supports element existence, visibility, text matching, URL patterns, JavaScript evaluation,
and logical operators (AND, OR, NOT).
"""

import re
import sys
from typing import Dict, Any, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


class ConditionEvaluator:
    """Evaluates workflow conditions against page state."""

    def __init__(self, page: Page):
        self.page = page

    async def evaluate(self, condition: Dict[str, Any]) -> bool:
        """
        Evaluate a condition and return True/False.

        Args:
            condition: Condition specification dict with 'type' and parameters

        Returns:
            Boolean result of condition evaluation
        """
        cond_type = condition.get("type")

        if not cond_type:
            raise ValueError("Condition missing 'type' field")

        # Route to appropriate handler
        if cond_type == "element_exists":
            return await self._evaluate_element_exists(condition)
        elif cond_type == "element_visible":
            return await self._evaluate_element_visible(condition)
        elif cond_type == "element_text":
            return await self._evaluate_element_text(condition)
        elif cond_type == "element_count":
            return await self._evaluate_element_count(condition)
        elif cond_type == "url_contains":
            return await self._evaluate_url_contains(condition)
        elif cond_type == "url_matches":
            return await self._evaluate_url_matches(condition)
        elif cond_type == "url_equals":
            return await self._evaluate_url_equals(condition)
        elif cond_type == "js_eval":
            return await self._evaluate_js_eval(condition)
        elif cond_type == "and":
            return await self._evaluate_and(condition)
        elif cond_type == "or":
            return await self._evaluate_or(condition)
        elif cond_type == "not":
            return await self._evaluate_not(condition)
        else:
            raise ValueError(f"Unknown condition type: {cond_type}")

    # Element-based conditions

    async def _evaluate_element_exists(self, condition: Dict[str, Any]) -> bool:
        """Check if element exists in DOM (may not be visible)."""
        selector = condition.get("selector")
        if not selector:
            raise ValueError("element_exists condition missing 'selector'")

        timeout = condition.get("timeout", 5000)

        try:
            await self.page.wait_for_selector(
                selector,
                timeout=timeout,
                state="attached"
            )
            return True
        except PlaywrightTimeoutError:
            return False
        except Exception as e:
            print(f"Warning: element_exists check failed: {e}", file=sys.stderr)
            return False

    async def _evaluate_element_visible(self, condition: Dict[str, Any]) -> bool:
        """Check if element exists AND is visible."""
        selector = condition.get("selector")
        if not selector:
            raise ValueError("element_visible condition missing 'selector'")

        timeout = condition.get("timeout", 5000)

        try:
            await self.page.wait_for_selector(
                selector,
                timeout=timeout,
                state="visible"
            )
            return True
        except PlaywrightTimeoutError:
            return False
        except Exception as e:
            print(f"Warning: element_visible check failed: {e}", file=sys.stderr)
            return False

    async def _evaluate_element_text(self, condition: Dict[str, Any]) -> bool:
        """Check element text content."""
        selector = condition.get("selector")
        if not selector:
            raise ValueError("element_text condition missing 'selector'")

        contains = condition.get("contains")
        equals = condition.get("equals")

        if not contains and not equals:
            raise ValueError("element_text condition must have 'contains' or 'equals'")

        timeout = condition.get("timeout", 5000)

        try:
            # Wait for element to exist
            await self.page.wait_for_selector(selector, timeout=timeout, state="attached")

            element = await self.page.query_selector(selector)
            if not element:
                return False

            text = await element.text_content()
            if text is None:
                return False

            if contains:
                return contains in text
            elif equals:
                return text.strip() == equals.strip()

            return False

        except PlaywrightTimeoutError:
            return False
        except Exception as e:
            print(f"Warning: element_text check failed: {e}", file=sys.stderr)
            return False

    async def _evaluate_element_count(self, condition: Dict[str, Any]) -> bool:
        """Check number of matching elements."""
        selector = condition.get("selector")
        if not selector:
            raise ValueError("element_count condition missing 'selector'")

        min_count = condition.get("min")
        max_count = condition.get("max")
        exact_count = condition.get("exact")

        if min_count is None and max_count is None and exact_count is None:
            raise ValueError("element_count must specify 'min', 'max', or 'exact'")

        try:
            elements = await self.page.query_selector_all(selector)
            count = len(elements)

            if exact_count is not None:
                return count == exact_count

            if min_count is not None and count < min_count:
                return False

            if max_count is not None and count > max_count:
                return False

            return True

        except Exception as e:
            print(f"Warning: element_count check failed: {e}", file=sys.stderr)
            return False

    # URL-based conditions

    async def _evaluate_url_contains(self, condition: Dict[str, Any]) -> bool:
        """Check if URL contains substring."""
        pattern = condition.get("pattern")
        if not pattern:
            raise ValueError("url_contains condition missing 'pattern'")

        current_url = self.page.url
        return pattern in current_url

    async def _evaluate_url_matches(self, condition: Dict[str, Any]) -> bool:
        """Check if URL matches regex pattern."""
        pattern = condition.get("pattern")
        if not pattern:
            raise ValueError("url_matches condition missing 'pattern'")

        current_url = self.page.url
        try:
            return bool(re.search(pattern, current_url))
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}")

    async def _evaluate_url_equals(self, condition: Dict[str, Any]) -> bool:
        """Check if URL exactly matches."""
        url = condition.get("url")
        if not url:
            raise ValueError("url_equals condition missing 'url'")

        current_url = self.page.url
        return current_url == url

    # JavaScript evaluation

    async def _evaluate_js_eval(self, condition: Dict[str, Any]) -> bool:
        """Evaluate JavaScript expression on page."""
        expression = condition.get("expression")
        if not expression:
            raise ValueError("js_eval condition missing 'expression'")

        expected = condition.get("expected", True)

        try:
            result = await self.page.evaluate(expression)
            return result == expected
        except Exception as e:
            print(f"Warning: js_eval check failed: {e}", file=sys.stderr)
            return False

    # Logical operators

    async def _evaluate_and(self, condition: Dict[str, Any]) -> bool:
        """All conditions must be true."""
        conditions = condition.get("conditions", [])
        if not conditions:
            raise ValueError("'and' condition missing 'conditions' array")

        for cond in conditions:
            result = await self.evaluate(cond)
            if not result:
                return False

        return True

    async def _evaluate_or(self, condition: Dict[str, Any]) -> bool:
        """At least one condition must be true."""
        conditions = condition.get("conditions", [])
        if not conditions:
            raise ValueError("'or' condition missing 'conditions' array")

        for cond in conditions:
            result = await self.evaluate(cond)
            if result:
                return True

        return False

    async def _evaluate_not(self, condition: Dict[str, Any]) -> bool:
        """Invert condition result."""
        inner_condition = condition.get("condition")
        if not inner_condition:
            raise ValueError("'not' condition missing 'condition' field")

        result = await self.evaluate(inner_condition)
        return not result
