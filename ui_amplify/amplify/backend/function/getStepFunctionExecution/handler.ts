import { SFNClient, DescribeExecutionCommand, GetExecutionHistoryCommand } from '@aws-sdk/client-sfn';

const client = new SFNClient({ region: process.env.AWS_REGION });

interface Message {
  role: string;
  content: string;
  timestamp?: string;
}

export const handler = async (event: any): Promise<any> => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  try {
    const { executionArn } = event.arguments || {};
    
    if (!executionArn) {
      return {
        error: 'Execution ARN is required'
      };
    }

    // Get execution details
    const describeCommand = new DescribeExecutionCommand({
      executionArn
    });
    
    const describeResponse = await client.send(describeCommand);
    
    // Get execution history to extract messages
    const historyCommand = new GetExecutionHistoryCommand({
      executionArn,
      maxResults: 1000,
      reverseOrder: false
    });
    
    const historyResponse = await client.send(historyCommand);
    
    // Extract messages from the execution history
    const messages: Message[] = [];
    let executionInput: any = {};
    let executionOutput: any = {};
    
    if (historyResponse.events) {
      for (const event of historyResponse.events) {
        // Get initial input
        if (event.type === 'ExecutionStarted' && event.executionStartedEventDetails?.input) {
          try {
            executionInput = JSON.parse(event.executionStartedEventDetails.input);
            // Extract initial messages if they exist
            if (executionInput.messages && Array.isArray(executionInput.messages)) {
              executionInput.messages.forEach((msg: any) => {
                messages.push({
                  role: msg.role || 'user',
                  content: msg.content || '',
                  timestamp: event.timestamp?.toISOString()
                });
              });
            }
          } catch (e) {
            console.error('Error parsing execution input:', e);
          }
        }
        
        // Get task outputs which might contain agent responses
        if (event.type === 'TaskSucceeded' && event.taskSucceededEventDetails?.output) {
          try {
            const output = JSON.parse(event.taskSucceededEventDetails.output);
            
            // Check for response in various formats
            if (output.response) {
              messages.push({
                role: 'assistant',
                content: output.response,
                timestamp: event.timestamp?.toISOString()
              });
            } else if (output.message) {
              messages.push({
                role: 'assistant',
                content: output.message,
                timestamp: event.timestamp?.toISOString()
              });
            } else if (output.Body?.response) {
              messages.push({
                role: 'assistant',
                content: output.Body.response,
                timestamp: event.timestamp?.toISOString()
              });
            }
          } catch (e) {
            console.error('Error parsing task output:', e);
          }
        }
        
        // Get final output
        if (event.type === 'ExecutionSucceeded' && event.executionSucceededEventDetails?.output) {
          try {
            executionOutput = JSON.parse(event.executionSucceededEventDetails.output);
          } catch (e) {
            console.error('Error parsing execution output:', e);
          }
        }
        
        // Handle execution failures
        if (event.type === 'ExecutionFailed') {
          messages.push({
            role: 'system',
            content: `Execution failed: ${event.executionFailedEventDetails?.error} - ${event.executionFailedEventDetails?.cause}`,
            timestamp: event.timestamp?.toISOString()
          });
        }
      }
    }
    
    // Extract agent name from state machine ARN
    let agentName = 'Unknown';
    if (describeResponse.stateMachineArn) {
      const arnParts = describeResponse.stateMachineArn.split(':');
      const smName = arnParts[arnParts.length - 1];
      agentName = smName.replace('-prod', '');
    }
    
    return {
      execution: {
        executionArn: describeResponse.executionArn,
        stateMachineArn: describeResponse.stateMachineArn,
        name: describeResponse.name,
        status: describeResponse.status,
        startDate: describeResponse.startDate?.toISOString(),
        stopDate: describeResponse.stopDate?.toISOString(),
        input: executionInput,
        output: executionOutput,
        agentName
      },
      messages,
      eventCount: historyResponse.events?.length || 0
    };
  } catch (error) {
    console.error('Error getting execution details:', error);
    return {
      error: 'Failed to get execution details',
      details: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};