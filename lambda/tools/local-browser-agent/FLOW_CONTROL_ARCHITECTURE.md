# Flow Control Architecture

## Design Philosophy

Inspired by AWS Step Functions, this workflow engine uses **explicit flow control** instead of implicit index management. This eliminates index increment bugs and makes workflow execution predictable and debuggable.

## Flow Control Directives

### 1. Default Sequential Flow
If no flow directive is specified, execution proceeds to the next step in the array:

```json
{
  "steps": [
    {"action": "navigate", "url": "..."},
    {"action": "click", "locator": {...}}  // Automatically follows from previous
  ]
}
```

### 2. Explicit Next (`next`)
Explicitly specify which named step to execute next:

```json
{
  "type": "sequence",
  "name": "PerformLogin",
  "steps": [...],
  "next": "PerformSearch"  // Jump to PerformSearch after this sequence
}
```

### 3. Goto (`goto`)
Jump to any named step (used in branches):

```json
{
  "type": "if",
  "name": "CheckAuth",
  "condition": {...},
  "then": {
    "goto": "PerformLogin"  // Jump to login
  }
}
```

### 4. End Workflow (`end`)
Mark this as the final step - workflow terminates successfully:

```json
{
  "type": "sequence",
  "name": "ExtractResults",
  "steps": [...],
  "end": true  // Workflow ends here
}
```

### 5. Succeed Step (`succeed`)
Explicit success terminal state:

```json
{
  "type": "succeed",
  "name": "WorkflowSuccess",
  "message": "Broadband availability data extracted successfully"
}
```

### 6. Fail Step (`fail`)
Explicit failure terminal state:

```json
{
  "type": "fail",
  "name": "WorkflowFailure",
  "error": "LOGIN_FAILED",
  "message": "Unable to authenticate with provided credentials"
}
```

## Flow Resolution Priority

When a step completes, the workflow executor determines the next step using this priority:

1. **goto** - Always honored, jumps to named step
2. **end: true** - Terminates workflow successfully
3. **next** - Jumps to named step
4. **default** - Proceeds to next step in array
5. **array boundary** - If at end of array with no directive, workflow ends

## Branch Flow Control

Branches (then/else in if, strategies in try, cases in switch) support:

```json
{
  "then": {
    "goto": "StepName"  // Jump to step
  }
}

{
  "then": {
    "action": "click",  // Execute action, continue
    "locator": {...}
  }
}

{
  "then": {
    "type": "sequence",  // Execute nested workflow
    "steps": [...]
  }
}
```

**Note:** `continue: true` is **deprecated** - it's implicit behavior (proceed to next step).

## Execution Model

```python
def execute_workflow():
    current_step_name = start_step or steps[0].name

    while current_step_name is not None:
        step = find_step(current_step_name)
        execute_step(step)

        # Determine next step
        if step.has("goto"):
            current_step_name = step.goto
        elif step.has("end") and step.end:
            current_step_name = None  # Terminate
        elif step.has("next"):
            current_step_name = step.next
        elif step.type == "succeed":
            current_step_name = None  # Success terminal
        elif step.type == "fail":
            raise WorkflowError(step.message)
        else:
            # Default: next in array
            current_step_name = get_next_in_array(step)
```

## Benefits

1. **No index management** - Eliminated all increment/decrement logic
2. **Clear termination** - Explicit end states
3. **Predictable flow** - Always know where execution goes next
4. **Better debugging** - Logs show "Going to: StepName" instead of index changes
5. **Simpler code** - No `is_top_level` parameters, no nested increment tracking
6. **Flexible** - Easy to add loops, retries, parallel execution in future

## Migration from Index-Based

Old pattern:
```json
{
  "steps": [
    {"type": "sequence", "name": "Step1", "steps": [...]},
    {"type": "sequence", "name": "Step2", "steps": [...]}
  ]
}
```

New pattern (optional explicit flow):
```json
{
  "steps": [
    {"type": "sequence", "name": "Step1", "steps": [...], "next": "Step2"},
    {"type": "sequence", "name": "Step2", "steps": [...], "end": true}
  ]
}
```

Or rely on default sequential flow (backward compatible):
```json
{
  "steps": [
    {"type": "sequence", "name": "Step1", "steps": [...]},
    {"type": "sequence", "name": "Step2", "steps": [...]}
  ]
}
```
Last step auto-ends.

## Validation Rules

1. All `goto` and `next` targets must exist in step_map
2. Only one terminal directive per step (end, succeed, fail)
3. `succeed` and `fail` steps cannot have `next` or `goto`
4. At least one step must be terminal (end/succeed) or workflow must reach array end
5. No circular references without explicit termination condition

## Future Extensions

- **Parallel execution**: `"type": "parallel"` to run branches concurrently
- **Map state**: `"type": "map"` to iterate over array
- **Wait state**: `"type": "wait"` with duration or timestamp
- **Choice optimization**: Compile common condition patterns
- **Retry policies**: Per-step retry configuration
