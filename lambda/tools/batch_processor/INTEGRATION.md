# Batch Processor Tool Integration Guide

## Architecture Decision: Step Functions as a Tool

### The Problem
Traditional Lambda-based tools have a 15-minute execution limit and incur costs for idle time when waiting for long-running operations. The batch processor needs to:
- Run for hours or potentially days
- Process thousands of rows in parallel
- Wait for agent/tool completions without Lambda timeout
- Return results to the calling agent

### The Solution: Direct Step Functions Invocation

Instead of wrapping the batch processor in a Lambda function, we register it as a **Step Functions-based tool** that agents invoke directly using `states:startExecution.sync:2`.

## How It Works

### 1. Tool Registration
The batch processor state machine is registered in the tool registry with:
```python
{
    "tool_name": "batch_processor",
    "tool_type": "state_machine",  # New field
    "resource_arn": "arn:aws:states:region:account:stateMachine:batch-processor",
    "description": "Process CSV batches through agents/tools",
    "input_schema": {...}
}
```

### 2. Agent Invocation
When an agent needs to use the batch processor, the Step Functions generator creates:
```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::states:startExecution.sync:2",
  "Parameters": {
    "StateMachineArn.$": "$.tool.resource_arn",
    "Input": {
      "csv_s3_uri.$": "$.csv_uri",
      "target.$": "$.target_config",
      "input_mapping.$": "$.mapping_config"
    }
  },
  "ResultSelector": {
    "output_csv.$": "$.Output.csv_location",
    "processed_rows.$": "$.Output.row_count",
    "execution_time.$": "$.Output.execution_time_ms"
  },
  "End": true
}
```

### 3. Synchronous Execution
- `.sync:2` means the agent waits for the batch processor to complete
- No Lambda timeout constraints
- Direct output returned to the agent
- Can run for hours/days if needed

## File Structure

```
lambda/tools/batch_processor/
├── README.md                         # User documentation
├── INTEGRATION.md                    # This file - integration patterns
├── batch-execution-design.md         # Original design document
├── state_machine_definition.json     # Step Functions ASL definition
├── requirements.txt                  # Python dependencies for Lambdas
├── input_mapper.py                   # Lambda: Transform CSV row to agent/tool input
├── output_mapper.py                  # Lambda: Transform agent/tool output to enriched row
└── json_to_csv.py                    # Lambda: Convert JSON results to final CSV
```

## Component Responsibilities

### State Machine (state_machine_definition.json)
- Uses **Distributed Map** to process CSV directly from S3
- Native CSV reading via ItemReader - no parsing Lambda needed!
- Manages parallel execution with configurable MaxConcurrency
- Handles retries and error recovery
- Writes results via ResultWriter to S3 as JSON
- No Lambda wrapper - invoked directly via `states:startExecution.sync:2`

### Supporting Lambda Functions
These are **not** the tool itself, but lightweight functions used within the Distributed Map iterator:

#### input_mapper.py
- Transforms a single CSV row to agent/tool input format
- Applies column mappings and transformations
- Handles concat, template, and JSONPath operations
- Runs once per CSV row within the Map iterator

#### output_mapper.py
- Transforms agent/tool output back to enriched row format
- Merges original row data with new columns
- Adds execution metadata (status, timing, errors)
- Runs once per CSV row after agent/tool execution

#### json_to_csv.py
- Reads JSON Lines output from ResultWriter (typically 1-2 files)
- Converts to CSV format with proper headers
- Preserves column ordering (data columns, then metadata columns)
- Runs once at the end of batch processing

## CDK Stack Implementation

The CDK stack will:

```python
# stacks/tools/batch_processor_tool_stack.py
class BatchProcessorToolStack(Stack):
    def __init__(self, scope, id, **kwargs):
        # Create supporting Lambda functions
        csv_handler = create_lambda("csv_handler", ...)
        mapper = create_lambda("mapper", ...)
        
        # Create the state machine
        batch_processor = StateMachine(
            self, "BatchProcessor",
            definition=load_definition_with_lambdas(
                csv_handler.function_arn,
                mapper.function_arn
            ),
            timeout=Duration.days(7)
        )
        
        # Register as a Step Functions tool (not Lambda)
        BatchedToolConstruct(
            self, "BatchProcessorTool",
            tools=[{
                "tool_name": "batch_processor",
                "tool_type": "state_machine",  # KEY DIFFERENCE
                "resource_arn": batch_processor.state_machine_arn,
                # ... rest of configuration
            }]
        )
```

## Benefits of This Approach

1. **No Lambda Timeout**: Can run for days if needed
2. **No Idle Costs**: Step Functions only charges for state transitions
3. **Native Integration**: Uses AWS service integrations directly
4. **Observability**: Full Step Functions execution history and visualization
5. **Framework Consistency**: Still uses tool registry and discovery

## Migration Path for Other Long-Running Tools

This pattern can be applied to other tools that face Lambda timeout issues:

1. **Web Search Agent**: Currently uses Lambda with blocking wait
2. **Document Processing**: Large document batches
3. **Data Pipeline Tools**: ETL operations

Each can be migrated to Step Functions-based tools using this same pattern.

## Testing Strategy

### Unit Tests
- Test Lambda functions independently (csv_handler, mapper)
- Mock S3 and Athena interactions

### Integration Tests
- Deploy test state machine
- Use small CSV files (10-20 rows)
- Verify end-to-end flow

### Load Tests
- Test with large CSVs (10,000+ rows)
- Verify parallel execution limits
- Monitor costs and performance

## Key Differences from Lambda Tools

| Aspect | Lambda Tool | Step Functions Tool |
|--------|------------|-------------------|
| Invocation | `lambda:invoke` | `states:startExecution.sync:2` |
| Timeout | 15 minutes max | No limit |
| Cost Model | Per millisecond | Per state transition |
| Idle Cost | Yes (blocking) | No |
| Observability | CloudWatch Logs | Step Functions Console |
| Error Handling | Try/catch in code | State machine retry/catch |
| Concurrency | Lambda concurrency | Map state MaxConcurrency |

## Future Enhancements

1. **Streaming Results**: Use S3 notifications to stream results as they complete
2. **Resume Capability**: Checkpoint progress for resumable batches
3. **Dynamic Scaling**: Adjust concurrency based on error rates
4. **Cost Optimization**: Use Spot instances for large batches
5. **Multi-Format Support**: Extend beyond CSV to JSON, Parquet, etc.