# Polling Interval Design for Monitoring Tools

## Problem
The batch orchestrator agent's `monitor_batch_execution` tool is being called repeatedly by the LLM without any delay, resulting in:
- Excessive API calls to Step Functions
- Rapid consumption of Lambda invocations
- Inefficient monitoring pattern
- LLM retrying multiple times until timeout

## Solution
Implement a polling interval mechanism using Step Functions Wait states, similar to human approval workflow.

## Implementation Design

### 1. Tool Configuration Enhancement
Add `polling_interval` field to tool configurations:

```python
{
    "tool_name": "monitor_batch_execution",
    "description": "Monitors batch processing execution progress",
    "polling_interval": 30,  # Wait 30 seconds before allowing next call
    "max_polling_attempts": 20,  # Maximum 20 attempts (10 minutes total)
    # ... rest of config
}
```

### 2. State Machine Generation
Modify the state machine generator to check for `polling_interval`:

```python
# In step_functions_generator_unified_llm.py
if config.get('polling_interval'):
    # Add a wait state before the tool execution
    states[f"Wait Before {tool_name}"] = {
        "Type": "Wait",
        "Seconds": config['polling_interval'],
        "Next": f"Execute {tool_name}"
    }
```

### 3. Enhanced Tool Response
Include polling metadata in the tool response:

```python
{
    "type": "tool_result",
    "tool_use_id": "...",
    "content": {
        "status": "RUNNING",
        "message": "Processing in progress",
        "next_check_in": 30,  # Seconds until next check
        "polling_metadata": {
            "attempt": 3,
            "max_attempts": 20,
            "interval_seconds": 30
        }
    }
}
```

## Benefits
1. **Reduced API Calls**: From potentially 50+ calls to ~20 calls over 10 minutes
2. **Predictable Behavior**: Consistent polling intervals
3. **Cost Savings**: Fewer Lambda invocations and API calls
4. **Better UX**: Clear expectations on when next update will be available
5. **Prevents Timeout**: LLM won't timeout waiting for responses

## Alternative Approaches Considered

### Option A: Client-Side Waiting
- LLM decides when to poll based on response metadata
- **Pros**: Flexible, LLM can adjust strategy
- **Cons**: Relies on LLM behavior, not guaranteed

### Option B: Lambda-Side Throttling
- Lambda function enforces minimum time between calls
- **Pros**: Simple to implement
- **Cons**: Wastes Lambda execution time, still uses invocations

### Option C: State Machine Wait State (CHOSEN)
- State machine enforces wait before tool execution
- **Pros**: Built-in Step Functions feature, reliable, cost-effective
- **Cons**: Requires state machine modification

## Implementation Steps

1. **Update Tool Config** (batch_orchestrator_agent_stack.py):
   - Add `polling_interval: 30` to monitor_batch_execution tool
   - Add `max_polling_attempts: 20` for safety

2. **Modify State Machine Generator** (step_functions_generator_unified_llm.py):
   - Check for `polling_interval` in tool config
   - Insert Wait state if present
   - Route to Wait state instead of direct execution

3. **Update Monitor Lambda** (monitor_execution.py):
   - Include polling metadata in response
   - Calculate estimated completion time if possible
   - Provide clear next steps

4. **System Prompt Enhancement**:
   - Inform the agent about polling intervals
   - Guide on interpreting polling responses
   - Set expectations for long-running operations

## Example State Machine Flow

```
Check for Tool Calls
    ↓
Map Tool Calls
    ↓
Route Tool Call
    ↓
[If monitor_batch_execution]
    ↓
Wait 30 Seconds  ← NEW
    ↓
Execute monitor_batch_execution
    ↓
Return Tool Result
```

## Testing Strategy

1. **Unit Test**: Verify Wait state generation for tools with polling_interval
2. **Integration Test**: Confirm 30-second delays between monitoring calls
3. **End-to-End Test**: Full batch processing with monitoring
4. **Load Test**: Verify reduction in API calls

## Metrics for Success

- **Before**: ~50 monitoring calls in 2 minutes
- **After**: ~4 monitoring calls in 2 minutes (30-second intervals)
- **API Call Reduction**: >90%
- **Cost Reduction**: ~$0.50 per 1000 batch processing operations