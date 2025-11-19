"""
Workflow Executor for Browser Automation

Executes workflows with conditional logic, intelligent retry strategies, and escalation.
Supports: if/else branching, try with multiple strategies, sequences, goto jumps, and switch statements.
"""

import sys
import asyncio
from typing import Dict, Any, List, Optional
from condition_evaluator import ConditionEvaluator


class WorkflowError(Exception):
    """Raised when workflow execution fails."""
    pass


class WorkflowExecutor:
    """
    Executes workflow scripts with control flow.

    Handles:
    - Conditional branching (if/else, switch)
    - Intelligent retry with multiple strategies
    - Named sequences and goto jumps
    - Loop detection and prevention
    """

    # Configuration
    MAX_VISITS_PER_STEP = 10  # Prevent infinite loops
    MAX_TOTAL_STEPS = 1000  # Overall execution limit

    def __init__(self, script: Dict[str, Any], executor):
        """
        Initialize workflow executor.

        Args:
            script: Workflow script dict
            executor: Playwright executor instance (must have .page and .execute_step())
        """
        self.script = script
        self.executor = executor  # OpenAIPlaywrightExecutor instance
        self.steps = script.get("steps", [])
        self.current_index = 0
        self.step_map = self._build_step_map()
        self.condition_evaluator = None  # Initialized when page available

        # Execution tracking
        self.step_visits = {}  # step_index -> visit_count
        self.step_history = []  # [(index, step_name), ...]
        self.total_steps_executed = 0

    def _build_step_map(self) -> Dict[str, int]:
        """Build index of named steps for goto targets."""
        step_map = {}
        for idx, step in enumerate(self.steps):
            if "name" in step:
                step_name = step["name"]
                if step_name in step_map:
                    print(f"Warning: Duplicate step name '{step_name}' at index {idx}", file=sys.stderr)
                step_map[step_name] = idx
        return step_map

    async def run(self):
        """Execute the workflow from start to finish."""
        # Initialize condition evaluator with page
        self.condition_evaluator = ConditionEvaluator(self.executor.page)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Starting Workflow Execution: {self.script.get('name', 'Unnamed')}", file=sys.stderr)
        print(f"Total steps: {len(self.steps)}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        while self.current_index < len(self.steps):
            # Safety checks
            if self.total_steps_executed >= self.MAX_TOTAL_STEPS:
                raise WorkflowError(f"Exceeded maximum steps ({self.MAX_TOTAL_STEPS})")

            step = self.steps[self.current_index]
            step_type = step.get("type", "action")
            step_name = step.get("name", f"Step_{self.current_index + 1}")

            # Check loop detection
            visit_count = self.step_visits.get(self.current_index, 0)
            if visit_count >= self.MAX_VISITS_PER_STEP:
                raise WorkflowError(
                    f"Infinite loop detected: Step {self.current_index} ('{step_name}') "
                    f"visited {visit_count} times"
                )

            # Track visit
            self.step_visits[self.current_index] = visit_count + 1
            self.step_history.append((self.current_index, step_name))
            self.total_steps_executed += 1

            # Log step
            print(f"\n[{self.total_steps_executed}] Step {self.current_index + 1}/{len(self.steps)}: {step_name}", file=sys.stderr)
            if "description" in step:
                print(f"  Description: {step['description']}", file=sys.stderr)

            # Execute based on type
            try:
                if step_type == "if":
                    await self._execute_if(step)
                elif step_type == "try":
                    await self._execute_try(step)
                elif step_type == "sequence":
                    await self._execute_sequence(step)
                elif step_type == "goto":
                    self._execute_goto(step)
                elif step_type == "switch":
                    await self._execute_switch(step)
                else:
                    # Regular action step - delegate to executor
                    await self.executor.execute_step(step)
                    self.current_index += 1

            except Exception as e:
                print(f"\n✗ ERROR in step {self.current_index}: {e}", file=sys.stderr)
                if self.script.get("abort_on_error", True):
                    raise
                else:
                    print(f"  Continuing despite error (abort_on_error=false)", file=sys.stderr)
                    self.current_index += 1

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✓ Workflow Completed Successfully", file=sys.stderr)
        print(f"Total steps executed: {self.total_steps_executed}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

    # Control flow step handlers

    async def _execute_if(self, step: Dict[str, Any]):
        """Execute conditional branch."""
        condition = step.get("condition")
        if not condition:
            raise ValueError("'if' step missing 'condition'")

        print(f"  Evaluating condition...", file=sys.stderr)
        result = await self.condition_evaluator.evaluate(condition)
        print(f"  → Condition result: {result}", file=sys.stderr)

        if result:
            if "then" in step:
                print(f"  → Taking 'then' branch", file=sys.stderr)
                await self._handle_branch(step["then"])
            else:
                self.current_index += 1
        else:
            if "else" in step:
                print(f"  → Taking 'else' branch", file=sys.stderr)
                await self._handle_branch(step["else"])
            else:
                self.current_index += 1

    async def _execute_try(self, step: Dict[str, Any]):
        """Execute retry block with multiple strategies."""
        strategies = step.get("strategies", [])
        if not strategies:
            raise ValueError("'try' step missing 'strategies' array")

        step_name = step.get("name", "unnamed try block")
        print(f"  Trying {len(strategies)} strategies...", file=sys.stderr)

        for strategy_index, strategy in enumerate(strategies):
            strategy_name = strategy.get("name", f"Strategy_{strategy_index + 1}")

            print(f"\n  [{strategy_index + 1}/{len(strategies)}] Attempting: {strategy_name}", file=sys.stderr)
            if "description" in strategy:
                print(f"    {strategy['description']}", file=sys.stderr)

            try:
                # Execute strategy based on type
                if "steps" in strategy:
                    # Step-based strategy
                    await self._execute_strategy_steps(strategy)

                elif "escalate" in strategy:
                    # Escalation strategy
                    await self._execute_escalation(strategy["escalate"])

                elif "alternative" in strategy:
                    # Alternative approach
                    await self._execute_alternative(strategy["alternative"])

                else:
                    raise ValueError(f"Strategy '{strategy_name}' has no execution method")

                # Verify success if verification specified
                if "verify" in strategy:
                    print(f"    Verifying success...", file=sys.stderr)
                    success = await self.condition_evaluator.evaluate(strategy["verify"])

                    if not success:
                        print(f"    ✗ Verification failed for {strategy_name}", file=sys.stderr)
                        continue  # Try next strategy

                # Success!
                print(f"    ✓ {strategy_name} succeeded", file=sys.stderr)
                self.current_index += 1
                return

            except Exception as e:
                print(f"    ✗ {strategy_name} failed: {e}", file=sys.stderr)
                # Continue to next strategy

        # All strategies failed
        print(f"\n  ✗ All {len(strategies)} strategies failed for '{step_name}'", file=sys.stderr)

        if "on_all_strategies_failed" in step:
            print(f"  Executing failure handler...", file=sys.stderr)
            await self._handle_failure_action(step["on_all_strategies_failed"])
        else:
            raise WorkflowError(f"Try block '{step_name}' exhausted all strategies")

    async def _execute_strategy_steps(self, strategy: Dict[str, Any]):
        """Execute a step-based strategy."""
        steps = strategy.get("steps", [])
        for step in steps:
            await self.executor.execute_step(step)

    async def _execute_escalation(self, escalate_config: Dict[str, Any]):
        """Execute escalation strategy (vision LLM, progressive escalation, etc.)."""
        escalate_type = escalate_config.get("type")

        if escalate_type == "vision_llm":
            # Use vision LLM to solve the problem
            prompt = escalate_config.get("prompt")
            if not prompt:
                raise ValueError("vision_llm escalation missing 'prompt'")

            print(f"    Escalating to Vision LLM...", file=sys.stderr)
            print(f"    Prompt: {prompt[:100]}...", file=sys.stderr)

            # Create an 'act' step and execute it
            # The OpenAI Computer Agent will use vision to solve this
            act_step = {
                "action": "act",
                "prompt": prompt,
                "timeout": escalate_config.get("timeout", 60000),
                "max_actions": escalate_config.get("max_actions", 10)
            }
            await self.executor.execute_step(act_step)

        elif escalate_type == "progressive_escalation":
            # Use existing progressive escalation engine
            target = escalate_config.get("target")
            if not target:
                raise ValueError("progressive_escalation missing 'target'")

            print(f"    Escalating with progressive escalation: {target}", file=sys.stderr)

            # Execute as a click with progressive escalation
            click_step = {
                "action": "click",
                "target": target,
                "use_progressive_escalation": True
            }
            await self.executor.execute_step(click_step)

        elif escalate_type == "human_intervention":
            # Pause and request human help
            message = escalate_config.get("message", "Human intervention required")
            timeout = escalate_config.get("timeout", 300000)  # 5 minutes default

            print(f"    🙋 Human intervention required: {message}", file=sys.stderr)
            print(f"    Waiting up to {timeout/1000}s for human action...", file=sys.stderr)

            # Wait for resume condition if specified
            if "resume_condition" in escalate_config:
                try:
                    # Poll for condition with timeout
                    start_time = asyncio.get_event_loop().time()
                    while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
                        result = await self.condition_evaluator.evaluate(
                            escalate_config["resume_condition"]
                        )
                        if result:
                            print(f"    ✓ Resume condition met, continuing...", file=sys.stderr)
                            return
                        await asyncio.sleep(1)

                    raise TimeoutError(f"Human intervention timeout after {timeout}ms")
                except Exception as e:
                    raise WorkflowError(f"Human intervention failed: {e}")
            else:
                # Simple timed wait
                await asyncio.sleep(timeout / 1000)

        else:
            raise ValueError(f"Unknown escalation type: {escalate_type}")

    async def _execute_alternative(self, alternative_config: Dict[str, Any]):
        """Execute alternative approach (API call, etc.)."""
        alt_type = alternative_config.get("type")

        if alt_type == "api_call":
            # Make HTTP API call instead of UI automation
            print(f"    Using API fallback...", file=sys.stderr)
            # TODO: Implement HTTP client for API fallback
            raise NotImplementedError("API fallback not yet implemented")

        else:
            raise ValueError(f"Unknown alternative type: {alt_type}")

    async def _execute_sequence(self, step: Dict[str, Any]):
        """Execute named sequence of steps."""
        steps = step.get("steps", [])
        for substep in steps:
            await self.executor.execute_step(substep)
        self.current_index += 1

    def _execute_goto(self, step: Dict[str, Any]):
        """Jump to named step."""
        target = step.get("target")
        if not target:
            raise ValueError("'goto' step missing 'target'")

        if target not in self.step_map:
            raise ValueError(f"goto target '{target}' not found in step map")

        new_index = self.step_map[target]
        print(f"  → Jumping to step {new_index + 1}: {target}", file=sys.stderr)
        self.current_index = new_index

    async def _execute_switch(self, step: Dict[str, Any]):
        """Execute switch/case statement."""
        cases = step.get("cases", [])
        default = step.get("default")

        for case in cases:
            condition = case.get("condition")
            if not condition:
                continue

            result = await self.condition_evaluator.evaluate(condition)
            if result:
                print(f"  → Switch case matched", file=sys.stderr)

                # Execute case action
                if "goto" in case:
                    self._handle_goto_branch(case["goto"])
                elif "steps" in case:
                    for case_step in case["steps"]:
                        await self.executor.execute_step(case_step)

                    # Handle 'then' after steps
                    if "then" in case:
                        await self._handle_branch(case["then"])
                    else:
                        self.current_index += 1
                else:
                    self.current_index += 1

                return

        # No case matched, use default
        if default:
            print(f"  → Using default case", file=sys.stderr)
            if "goto" in default:
                self._handle_goto_branch(default["goto"])
            elif "steps" in default:
                for default_step in default["steps"]:
                    await self.executor.execute_step(default_step)

                if "then" in default:
                    await self._handle_branch(default["then"])
                else:
                    self.current_index += 1
            else:
                self.current_index += 1
        else:
            # No match and no default
            print(f"  → No case matched, no default specified", file=sys.stderr)
            self.current_index += 1

    # Helper methods

    async def _handle_branch(self, branch: Any):
        """Handle then/else branch action."""
        if isinstance(branch, dict):
            if "goto" in branch:
                self._handle_goto_branch(branch["goto"])
            elif "continue" in branch and branch["continue"]:
                self.current_index += 1
            elif "action" in branch:
                # Execute inline action
                await self.executor.execute_step(branch)

                # Check for chained 'then'
                if "then" in branch:
                    await self._handle_branch(branch["then"])
                else:
                    self.current_index += 1
            else:
                self.current_index += 1
        else:
            self.current_index += 1

    def _handle_goto_branch(self, target: str):
        """Handle goto in a branch."""
        if target not in self.step_map:
            raise ValueError(f"goto target '{target}' not found")
        self.current_index = self.step_map[target]

    async def _handle_failure_action(self, failure_config: Dict[str, Any]):
        """Handle on_all_strategies_failed action."""
        if "action" in failure_config:
            # Execute the failure action
            await self.executor.execute_step(failure_config)

        if "type" in failure_config and failure_config["type"] == "error":
            # Raise error
            message = failure_config.get("message", "Strategy exhaustion")
            raise WorkflowError(message)

        # Handle then branch if present
        if "then" in failure_config:
            await self._handle_branch(failure_config["then"])
        else:
            self.current_index += 1
