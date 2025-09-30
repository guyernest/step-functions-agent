import {
  DynamoDBClient,
  QueryCommand,
} from '@aws-sdk/client-dynamodb';
import { unmarshall } from '@aws-sdk/util-dynamodb';

const dynamoClient = new DynamoDBClient({});

const TABLE_NAME = process.env.EXECUTION_INDEX_TABLE_NAME || 'ExecutionIndex';

interface Execution {
  executionArn: string;
  stateMachineArn: string;
  name: string;
  status: string;
  startDate: string;
  stopDate?: string;
  agentName: string;
  durationSeconds?: number;
}

interface PaginatedResponse {
  executions: Execution[];
  nextToken?: string;
  hasMore: boolean;
  totalCount?: number;
  metadata?: {
    fromIndex: boolean;
    fetchTime: number;
  };
}

export const handler = async (event: any): Promise<string> => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  const startTime = Date.now();

  try {
    const {
      agentName,
      status,
      maxResults = 50,
      nextToken,
      startDateFrom,
      startDateTo,
    } = event.arguments || {};

    // Build query parameters
    let keyConditionExpression: string;
    let expressionAttributeValues: any;
    let indexName: string;
    let expressionAttributeNames: any | undefined;

    if (agentName) {
      // Query by agent name using AgentDateIndex GSI
      indexName = 'AgentDateIndex';
      keyConditionExpression = 'agentName = :agentName';
      expressionAttributeValues = {
        ':agentName': { S: agentName },
      };

      // Add date range if provided
      if (startDateFrom || startDateTo) {
        const fromDate = startDateFrom ? `${startDateFrom}T00:00:00.000Z` : '1970-01-01T00:00:00.000Z';
        const toDate = startDateTo ? `${startDateTo}T23:59:59.999Z` : '9999-12-31T23:59:59.999Z';

        keyConditionExpression += ' AND startDate BETWEEN :startDate AND :endDate';
        expressionAttributeValues[':startDate'] = { S: fromDate };
        expressionAttributeValues[':endDate'] = { S: toDate };
      }
    } else if (status) {
      // Query by status using StatusDateIndex GSI
      indexName = 'StatusDateIndex';
      keyConditionExpression = '#status = :status';
      expressionAttributeNames = { '#status': 'status' };
      expressionAttributeValues = {
        ':status': { S: status },
      };

      // Add date range if provided
      if (startDateFrom || startDateTo) {
        const fromDate = startDateFrom ? `${startDateFrom}T00:00:00.000Z` : '1970-01-01T00:00:00.000Z';
        const toDate = startDateTo ? `${startDateTo}T23:59:59.999Z` : '9999-12-31T23:59:59.999Z';

        keyConditionExpression += ' AND startDate BETWEEN :startDate AND :endDate';
        expressionAttributeValues[':startDate'] = { S: fromDate };
        expressionAttributeValues[':endDate'] = { S: toDate };
      }
    } else {
      // No agent or status filter - not supported efficiently
      const response: PaginatedResponse = {
        executions: [],
        hasMore: false,
        totalCount: 0,
        metadata: {
          fromIndex: true,
          fetchTime: Date.now() - startTime,
        },
      };
      return JSON.stringify(response);
    }

    // Build filter expression for status if querying by agent
    let filterExpression: string | undefined;

    if (agentName && status) {
      if (!expressionAttributeNames) {
        expressionAttributeNames = {};
      }
      filterExpression = '#status = :statusFilter';
      expressionAttributeNames['#status'] = 'status';
      expressionAttributeValues[':statusFilter'] = { S: status };
    }

    const queryCommand = new QueryCommand({
      TableName: TABLE_NAME,
      IndexName: indexName,
      KeyConditionExpression: keyConditionExpression,
      FilterExpression: filterExpression,
      ExpressionAttributeValues: expressionAttributeValues,
      ExpressionAttributeNames: expressionAttributeNames,
      Limit: maxResults,
      ExclusiveStartKey: nextToken ? JSON.parse(Buffer.from(nextToken, 'base64').toString('utf-8')) : undefined,
      ScanIndexForward: false, // Sort descending (most recent first)
    });

    const result = await dynamoClient.send(queryCommand);

    const executions: Execution[] = (result.Items || []).map(item => {
      const unmarshalled = unmarshall(item) as any;
      return {
        executionArn: unmarshalled.executionArn,
        stateMachineArn: unmarshalled.stateMachineArn,
        name: unmarshalled.executionName,
        status: unmarshalled.status,
        startDate: unmarshalled.startDate,
        stopDate: unmarshalled.stopDate,
        agentName: unmarshalled.agentName,
        durationSeconds: unmarshalled.durationSeconds,
      };
    });

    const responseNextToken = result.LastEvaluatedKey
      ? Buffer.from(JSON.stringify(result.LastEvaluatedKey)).toString('base64')
      : undefined;

    const response: PaginatedResponse = {
      executions,
      nextToken: responseNextToken,
      hasMore: !!result.LastEvaluatedKey,
      totalCount: executions.length,
      metadata: {
        fromIndex: true,
        fetchTime: Date.now() - startTime,
      },
    };

    console.log(`Returning ${executions.length} executions from index`);
    return JSON.stringify(response);
  } catch (error) {
    console.error('Error querying execution index:', error);
    const errorResponse: PaginatedResponse = {
      executions: [],
      hasMore: false,
      metadata: {
        fromIndex: true,
        fetchTime: Date.now() - startTime,
      },
    };
    return JSON.stringify(errorResponse);
  }
};