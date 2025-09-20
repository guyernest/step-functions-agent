# Address Search Batch Tool - Implementation Summary

## What We Built

We've successfully created the **first Step Functions-based tool** in the framework - a batch processor that enriches UK addresses with property information. This groundbreaking implementation demonstrates how to integrate long-running state machines as tools alongside traditional Lambda-based tools.

## Files Created

```
lambda/tools/address-search-batch/
├── config.json                    # Tool configuration and mappings
├── address_mapper.py              # Specialized mapper for UK addresses
├── test_addresses.csv             # Sample test data
├── requirements.txt               # Python dependencies
├── README.md                      # Comprehensive documentation
└── IMPLEMENTATION_SUMMARY.md      # This file

stacks/tools/
└── address_search_batch_tool_stack.py  # CDK stack for deployment
```

## Key Innovations

### 1. Step Functions as a Tool

This is the first tool that:
- **Is a Step Functions state machine**, not a Lambda function
- **Registers with `tool_type: "state_machine"`** in the tool registry
- **Gets invoked via `states:startExecution.sync:2`** by agents
- **Can run for hours** without Lambda timeout constraints

### 2. Configuration-Driven Design

Following the `agentcore_browser` pattern:
- Configuration file (`config.json`) defines mappings and defaults
- Easy to modify without code changes
- Supports runtime overrides via `custom_mappings`

### 3. Clean Integration

The tool integrates seamlessly:
- Uses existing `BatchedToolConstruct` for registration
- Compatible with existing agent infrastructure
- No changes needed to shared infrastructure stack

## How to Deploy

### Step 1: Add to app.py

Add these lines to `/Users/guy/projects/step-functions-agent/app.py`:

```python
# At the top with other imports (around line 36):
from stacks.tools.address_search_batch_tool_stack import AddressSearchBatchToolStack

# In the deployment section (around line 314, after agentcore_browser_tools):
# Address Search Batch Tool - Step Functions batch processor
address_search_batch = AddressSearchBatchToolStack(
    app,
    f"AddressSearchBatchToolStack-{environment}",
    env_name=environment,
    env=env,
    description=f"Address search batch processor for {environment} environment"
)
address_search_batch.add_dependency(shared_infrastructure_stack)
```

### Step 2: Deploy

```bash
# Deploy the new tool
cdk deploy AddressSearchBatchToolStack-prod
```

### Step 3: Test

Upload test data and monitor execution:
```bash
# Upload test CSV
aws s3 cp lambda/tools/address-search-batch/test_addresses.csv \
  s3://your-bucket/test/addresses.csv

# Start execution (can be done via agent or directly)
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:eu-west-1:${ACCOUNT}:stateMachine:address-search-batch-prod \
  --input '{"csv_s3_uri":"s3://your-bucket/test/addresses.csv","output_bucket":"address-search-batch-results-prod-${ACCOUNT}"}'
```

## Integration Requirements

### For Agents Using This Tool

Agents need to handle `tool_type: "state_machine"` in their Step Functions definition:

```json
{
  "Type": "Choice",
  "Choices": [
    {
      "Variable": "$.tool.tool_type",
      "StringEquals": "state_machine",
      "Next": "InvokeStateMachineTool"
    }
  ]
},
"InvokeStateMachineTool": {
  "Type": "Task",
  "Resource": "arn:aws:states:::states:startExecution.sync:2",
  "Parameters": {
    "StateMachineArn.$": "$.tool.resource_arn",
    "Input.$": "$.tool_input"
  }
}
```

### Tool Registry Schema

The tool is registered with these key fields:
```json
{
  "tool_name": "address_search_batch",
  "tool_type": "state_machine",        // NEW: Indicates Step Functions tool
  "resource_arn": "arn:aws:states:...", // State machine ARN
  "language": "state_machine",          // Special language type
  "config": {                           // Tool-specific configuration
    "target_agent": "web-search-agent-unified",
    "default_mappings": {...}
  }
}
```

## Architecture Benefits

### Why Step Functions for Batch Processing?

1. **No Timeout Limits**: Can process thousands of rows over hours
2. **Cost Efficient**: Pay only for state transitions, not idle time
3. **Native CSV Support**: Distributed Map reads CSV directly from S3
4. **Visual Monitoring**: Step Functions console shows real-time progress
5. **Automatic Parallelization**: Process multiple addresses concurrently

### Comparison with Lambda Tools

| Aspect | Lambda Tool | Step Functions Tool |
|--------|-------------|-------------------|
| Max Runtime | 15 minutes | Unlimited |
| Cost Model | Per millisecond | Per state transition |
| CSV Processing | Must parse in Lambda | Native S3 reader |
| Concurrency | Lambda limits | Configurable Map state |
| Monitoring | CloudWatch Logs | Visual workflow |

## Future Enhancements

### Immediate Next Steps

1. **Update Agent Generator**: Modify `step_functions_generator.py` to handle `tool_type` routing
2. **Create More Batch Tools**: Apply this pattern to other batch scenarios
3. **Add Streaming Results**: Return results as they complete, not just at the end

### Long-term Vision

- **Hybrid Tools**: Tools that can run as Lambda for small inputs or Step Functions for large batches
- **Tool Composition**: Chain multiple tools in a single state machine
- **Dynamic Tool Discovery**: Agents automatically select Lambda vs Step Functions based on input size

## Summary

We've successfully created a new class of tools in the framework - Step Functions-based tools that can handle long-running batch operations. The `address_search_batch` tool demonstrates:

1. ✅ Clean integration with existing tool registry
2. ✅ Configuration-driven design following established patterns
3. ✅ Specialized mappers for domain-specific transformations
4. ✅ Full documentation and test data
5. ✅ CDK stack ready for deployment

This opens up new possibilities for the framework, allowing agents to orchestrate complex, long-running workflows that were previously impossible with Lambda-based tools alone.