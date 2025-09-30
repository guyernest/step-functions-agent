# Execution Index - Implementation Summary

## What We Built

A DynamoDB-based index for Step Functions executions that captures the **full lifecycle** of every agent execution.

## Full Lifecycle Tracking

### Event Capture
EventBridge captures **5 status changes** for each execution:
1. **RUNNING** - Execution starts
2. **SUCCEEDED** - Execution completes successfully
3. **FAILED** - Execution fails with error
4. **TIMED_OUT** - Execution exceeds timeout
5. **ABORTED** - Execution manually aborted

### Data Storage
Each execution gets a **single DynamoDB item** that is:
- **Created** when execution starts (RUNNING)
- **Updated** when execution completes (SUCCEEDED/FAILED/TIMED_OUT/ABORTED)

### DynamoDB Schema

**Primary Key**: `executionArn` (for simple, idempotent updates)

**Global Secondary Indexes**:
1. **AgentDateIndex** - PK: `agentName`, SK: `startDate`
2. **StatusDateIndex** - PK: `status`, SK: `startDate`

### Stored Information

#### Always Present
- `executionArn` - Unique execution ARN (Primary Key)
- `agentName` - Agent identifier from tags (GSI1 PK)
- `status` - Current status (GSI2 PK)
- `startDate` - When execution started (Both GSI SK)
- `stateMachineArn` - State machine ARN
- `executionName` - Execution name
- `indexedAt` - When index was last updated

#### Added on Completion
- `stopDate` - When execution finished
- `durationSeconds` - Execution duration (calculated)

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                   Execution Lifecycle                        │
└─────────────────────────────────────────────────────────────┘

Step 1: Execution Starts
   Agent Execution → Step Functions → EventBridge
                                           │
                                           ▼
                                    Lambda (index)
                                           │
                                           ▼
                                    DynamoDB: CREATE
                                    {
                                      status: "RUNNING",
                                      startDate: "...",
                                      // No stopDate yet
                                    }

Step 2: Execution Completes
   Agent Execution → Step Functions → EventBridge
                                           │
                                           ▼
                                    Lambda (index)
                                           │
                                           ▼
                                    DynamoDB: UPDATE same item
                                    {
                                      status: "SUCCEEDED",
                                      startDate: "...",
                                      stopDate: "...",      ← Added
                                      durationSeconds: 45   ← Calculated
                                    }
```

## UI Benefits

### What Users See
1. **Real-time updates**: Executions appear immediately when they start
2. **Status tracking**: See RUNNING executions in progress
3. **Completion info**: See final status, stop time, and duration
4. **Fast queries**: Filter by date range, agent, or status instantly

### Example UI Display

```
History Page
┌────────────────────────────────────────────────────────────┐
│ Agent: my-agent     Status: All     Date: Today            │
├────────────────────────────────────────────────────────────┤
│ ✓ SUCCEEDED  abc123  12:35:00  10s   View Details          │
│ ⚡ RUNNING   def456  12:40:15  -     View Details          │
│ ✗ FAILED    ghi789  12:30:00  5s    View Details          │
└────────────────────────────────────────────────────────────┘
```

## Key Improvements

### Before (Step Functions API)
❌ Slow queries (iterate all state machines)
❌ No date filtering support
❌ Complex pagination
❌ Many API calls
❌ Can't efficiently find today's executions

### After (DynamoDB Index)
✅ Fast queries (indexed lookups)
✅ Native date range support
✅ Simple pagination
✅ Single query
✅ Instant results for any date range

## Configuration Required

### Backend (backend.ts)
1. Create DynamoDB table with GSI
2. Add EventBridge rule (captures all Step Functions events)
3. Grant Lambda permissions
4. Wire Lambda to table

### No Agent Changes
- Uses existing tags
- No modifications to agent stacks
- Works automatically for all agents

## Implementation Checklist

- [ ] Add Lambda functions to `backend.ts`
- [ ] Create ExecutionIndex DynamoDB table
- [ ] Add EventBridge rule
- [ ] Grant permissions
- [ ] Add GraphQL query
- [ ] Update UI to use new query
- [ ] Test with new execution
- [ ] Verify all statuses tracked (RUNNING → SUCCEEDED/FAILED/etc)
- [ ] Optional: Backfill historical data

## Testing

```bash
# 1. Deploy
cd ui_amplify
npx ampx sandbox

# 2. Trigger an agent execution
# (Use UI or AWS CLI)

# 3. Check DynamoDB
aws dynamodb scan --table-name ExecutionIndex-sandbox-guy

# 4. Verify you see:
# - Initial entry with status=RUNNING
# - Updated entry with status=SUCCEEDED and stopDate

# 5. Test UI
# - Go to History page
# - Filter by today
# - Should see the execution immediately
```

## Next Steps

1. Follow `EXECUTION_INDEX_IMPLEMENTATION.md` for detailed integration
2. Deploy to sandbox first
3. Test full lifecycle (start → complete)
4. Deploy to prod
5. Optional: Add backfill script for historical data

## Additional Features We Can Add Later

- [ ] TTL for automatic cleanup after 90 days
- [ ] Error messages stored in index
- [ ] Input/output size tracking
- [ ] Cost tracking per execution
- [ ] Real-time updates via WebSocket
- [ ] Export to S3 for analytics