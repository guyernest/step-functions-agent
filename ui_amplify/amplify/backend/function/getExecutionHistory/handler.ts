import type { Handler } from 'aws-lambda';
import { SFNClient, GetExecutionHistoryCommand } from '@aws-sdk/client-sfn';

const sfnClient = new SFNClient({});

interface GetExecutionHistoryInput {
  executionArn: string;
  maxResults?: number;
  nextToken?: string;
}

export const handler: Handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  const input = event as GetExecutionHistoryInput;
  const { executionArn, maxResults, nextToken } = input;
  
  if (!executionArn) {
    throw new Error('executionArn is required');
  }
  
  try {
    const command = new GetExecutionHistoryCommand({
      executionArn,
      maxResults: maxResults || 50,
      nextToken,
      reverseOrder: true, // Most recent events first
    });
    
    const response = await sfnClient.send(command);
    
    return {
      events: response.events || [],
      nextToken: response.nextToken,
    };
  } catch (error) {
    console.error('Error getting execution history:', error);
    throw new Error(`Failed to get execution history: ${error instanceof Error ? error.message : String(error)}`);
  }
};