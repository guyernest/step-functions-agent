import { defineFunction } from '@aws-amplify/backend';

export const executionIndexTable = {
  tableName: 'ExecutionIndex',
  partitionKey: {
    name: 'agentName',
    type: 'S' as const,
  },
  sortKey: {
    name: 'startDateArn',
    type: 'S' as const,
  },
  globalSecondaryIndexes: [
    {
      indexName: 'StatusDateIndex',
      partitionKey: {
        name: 'status',
        type: 'S' as const,
      },
      sortKey: {
        name: 'startDateArn',
        type: 'S' as const,
      },
      projectionType: 'ALL' as const,
    },
  ],
};