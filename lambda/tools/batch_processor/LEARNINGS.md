# Batch Processor Learnings

## Key Design Decisions

### 1. INLINE Map Mode vs DISTRIBUTED
**Problem**: Lambda's 15-minute timeout limitation for batch processing.

**Solution**: Use Step Functions with INLINE Map mode for synchronous agent execution:
- INLINE mode supports `.sync:2` for synchronous execution
- DISTRIBUTED mode runs in Express workflow which doesn't support `.sync`
- Trade-off: INLINE limited to 40 concurrent executions vs DISTRIBUTED's 10,000

### 2. Agent Integration Architecture
**Problem**: Need to call Agent Core agents from batch processor.

**Solution**:
- Batch processor Lambda prepares and maps input
- Step Functions Map state iterates over items
- Each iteration calls Agent Core synchronously
- Results collector Lambda aggregates outputs

### 3. Health Check Integration
**Issue**: Agent Core requires health checks or fails with "Runtime health check failed or timed out"

**Resolution**:
- Agent Core agents must implement `/health` and `/ready` endpoints
- These endpoints must return proper HTTP status codes and JSON responses
- Without these, batch processor cannot call the agent

## Implementation Details

### State Machine Structure
```json
{
  "MapState": {
    "Type": "Map",
    "MaxConcurrency": 10,
    "ItemProcessor": {
      "ProcessorConfig": {
        "Mode": "INLINE"  // Critical for .sync:2 support
      },
      "States": {
        "InvokeAgent": {
          "Type": "Task",
          "Resource": "arn:aws:states:::states:startExecution.sync:2",
          "Parameters": {
            "StateMachineArn.$": "$.target.arn",
            "Input.$": "$.mapped_input"
          }
        }
      }
    }
  }
}
```

### Input Mapping
The `address_mapper.py` transforms CSV data to agent-compatible format:
```python
{
  "messages": [
    {
      "role": "user",
      "content": "Query built from CSV row"
    }
  ]
}
```

## Troubleshooting

### Common Issues
1. **PointInTimeRecoverySpecification Error**: Use `point_in_time_recovery=True` in CDK
2. **Express workflow sync error**: Switch from DISTRIBUTED to INLINE mode
3. **Agent input format**: Must use `messages` array format
4. **IAM permissions**: Lambda needs `states:DescribeExecution` permission

### Testing Approach
1. Deploy batch processor stack
2. Ensure Agent Core is running with health checks
3. Upload test CSV to S3
4. Trigger batch processor
5. Monitor DynamoDB for results

## Future Improvements
- Implement DynamoDB-based architecture for unlimited batch sizes
- Add retry logic with exponential backoff
- Support for multiple agent types in single batch
- Real-time progress tracking via WebSocket