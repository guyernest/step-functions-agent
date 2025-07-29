import type { Handler } from 'aws-lambda';
import { SFNClient, DescribeExecutionCommand } from '@aws-sdk/client-sfn';

const sfnClient = new SFNClient({});

interface GetExecutionInput {
  executionArn: string;
}

export const handler: Handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  const input = event as GetExecutionInput;
  const { executionArn } = input;
  
  if (!executionArn) {
    throw new Error('executionArn is required');
  }
  
  try {
    const command = new DescribeExecutionCommand({
      executionArn,
    });
    
    const response = await sfnClient.send(command);
    
    // Parse input to extract agent information
    let agentName = 'unknown';
    try {
      const inputData = JSON.parse(response.input || '{}');
      agentName = inputData.agentName || inputData.agent_name || 'unknown';
    } catch (e) {
      // Try to extract from execution name if possible
      const nameParts = response.name?.split('-');
      agentName = nameParts?.[0] || 'unknown';
    }
    
    return {
      executionArn: response.executionArn,
      name: response.name,
      stateMachineArn: response.stateMachineArn,
      status: response.status,
      startDate: response.startDate?.toISOString(),
      stopDate: response.stopDate?.toISOString(),
      input: response.input ? JSON.parse(response.input) : null,
      output: response.output ? JSON.parse(response.output) : null,
      error: response.error,
      agentName, // Add this for UI convenience
    };
  } catch (error) {
    console.error('Error getting Step Function execution:', error);
    throw new Error(`Failed to get execution: ${error instanceof Error ? error.message : String(error)}`);
  }
};