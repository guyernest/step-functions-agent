import { AppSyncResolverHandler } from 'aws-lambda';
import { SFNClient, DescribeExecutionCommand } from '@aws-sdk/client-sfn';

const sfnClient = new SFNClient({ region: process.env.AWS_REGION });

type GetExecutionArguments = {
  executionArn: string;
};

interface ExecutionDetail {
  executionArn: string;
  name: string;
  stateMachineArn: string;
  status: string;
  startDate: string;
  stopDate?: string;
  input?: any;
  output?: any;
  error?: string;
  agentName?: string;
}

const extractAgentName = (executionName: string, stateMachineArn: string, input?: any): string => {
  // First try to extract from input if available
  if (input) {
    try {
      const parsedInput = typeof input === 'string' ? JSON.parse(input) : input;
      if (parsedInput.agent_name) {
        return parsedInput.agent_name;
      }
    } catch (e) {
      // Ignore parse errors
    }
  }

  // UUID pattern: "agent-name-uuid" (e.g., "sql-agent-1207b42a-e88c-4aa6-ac84-9dcba474007b")
  const uuidPattern = /^(.+)-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
  const uuidMatch = executionName.match(uuidPattern);
  if (uuidMatch) {
    return uuidMatch[1];
  }

  // Timestamp pattern: "agent-name-timestamp" (e.g., "sql-agent-1234567890")
  const timestampPattern = /^(.+)-(\d{10,13})$/;
  const timestampMatch = executionName.match(timestampPattern);
  if (timestampMatch) {
    return timestampMatch[1];
  }

  // Try to extract from state machine ARN
  if (stateMachineArn) {
    const arnParts = stateMachineArn.split(':');
    if (arnParts.length >= 6) {
      const stateMachineName = arnParts[arnParts.length - 1];
      // Remove common suffixes
      const cleanName = stateMachineName
        .replace(/-prod$/i, '')
        .replace(/-dev$/i, '')
        .replace(/-staging$/i, '')
        .replace(/Agent$/i, '')
        .replace(/StateMachine$/i, '');
      
      if (cleanName && cleanName !== stateMachineName) {
        return cleanName;
      }
    }
  }

  // If the name is just a UUID, return "Unknown"
  const pureUuidPattern = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
  if (pureUuidPattern.test(executionName)) {
    return 'Unknown';
  }

  return executionName;
};

export const handler: AppSyncResolverHandler<GetExecutionArguments, ExecutionDetail> = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  try {
    const { executionArn } = event.arguments;

    if (!executionArn) {
      console.error('No executionArn found in event:', event);
      throw new Error('executionArn is required');
    }

    const describeCommand = new DescribeExecutionCommand({
      executionArn
    });

    const executionDetails = await sfnClient.send(describeCommand);

    let input, output, agentName;

    // Parse input
    if (executionDetails.input) {
      try {
        input = JSON.parse(executionDetails.input);
        agentName = input.agent_name || extractAgentName(
          executionDetails.name!, 
          executionDetails.stateMachineArn!,
          input
        );
      } catch {
        input = executionDetails.input;
        agentName = extractAgentName(
          executionDetails.name!,
          executionDetails.stateMachineArn!
        );
      }
    } else {
      agentName = extractAgentName(
        executionDetails.name!,
        executionDetails.stateMachineArn!
      );
    }

    // Parse output
    if (executionDetails.output) {
      try {
        output = JSON.parse(executionDetails.output);
      } catch {
        output = executionDetails.output;
      }
    }

    const result: ExecutionDetail = {
      executionArn: executionDetails.executionArn!,
      name: executionDetails.name!,
      stateMachineArn: executionDetails.stateMachineArn!,
      status: executionDetails.status!,
      startDate: executionDetails.startDate!.toISOString(),
      stopDate: executionDetails.stopDate?.toISOString(),
      input,
      output,
      error: executionDetails.error,
      agentName
    };

    return result;
  } catch (error) {
    console.error('Error fetching execution detail:', error);
    throw error;
  }
};