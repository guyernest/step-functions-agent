"""
Workflow Executor for Browser Automation

Explicit flow control model inspired by AWS Step Functions.
Eliminates index management bugs by using named steps and explicit transitions.

Flow Control:
- goto: Jump to named step
- next: Proceed to named step
- end: Terminate workflow successfully
- succeed/fail: Explicit terminal states
- default: Sequential (next in array)
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
    Executes workflow scripts with explicit flow control.

    Flow resolution priority:
    1. goto - Always honored
    2. end: true - Terminates successfully
    3. next - Jump to named step
    4. type: succeed - Success terminal
    5. type: fail - Failure terminal
    6. default - Next in array
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
        self.step_map = self._build_step_map()
        self.condition_evaluator = None  # Initialized when page available

        # Execution tracking
        self.step_visits = {}  # step_name -> visit_count
        self.step_history = []  # [step_name, ...]
        self.total_steps_executed = 0
        self.step_results = []  # Collect results from action steps
        self.screenshots = []  # Collect screenshot URIs

        # Current execution state
        self.current_step_name = None
        self.next_step_name = None  # Set by flow control

    def _build_step_map(self) -> Dict[str, int]:
        """Build index of named steps for goto/next targets."""
        step_map = {}
        for idx, step in enumerate(self.steps):
            if "name" in step:
                step_name = step["name"]
                if step_name in step_map:
                    print(f"Warning: Duplicate step name '{step_name}' at index {idx}", file=sys.stderr)
                step_map[step_name] = idx
        return step_map

    def _get_step_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get step by name."""
        if name not in self.step_map:
            return None
        return self.steps[self.step_map[name]]

    def _get_step_name(self, step: Dict[str, Any], index: int) -> str:
        """Get step name (use explicit name or generate from index)."""
        return step.get("name", f"Step_{index}")

    def _get_next_step_in_array(self, current_index: int) -> Optional[str]:
        """Get next step name in array sequence."""
        next_index = current_index + 1
        if next_index < len(self.steps):
            return self._get_step_name(self.steps[next_index], next_index)
        return None

    def _resolve_next_step(self, step: Dict[str, Any], current_index: int) -> Optional[str]:
        """
        Resolve next step using flow control directives.

        Priority:
        1. goto - explicit jump (already handled during execution)
        2. end: true - terminates workflow
        3. next - named step
        4. type: succeed/fail - terminal states (already handled)
        5. default - next in array

        Returns:
            Next step name, or None to terminate
        """
        # Check if next was set by goto during execution
        if self.next_step_name:
            next_name = self.next_step_name
            self.next_step_name = None  # Clear for next iteration
            return next_name

        # Check end directive
        if step.get("end"):
            print(f"  → Workflow terminates (end: true)", file=sys.stderr)
            return None

        # Check explicit next
        if "next" in step:
            next_name = step["next"]
            if next_name not in self.step_map:
                raise WorkflowError(f"Step '{self.current_step_name}' references unknown next step: '{next_name}'")
            print(f"  → Explicit next: {next_name}", file=sys.stderr)
            return next_name

        # Default: sequential flow
        next_name = self._get_next_step_in_array(current_index)
        if next_name:
            print(f"  → Sequential next: {next_name}", file=sys.stderr)
        else:
            print(f"  → End of workflow (no more steps)", file=sys.stderr)
        return next_name

    async def run(self):
        """Execute the workflow from start to finish."""
        # Initialize condition evaluator with page
        self.condition_evaluator = ConditionEvaluator(self.executor.page)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Starting Workflow: {self.script.get('name', 'Unnamed')}", file=sys.stderr)
        print(f"Total steps defined: {len(self.steps)}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        # Start with first step
        if not self.steps:
            print("Warning: Workflow has no steps", file=sys.stderr)
            return

        self.current_step_name = self._get_step_name(self.steps[0], 0)

        # Main execution loop - follow flow control
        while self.current_step_name is not None:
            # Safety check
            if self.total_steps_executed >= self.MAX_TOTAL_STEPS:
                raise WorkflowError(f"Exceeded maximum steps ({self.MAX_TOTAL_STEPS})")

            # Get step
            step_index = self.step_map.get(self.current_step_name)
            if step_index is None:
                # Try to find by generated name
                for idx, s in enumerate(self.steps):
                    if self._get_step_name(s, idx) == self.current_step_name:
                        step_index = idx
                        break

            if step_index is None:
                raise WorkflowError(f"Step not found: '{self.current_step_name}'")

            step = self.steps[step_index]

            # Loop detection
            visit_count = self.step_visits.get(self.current_step_name, 0)
            if visit_count >= self.MAX_VISITS_PER_STEP:
                raise WorkflowError(
                    f"Infinite loop detected: '{self.current_step_name}' visited {visit_count} times"
                )

            # Track execution
            self.step_visits[self.current_step_name] = visit_count + 1
            self.step_history.append(self.current_step_name)
            self.total_steps_executed += 1

            # Log step
            print(f"\n[{self.total_steps_executed}] Executing: {self.current_step_name}", file=sys.stderr)
            if "description" in step:
                print(f"  Description: {step['description']}", file=sys.stderr)

            # Execute step
            try:
                abort_on_error = self.script.get("abort_on_error", True)
                await self._dispatch_step(step)

            except Exception as e:
                print(f"\n✗ ERROR in step '{self.current_step_name}': {e}", file=sys.stderr)
                if abort_on_error:
                    raise WorkflowError(f"Step '{self.current_step_name}' failed: {e}")
                else:
                    print(f"  Continuing despite error (abort_on_error=false)", file=sys.stderr)

            # Resolve next step
            self.current_step_name = self._resolve_next_step(step, step_index)

        # Workflow complete
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✓ Workflow Completed Successfully", file=sys.stderr)
        print(f"Steps executed: {self.total_steps_executed}", file=sys.stderr)
        print(f"Unique steps visited: {len(self.step_visits)}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

    async def _dispatch_step(self, step: Dict[str, Any]):
        """Route step to appropriate handler based on type."""
        step_type = step.get("type", step.get("action"))
        print(f"  [DISPATCH] step_type={step_type}, has_action={bool(step.get('action'))}", file=sys.stderr)

        # Workflow control structures
        if step_type == "if":
            await self._execute_if(step)
        elif step_type == "try":
            await self._execute_try(step)
        elif step_type == "sequence":
            await self._execute_sequence(step)
        elif step_type == "switch":
            await self._execute_switch(step)
        elif step_type == "goto":
            self._execute_goto(step)
        elif step_type == "succeed":
            self._execute_succeed(step)
        elif step_type == "fail":
            self._execute_fail(step)
        # Action steps - delegate to executor
        elif step.get("action"):
            print(f"  [DISPATCH] Calling execute_step for action: {step.get('action')}", file=sys.stderr)
            step_result = await self.executor.execute_step(step)
            print(f"  [DISPATCH] execute_step returned: type={type(step_result)}, is_none={step_result is None}", file=sys.stderr)
            # Collect results for final output
            if step_result:
                print(f"  → Collecting step result: {step_result.get('action', 'unknown')}, success={step_result.get('success')}", file=sys.stderr)
                self.step_results.append(step_result)
                # Collect screenshots if present
                if "screenshot_s3_uri" in step_result:
                    self.screenshots.append(step_result["screenshot_s3_uri"])
                # Log extracted data if present
                if "data" in step_result:
                    print(f"  → Extracted data collected: {list(step_result['data'].keys())}", file=sys.stderr)
            else:
                print(f"  [DISPATCH] WARNING: execute_step returned None or empty!", file=sys.stderr)
        else:
            raise ValueError(f"Unknown step type: {step_type}")

    async def _execute_if(self, step: Dict[str, Any]):
        """Execute conditional branch."""
        condition = step.get("condition")
        if not condition:
            raise ValueError("'if' step missing 'condition'")

        print(f"  Evaluating condition...", file=sys.stderr)
        result = await self.condition_evaluator.evaluate(condition)
        print(f"  → Result: {result}", file=sys.stderr)

        branch = step.get("then") if result else step.get("else")
        if branch:
            print(f"  → Taking {'then' if result else 'else'} branch", file=sys.stderr)
            await self._execute_branch(branch)

    async def _execute_try(self, step: Dict[str, Any]):
        """Execute retry block with multiple strategies."""
        strategies = step.get("strategies", [])
        if not strategies:
            raise ValueError("'try' step missing 'strategies' array")

        step_name = step.get("name", "unnamed try block")
        print(f"  Trying {len(strategies)} strategies...", file=sys.stderr)

        last_error = None
        for strategy_index, strategy in enumerate(strategies):
            strategy_name = strategy.get("name", f"Strategy_{strategy_index + 1}")
            print(f"\n  [{strategy_index + 1}/{len(strategies)}] Attempting: {strategy_name}", file=sys.stderr)

            try:
                # Execute strategy steps
                strategy_steps = strategy.get("steps", [])
                for substep in strategy_steps:
                    await self._dispatch_step(substep)

                # Verify if specified
                if "verify" in strategy:
                    print(f"    Verifying success...", file=sys.stderr)
                    verify_result = await self.condition_evaluator.evaluate(strategy["verify"])
                    if not verify_result:
                        raise Exception("Verification failed")

                # Success!
                print(f"    ✓ {strategy_name} succeeded", file=sys.stderr)
                return

            except Exception as e:
                last_error = e
                print(f"    ✗ {strategy_name} failed: {e}", file=sys.stderr)
                continue

        # All strategies failed
        raise WorkflowError(f"Try block '{step_name}' exhausted all strategies. Last error: {last_error}")

    async def _execute_sequence(self, step: Dict[str, Any]):
        """Execute sequence of steps."""
        steps = step.get("steps", [])
        for substep in steps:
            await self._dispatch_step(substep)

    async def _execute_switch(self, step: Dict[str, Any]):
        """Execute switch statement."""
        cases = step.get("cases", [])

        # Try each case
        for case in cases:
            condition = case.get("condition")
            if condition:
                result = await self.condition_evaluator.evaluate(condition)
                if result:
                    print(f"  → Switch case matched", file=sys.stderr)
                    case_steps = case.get("steps", [])
                    for substep in case_steps:
                        await self._dispatch_step(substep)
                    return

        # Default case
        if "default" in step:
            print(f"  → Using default case", file=sys.stderr)
            default_steps = step["default"].get("steps", [])
            for substep in default_steps:
                await self._dispatch_step(substep)

    def _execute_goto(self, step: Dict[str, Any]):
        """Jump to named step."""
        target = step.get("target")
        if not target:
            raise ValueError("'goto' step missing 'target'")

        if target not in self.step_map:
            raise ValueError(f"goto target '{target}' not found in step map")

        print(f"  → Jumping to: {target}", file=sys.stderr)
        self.next_step_name = target

    def _execute_succeed(self, step: Dict[str, Any]):
        """Explicit success terminal state."""
        message = step.get("message", "Workflow succeeded")
        print(f"  ✓ SUCCESS: {message}", file=sys.stderr)
        self.next_step_name = None  # Terminate

    def _execute_fail(self, step: Dict[str, Any]):
        """Explicit failure terminal state."""
        error = step.get("error", "WORKFLOW_FAILED")
        message = step.get("message", "Workflow failed")
        raise WorkflowError(f"{error}: {message}")

    async def _execute_branch(self, branch: Any):
        """
        Execute a branch (then/else in if, case in switch).

        Branches can be:
        - {"goto": "StepName"} - jump to step
        - {"action": "...", ...} - inline action
        - {"type": "...", ...} - nested workflow structure
        """
        if isinstance(branch, dict):
            if "goto" in branch:
                # Goto jump
                target = branch["goto"]
                if target not in self.step_map:
                    raise ValueError(f"Branch goto target '{target}' not found")
                print(f"    Branch: goto {target}", file=sys.stderr)
                self.next_step_name = target

            elif "action" in branch or "type" in branch:
                # Inline step execution
                await self._dispatch_step(branch)
