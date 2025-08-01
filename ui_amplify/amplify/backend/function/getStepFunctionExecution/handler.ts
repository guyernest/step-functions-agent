import { SFNClient, DescribeExecutionCommand, GetExecutionHistoryCommand } from '@aws-sdk/client-sfn';

const client = new SFNClient({ region: process.env.AWS_REGION });

interface Message {
  role: string;
  content: any; // Can be string, object, or array
  timestamp?: string;
  type?: string;
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
    let currentToolCall: any = null;
    
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
        
        // Get Lambda function invocations (tool calls)
        if (event.type === 'LambdaFunctionScheduled' && event.lambdaFunctionScheduledEventDetails) {
          try {
            const input = JSON.parse(event.lambdaFunctionScheduledEventDetails.input || '{}');
            
            // Extract tool information
            let toolName = 'Unknown Tool';
            let toolInput = input;
            
            // Check for Claude-style tool use
            if (input.tool_use_id && input.name) {
              toolName = input.name;
              toolInput = input.input || {};
              currentToolCall = { id: input.tool_use_id, name: toolName };
            }
            // Check for function-style tool use
            else if (input.function && input.function.name) {
              toolName = input.function.name;
              toolInput = input.function.arguments || {};
              currentToolCall = { name: toolName };
            }
            // Check for direct tool name
            else if (input.tool_name) {
              toolName = input.tool_name;
              delete input.tool_name; // Remove from display
              currentToolCall = { name: toolName };
            }
            
            messages.push({
              role: 'tool',
              content: [{
                type: 'tool_use',
                name: toolName,
                input: toolInput,
                tool_use_id: currentToolCall.id
              }],
              timestamp: event.timestamp?.toISOString(),
              type: 'tool_call'
            });
          } catch (e) {
            console.error('Error parsing Lambda input:', e);
          }
        }
        
        // Get Lambda function results (tool results)
        if (event.type === 'LambdaFunctionSucceeded' && event.lambdaFunctionSucceededEventDetails?.output) {
          try {
            const output = JSON.parse(event.lambdaFunctionSucceededEventDetails.output);
            
            messages.push({
              role: 'tool',
              content: [{
                type: 'tool_result',
                content: output.body || output.Body || output.result || output,
                tool_use_id: currentToolCall?.id
              }],
              timestamp: event.timestamp?.toISOString(),
              type: 'tool_result'
            });
            
            currentToolCall = null;
          } catch (e) {
            console.error('Error parsing Lambda output:', e);
            // If parsing fails, still show the raw output
            messages.push({
              role: 'tool',
              content: [{
                type: 'tool_result',
                content: event.lambdaFunctionSucceededEventDetails.output
              }],
              timestamp: event.timestamp?.toISOString(),
              type: 'tool_result'
            });
          }
        }
        
        // Get Lambda function errors
        if (event.type === 'LambdaFunctionFailed' && event.lambdaFunctionFailedEventDetails) {
          messages.push({
            role: 'system',
            content: {
              error: event.lambdaFunctionFailedEventDetails.error || 'Tool execution failed',
              details: event.lambdaFunctionFailedEventDetails.cause
            },
            timestamp: event.timestamp?.toISOString(),
            type: 'error'
          });
          currentToolCall = null;
        }
        
        // Get task outputs which might contain agent responses
        if (event.type === 'TaskSucceeded' && event.taskSucceededEventDetails?.output) {
          try {
            const output = JSON.parse(event.taskSucceededEventDetails.output);
            
            // Check for message content
            if (output.messages && Array.isArray(output.messages)) {
              output.messages.forEach((msg: any) => {
                // Handle tool calls in messages
                if (msg.tool_calls && Array.isArray(msg.tool_calls)) {
                  messages.push({
                    role: msg.role || 'assistant',
                    content: msg.tool_calls,
                    timestamp: event.timestamp?.toISOString(),
                    type: 'tool_calls'
                  });
                } else if (msg.content) {
                  messages.push({
                    role: msg.role || 'assistant',
                    content: msg.content,
                    timestamp: event.timestamp?.toISOString()
                  });
                }
              });
            }
            // Check for direct response formats
            else if (output.response || output.message || output.content) {
              const content = output.response || output.message || output.content;
              messages.push({
                role: 'assistant',
                content: content,
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
            
            // Check if the output contains messages (this is the full conversation)
            if (executionOutput.messages && Array.isArray(executionOutput.messages)) {
              // Clear existing messages and use the ones from output
              messages.length = 0;
              
              executionOutput.messages.forEach((msg: any) => {
                messages.push({
                  role: msg.role,
                  content: msg.content,
                  timestamp: event.timestamp?.toISOString()
                });
              });
            }
          } catch (e) {
            console.error('Error parsing execution output:', e);
          }
        }
        
        // Handle execution failures
        if (event.type === 'ExecutionFailed') {
          messages.push({
            role: 'system',
            content: {
              error: event.executionFailedEventDetails?.error || 'Execution failed',
              details: event.executionFailedEventDetails?.cause
            },
            timestamp: event.timestamp?.toISOString(),
            type: 'error'
          });
        }
        
        // Handle Activity tasks (for human approval)
        if (event.type === 'ActivityScheduled' && event.activityScheduledEventDetails) {
          messages.push({
            role: 'system',
            content: `Waiting for human approval: ${event.activityScheduledEventDetails.input || 'No details'}`,
            timestamp: event.timestamp?.toISOString(),
            type: 'approval_request'
          });
        }
        
        if (event.type === 'ActivitySucceeded' && event.activitySucceededEventDetails?.output) {
          try {
            const output = JSON.parse(event.activitySucceededEventDetails.output);
            messages.push({
              role: 'system',
              content: `Approval granted: ${output.approved ? 'Yes' : 'No'}`,
              timestamp: event.timestamp?.toISOString(),
              type: 'approval_result'
            });
          } catch (e) {
            messages.push({
              role: 'system',
              content: 'Activity completed',
              timestamp: event.timestamp?.toISOString()
            });
          }
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