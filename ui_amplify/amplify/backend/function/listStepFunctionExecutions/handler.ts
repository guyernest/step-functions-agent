import type { Handler } from 'aws-lambda';
import { SFNClient, ListExecutionsCommand, DescribeExecutionCommand } from '@aws-sdk/client-sfn';

const sfnClient = new SFNClient({});

interface ListExecutionsInput {
  stateMachineArn?: string;
  statusFilter?: string;
  maxResults?: number;
  nextToken?: string;
}

export const handler: Handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  const input = event as ListExecutionsInput;
  const { stateMachineArn, statusFilter, maxResults, nextToken } = input;
  
  try {
    // If no specific state machine is provided, we need to list all executions
    // For now, let's assume we have a way to get relevant state machines
    
    const command = new ListExecutionsCommand({
      stateMachineArn,
      statusFilter: statusFilter as any,
      maxResults: maxResults || 50,
      nextToken,
    });
    
    const response = await sfnClient.send(command);
    
    // Transform the executions to match our GraphQL schema
    const executions = await Promise.all((response.executions || []).map(async exec => {
      // Parse input to extract agent information
      let agentName = 'unknown';
      let input = null;
      let output = null;
      let error = null;
      
      // For the first few executions, get detailed information
      const isRecent = (response.executions || []).indexOf(exec) < 5;
      
      if (isRecent && exec.executionArn) {
        try {
          const detailCommand = new DescribeExecutionCommand({
            executionArn: exec.executionArn
          });
          const detail = await sfnClient.send(detailCommand);
          
          // Parse input to extract agent information
          if (detail.input) {
            try {
              const inputData = JSON.parse(detail.input);
              agentName = inputData.agentName || inputData.agent_name || 'unknown';
              input = inputData;
            } catch (e) {
              console.warn('Failed to parse execution input:', e);
            }
          }
          
          if (detail.output) {
            try {
              output = JSON.parse(detail.output);
            } catch (e) {
              console.warn('Failed to parse execution output:', e);
            }
          }
          
          error = detail.error || null;
        } catch (e) {
          console.warn('Failed to get execution details:', e);
        }
      }
      
      // Fallback: extract agent name from execution name
      if (agentName === 'unknown') {
        const nameParts = exec.name?.split('-');
        agentName = nameParts?.[0] || 'unknown';
      }
      
      return {
        executionArn: exec.executionArn,
        name: exec.name,
        stateMachineArn: exec.stateMachineArn,
        status: exec.status,
        startDate: exec.startDate?.toISOString(),
        stopDate: exec.stopDate?.toISOString(),
        input,
        output,
        error,
        agentName,
      };
    }));
    
    return executions;
  } catch (error) {
    console.error('Error listing Step Function executions:', error);
    throw new Error(`Failed to list executions: ${error instanceof Error ? error.message : String(error)}`);
  }
};