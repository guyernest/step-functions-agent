# Execution Index - Design Rationale

## Schema Design

### Primary Key: `executionArn`

**Why executionArn as PK?**
- ✅ **Natural unique identifier** - Each execution has a unique ARN
- ✅ **Simple updates** - Can update the same item multiple times (RUNNING → SUCCEEDED)
- ✅ **Direct lookups** - Can fetch execution details by ARN directly
- ✅ **No composite keys** - Simpler than `agentName + startDate#arn`

### GSI #1: AgentDateIndex
- **PK**: `agentName`
- **SK**: `startDate`

**Use Case**: "Show me all executions for agent X in date range Y-Z"

Query pattern:
```typescript
agentName = 'my-agent' AND startDate BETWEEN '2025-09-29T00:00:00.000Z' AND '2025-09-29T23:59:59.999Z'
```

### GSI #2: StatusDateIndex
- **PK**: `status`
- **SK**: `startDate`

**Use Case**: "Show me all FAILED executions in date range Y-Z"

Query pattern:
```typescript
status = 'FAILED' AND startDate BETWEEN '2025-09-29T00:00:00.000Z' AND '2025-09-29T23:59:59.999Z'
```

## Comparison: Two Design Approaches

### ❌ Old Design (Composite Sort Key)
```
PK: agentName
SK: startDate#executionArn
GSI: status + startDate#executionArn
```

**Problems**:
1. Complex composite sort key (`startDate#executionArn`)
2. Harder to update (need to construct the composite key)
3. More error-prone (string formatting issues)
4. Redundant data in sort key

### ✅ New Design (Simple PK + GSIs)
```
PK: executionArn
GSI1: agentName + startDate
GSI2: status + startDate
```

**Benefits**:
1. Simple primary key (just the ARN)
2. Easy updates (use ARN directly)
3. Clean GSI design (separate concerns)
4. No composite key complexity

## Update Pattern

### Old Design - Update Flow
```typescript
// Step 1: Construct composite key
const sortKey = `${startDate}#${executionArn}`;

// Step 2: Update item
PutItem({
  agentName: 'my-agent',
  startDateArn: sortKey,  // Must construct this exactly right
  status: 'SUCCEEDED',
  ...
});
```

### New Design - Update Flow
```typescript
// Simple - just use the executionArn
PutItem({
  executionArn: executionArn,  // That's it!
  status: 'SUCCEEDED',
  ...
});
```

## Query Patterns

### Query by Agent + Date
**Old**: Query with composite SK range
```typescript
agentName = 'my-agent' AND startDateArn BETWEEN '2025-09-29#' AND '2025-09-29#~'
```
Issues: Need to append `#` and `~` for range queries

**New**: Simple date range
```typescript
agentName = 'my-agent' AND startDate BETWEEN '2025-09-29T00:00:00.000Z' AND '2025-09-29T23:59:59.999Z'
```
Clean and intuitive!

### Query by Status + Date
**Old**: GSI with composite SK
```typescript
status = 'FAILED' AND startDateArn BETWEEN '2025-09-29#' AND '2025-09-29#~'
```

**New**: Simple GSI query
```typescript
status = 'FAILED' AND startDate BETWEEN '2025-09-29T00:00:00.000Z' AND '2025-09-29T23:59:59.999Z'
```

## Data Model

### Item Structure
```json
{
  // Primary Key
  "executionArn": "arn:aws:states:...:execution:my-agent-prod:abc123",

  // GSI Keys
  "agentName": "my-agent",      // AgentDateIndex PK
  "status": "SUCCEEDED",         // StatusDateIndex PK
  "startDate": "2025-09-29T12:34:50.000Z",  // Both GSI SK

  // Other Attributes
  "stateMachineArn": "arn:aws:states:...:stateMachine:my-agent-prod",
  "executionName": "abc123",
  "stopDate": "2025-09-29T12:35:00.000Z",
  "durationSeconds": 10,
  "indexedAt": "2025-09-29T12:35:01.456Z"
}
```

## Why This Design is Better

### 1. Simplicity
- Primary key is just the natural identifier
- No need to construct composite keys
- Easier to understand and maintain

### 2. Reliability
- Less chance of bugs (no string concatenation for keys)
- Updates are idempotent (same PK every time)
- Can't mess up the sort key format

### 3. Flexibility
- Easy to add more GSIs if needed
- Can query by executionArn directly
- GSIs provide clean query patterns

### 4. Performance
- Same query performance as composite key approach
- GSIs are equally efficient
- No performance trade-offs

### 5. Maintainability
- Code is cleaner and easier to read
- Updates are straightforward
- Less cognitive load for developers

## Real-World Example

### Scenario: Update an execution from RUNNING → SUCCEEDED

**Old Design**:
```typescript
// Problem: Need to know the startDate to construct the key
const startDate = execution.startDate;
const sortKey = `${startDate}#${executionArn}`;

await dynamodb.putItem({
  TableName: 'ExecutionIndex',
  Item: {
    agentName: { S: agentName },
    startDateArn: { S: sortKey },  // Hope we got this right!
    status: { S: 'SUCCEEDED' },
    // ...
  }
});
```

**New Design**:
```typescript
// Simple: Just use the executionArn
await dynamodb.putItem({
  TableName: 'ExecutionIndex',
  Item: {
    executionArn: { S: executionArn },  // Easy!
    status: { S: 'SUCCEEDED' },
    // ...
  }
});
```

## Conclusion

Using `executionArn` as the primary key with GSIs for query patterns is:
- ✅ Simpler
- ✅ More reliable
- ✅ Easier to maintain
- ✅ Just as performant
- ✅ More intuitive

This is the **correct design** for this use case!