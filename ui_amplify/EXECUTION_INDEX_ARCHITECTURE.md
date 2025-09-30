# Execution Index Architecture

## Event Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Step Functions Agents                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Agent A    │  │   Agent B    │  │   Agent C    │          │
│  │ (prod)       │  │ (prod)       │  │ (prod)       │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         │ Tags:            │ Tags:            │ Tags:            │
│         │ Type=Agent       │ Type=Agent       │ Type=Agent       │
│         │ Application=     │ Application=     │ Application=     │
│         │ StepFunctions    │ StepFunctions    │ StepFunctions    │
│         │ Agent            │ Agent            │ Agent            │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          │ Execution Events │                  │
          └──────────┬───────┴──────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   EventBridge Rule   │
          │                      │
          │  Pattern:            │
          │  - source: aws.states│
          │  - detailType:       │
          │    Execution Status  │
          │    Change            │
          │  - status:           │
          │    RUNNING,          │
          │    SUCCEEDED, etc    │
          └──────────┬───────────┘
                     │
                     │ Triggers on ALL Step Functions
                     │ execution events (account-wide)
                     │
                     ▼
       ┌─────────────────────────────────┐
       │  indexStepFunctionExecution     │
       │  Lambda Function                │
       │                                 │
       │  1. Receive event               │
       │  2. Read state machine tags     │
       │  3. Check if agent:             │
       │     - Type=Agent?               │
       │     - Application=              │
       │       StepFunctionsAgent?       │
       │  4. If yes → write to DynamoDB  │
       │  5. If no → skip (exit early)   │
       └─────────────┬───────────────────┘
                     │
                     │ Writes only
                     │ agent executions
                     │
                     ▼
          ┌──────────────────────┐
          │   DynamoDB Table     │
          │   ExecutionIndex     │
          │                      │
          │  PK: executionArn    │
          │  GSI1: agent+date    │
          │  GSI2: status+date   │
          └──────────┬───────────┘
                     │
                     │ Fast queries
                     │
                     ▼
       ┌─────────────────────────────────┐
       │  listExecutionsFromIndex        │
       │  Lambda Function                │
       │                                 │
       │  Queries DynamoDB by:           │
       │  - agentName + date range       │
       │  - status + date range          │
       │                                 │
       │  Returns paginated results      │
       └─────────────┬───────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   GraphQL API        │
          │   (AppSync)          │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   React UI           │
          │   History Page       │
          └──────────────────────┘
```

## Key Points

### 1. Single EventBridge Rule
- **One rule** for the entire account
- Catches all Step Functions execution events
- No per-agent configuration needed
- No changes to existing agent stacks

### 2. Tag-Based Filtering
- Lambda reads tags from state machine ARN
- Only indexes if both tags exist:
  - `Type=Agent`
  - `Application=StepFunctionsAgent`
- Non-agent executions are skipped immediately

### 3. No Agent Stack Changes Required
- Uses existing tags already on agents
- Agent stacks don't need to know about indexing
- Separation of concerns: agents do their job, UI handles indexing

### 4. Automatic for New Agents
- Deploy a new agent with correct tags
- It's automatically indexed
- No additional configuration

## Example Event Flow - Full Lifecycle

### 1. Execution Starts (RUNNING)

```json
// EventBridge captures this event
{
  "source": "aws.states",
  "detail-type": "Step Functions Execution Status Change",
  "detail": {
    "executionArn": "arn:aws:states:us-west-2:123:execution:my-agent-prod:abc123",
    "stateMachineArn": "arn:aws:states:us-west-2:123:stateMachine:my-agent-prod",
    "name": "abc123",
    "status": "RUNNING",
    "startDate": 1234567890000
  }
}

// Lambda writes to DynamoDB:
{
  executionArn: "arn:aws:states:us-west-2:123:execution:my-agent-prod:abc123",  // PK
  agentName: "my-agent",           // GSI1 PK
  startDate: "2025-09-29T12:34:50.000Z",  // GSI1 SK, GSI2 SK
  status: "RUNNING",               // GSI2 PK
  stateMachineArn: "arn:aws:states:us-west-2:123:stateMachine:my-agent-prod",
  executionName: "abc123",
  indexedAt: "2025-09-29T12:34:51.123Z"
}
```

### 2. Execution Completes (SUCCEEDED/FAILED/TIMED_OUT/ABORTED)

```json
// EventBridge captures completion event
{
  "source": "aws.states",
  "detail-type": "Step Functions Execution Status Change",
  "detail": {
    "executionArn": "arn:aws:states:us-west-2:123:execution:my-agent-prod:abc123",
    "stateMachineArn": "arn:aws:states:us-west-2:123:stateMachine:my-agent-prod",
    "name": "abc123",
    "status": "SUCCEEDED",
    "startDate": 1234567890000,
    "stopDate": 1234567900000
  }
}

// Lambda UPDATES the same DynamoDB item (using PK: executionArn):
{
  executionArn: "arn:aws:states:us-west-2:123:execution:my-agent-prod:abc123",  // PK (same)
  agentName: "my-agent",
  startDate: "2025-09-29T12:34:50.000Z",
  status: "SUCCEEDED",              // ← Updated
  stateMachineArn: "arn:aws:states:us-west-2:123:stateMachine:my-agent-prod",
  executionName: "abc123",
  stopDate: "2025-09-29T12:35:00.000Z",    // ← Added
  durationSeconds: 10,               // ← Added (calculated)
  indexedAt: "2025-09-29T12:35:01.456Z"    // ← Updated
}
```

### Supported Status Values

The EventBridge rule captures these status changes:
- **RUNNING** - Execution started (creates initial index entry)
- **SUCCEEDED** - Execution completed successfully (updates with stopDate & duration)
- **FAILED** - Execution failed (updates with stopDate & duration)
- **TIMED_OUT** - Execution exceeded timeout (updates with stopDate & duration)
- **ABORTED** - Execution was aborted (updates with stopDate & duration)

## Cost Considerations

### EventBridge
- Free tier: 1 million events/month
- After: $1.00 per million events
- For 10,000 executions/month: ~$0.01

### Lambda Invocations
- Free tier: 1 million requests/month
- After: $0.20 per million requests
- For 10,000 executions/month: ~$0.002

### DynamoDB
- On-demand pricing: ~$1.25 per million writes
- For 10,000 executions/month: ~$0.01

**Total cost for 10,000 executions/month: ~$0.02**

## Comparison to Previous Approach

| Aspect | Old (Step Functions API) | New (DynamoDB Index) |
|--------|-------------------------|----------------------|
| Query by date | Not supported, must fetch all | Native support, O(1) lookup |
| Query by agent | Must list all state machines | Direct partition key query |
| Pagination | Complex multi-state-machine logic | Native DynamoDB pagination |
| Performance | Slow (iterates all machines) | Fast (indexed queries) |
| Cost per query | High (many API calls) | Low (single DynamoDB query) |
| Scalability | Poor (linear with # of machines) | Excellent (constant time) |
| Setup | None | One-time EventBridge rule |

## Summary

✅ **Simple**: One EventBridge rule, no per-agent setup
✅ **Robust**: Uses existing tags, automatic for new agents
✅ **Fast**: O(1) queries vs O(n) iteration
✅ **Cheap**: ~$0.02 per 10,000 executions
✅ **Scalable**: Handles millions of executions efficiently