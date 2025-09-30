# Execution Index Implementation Guide

## Overview
This document outlines the implementation of a DynamoDB index for Step Functions executions to enable efficient date-range queries.

## Architecture

### DynamoDB Table: ExecutionIndex

**Primary Key**:
- **Partition Key**: `executionArn` (String) - Unique identifier for direct updates

**Global Secondary Indexes**:
1. **AgentDateIndex** - Query by agent + date range
   - PK: `agentName` (String)
   - SK: `startDate` (String - ISO-8601)

2. **StatusDateIndex** - Query by status + date range
   - PK: `status` (String)
   - SK: `startDate` (String - ISO-8601)

**Attributes**: executionArn, agentName, stateMachineArn, executionName, status, startDate, stopDate, durationSeconds, indexedAt

### Components Created
1. **indexStepFunctionExecution** - Lambda triggered by EventBridge to populate index
2. **listExecutionsFromIndex** - Lambda to query the index efficiently
3. Table schema definition

## Implementation Steps

### 1. Add Functions to backend.ts

```typescript
import { indexStepFunctionExecution } from './backend/function/indexStepFunctionExecution/resource';
import { listExecutionsFromIndex } from './backend/function/listExecutionsFromIndex/resource';

const backend = defineBackend({
  // ... existing functions
  indexStepFunctionExecution,
  listExecutionsFromIndex,
});
```

### 2. Create ExecutionIndex DynamoDB Table

Add after line 274 in `backend.ts`:

```typescript
// Create ExecutionIndex table for efficient history queries
const executionIndexTableName = `ExecutionIndex-${tableEnvSuffix}`;
const executionIndexTable = new aws_dynamodb.Table(externalDataSourcesStack, 'ExecutionIndexTable', {
  tableName: executionIndexTableName,
  partitionKey: { name: 'executionArn', type: aws_dynamodb.AttributeType.STRING },
  billingMode: aws_dynamodb.BillingMode.PAY_PER_REQUEST,
  pointInTimeRecovery: true,
  removalPolicy: RemovalPolicy.DESTROY, // Change to RETAIN for production
  stream: aws_dynamodb.StreamViewType.NEW_AND_OLD_IMAGES, // For future use
});

// Add GSI for agent + date queries
executionIndexTable.addGlobalSecondaryIndex({
  indexName: 'AgentDateIndex',
  partitionKey: { name: 'agentName', type: aws_dynamodb.AttributeType.STRING },
  sortKey: { name: 'startDate', type: aws_dynamodb.AttributeType.STRING },
  projectionType: aws_dynamodb.ProjectionType.ALL,
});

// Add GSI for status + date queries
executionIndexTable.addGlobalSecondaryIndex({
  indexName: 'StatusDateIndex',
  partitionKey: { name: 'status', type: aws_dynamodb.AttributeType.STRING },
  sortKey: { name: 'startDate', type: aws_dynamodb.AttributeType.STRING },
  projectionType: aws_dynamodb.ProjectionType.ALL,
});
```

### 3. Grant Permissions

Add after the table creation:

```typescript
// Grant permissions to indexStepFunctionExecution Lambda
executionIndexTable.grantWriteData(backend.indexStepFunctionExecution.resources.lambda);
backend.indexStepFunctionExecution.addEnvironment('EXECUTION_INDEX_TABLE_NAME', executionIndexTable.tableName);

// Grant Step Functions permissions to read tags
const indexSfnPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: ['states:ListTagsForResource'],
  resources: ['*'],
});
backend.indexStepFunctionExecution.resources.lambda.addToRolePolicy(indexSfnPolicy);

// Grant permissions to listExecutionsFromIndex Lambda
executionIndexTable.grantReadData(backend.listExecutionsFromIndex.resources.lambda);
backend.listExecutionsFromIndex.addEnvironment('EXECUTION_INDEX_TABLE_NAME', executionIndexTable.tableName);
```

### 4. Create EventBridge Rule

Add these imports at the top of `backend.ts`:

```typescript
import { Rule } from 'aws-cdk-lib/aws-events';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
```

Then add the EventBridge rule (add after ExecutionIndex table creation):

```typescript
// Create EventBridge rule to capture ALL Step Functions execution events
// The Lambda will filter by tags to only index agent executions
const executionEventRule = new Rule(externalDataSourcesStack, 'ExecutionEventRule', {
  ruleName: `step-functions-execution-index-${tableEnvSuffix}`,
  description: 'Capture Step Functions execution events for indexing (filters by tags)',
  eventPattern: {
    source: ['aws.states'],
    detailType: ['Step Functions Execution Status Change'],
    detail: {
      status: ['RUNNING', 'SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED'],
    },
  },
});

// Add Lambda as target
executionEventRule.addTarget(
  new LambdaFunction(backend.indexStepFunctionExecution.resources.lambda, {
    retryAttempts: 2,
  })
);
```

**How it works**:
- EventBridge rule catches **ALL** Step Functions execution events account-wide
- Lambda function reads state machine tags for each event
- Only indexes executions where tags include:
  - `Type=Agent`
  - `Application=StepFunctionsAgent`
- Non-agent executions are quickly filtered out and skipped
- **No per-agent configuration needed** - uses existing tags!

### 5. Add GraphQL Query

In `amplify/data/resource.ts`, add:

```typescript
import { listExecutionsFromIndex } from '../backend/function/listExecutionsFromIndex/resource';

// In the schema definition:
listExecutionsFromIndex: a
  .query()
  .arguments({
    agentName: a.string(),
    status: a.string(),
    maxResults: a.integer(),
    nextToken: a.string(),
    startDateFrom: a.string(),
    startDateTo: a.string(),
  })
  .returns(a.json())
  .handler(a.handler.function(listExecutionsFromIndex))
  .authorization((allow) => [
    allow.authenticated(),
    allow.publicApiKey()
  ]),
```

### 6. Update UI to Use New Query

In `src/pages/History.tsx`, update `fetchExecutions`:

```typescript
// Change from:
const response = await client.queries.listStepFunctionExecutions(params)

// To:
const response = await client.queries.listExecutionsFromIndex(params)
```

### 7. Backfill Historical Data (Optional)

Create a one-time script to populate the index with existing executions:

```bash
# Create backfill script
aws lambda invoke --function-name backfill-execution-index /dev/stdout
```

## Benefits

1. **Performance**: O(1) queries by agent + date range instead of O(n) iteration
2. **Scalability**: Handles thousands of executions efficiently
3. **Cost**: Reduces Step Functions API calls significantly
4. **Flexibility**: Easy to add more indexes or attributes

## Deployment

```bash
cd ui_amplify
npx ampx sandbox
```

## Testing

1. Create a new execution
2. Check DynamoDB table for the indexed entry
3. Query using the History page with date filters
4. Verify fast response times

## Future Enhancements

1. Add TTL for automatic cleanup of old entries
2. Add more GSIs for different query patterns
3. Add execution details caching
4. Add real-time updates via DynamoDB Streams → WebSocket

## Migration Path

1. Deploy the new index table and functions
2. Run backfill for historical data
3. Test the new listExecutionsFromIndex query
4. Update UI to use new query
5. Monitor performance
6. Eventually deprecate old listStepFunctionExecutions query