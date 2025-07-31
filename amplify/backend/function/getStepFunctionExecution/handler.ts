import { SFNClient, DescribeExecutionCommand, GetExecutionHistoryCommand } from '@aws-sdk/client-sfn';

const sfnClient = new SFNClient({});

export const handler = async (event: any) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  const { executionArn } = event.arguments || {};
  
  if (!executionArn) {
    throw new Error('Execution ARN is required');
  }
  
  try {
    // Get execution details
    const describeCommand = new DescribeExecutionCommand({
      executionArn: executionArn
    });
    
    const executionDetails = await sfnClient.send(describeCommand);
    
    // Extract agent name from execution input if available
    let agentName: string | undefined;
    if (executionDetails.input) {
      try {
        const input = JSON.parse(executionDetails.input);
        agentName = input.agentName;
      } catch (e) {
        console.log('Could not parse execution input');
      }
    }
    
    // Parse output if it's a JSON string
    let parsedOutput: any;
    if (executionDetails.output) {
      try {
        parsedOutput = JSON.parse(executionDetails.output);
      } catch (e) {
        parsedOutput = executionDetails.output;
      }
    }
    
    return {
      executionArn: executionDetails.executionArn,
      name: executionDetails.name,
      stateMachineArn: executionDetails.stateMachineArn,
      status: executionDetails.status,
      startDate: executionDetails.startDate?.toISOString(),
      stopDate: executionDetails.stopDate?.toISOString(),
      input: executionDetails.input ? JSON.parse(executionDetails.input) : null,
      output: parsedOutput,
      error: executionDetails.error,
      cause: executionDetails.cause,
      agentName: agentName
    };
    
  } catch (error) {
    console.error('Error getting execution details:', error);
    throw error;
  }
};