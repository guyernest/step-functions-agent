import { AppSyncResolverHandler } from 'aws-lambda';
import { SFNClient, ListExecutionsCommand, DescribeExecutionCommand, ExecutionStatus } from '@aws-sdk/client-sfn';

const sfnClient = new SFNClient({ region: process.env.AWS_REGION });

type ListExecutionsArguments = {
  stateMachineArn?: string;
  statusFilter?: string;
  maxResults?: number;
};

interface Execution {
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
  // Format: arn:aws:states:region:account:stateMachine:AgentName-suffix
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

  // Otherwise return the execution name as is
  return executionName;
};

export const handler: AppSyncResolverHandler<ListExecutionsArguments, Execution[]> = async (event) => {
  try {
    const { stateMachineArn, statusFilter, maxResults = 50 } = event.arguments;

    // Build the list executions command
    const listCommand = new ListExecutionsCommand({
      ...(stateMachineArn && { stateMachineArn }),
      ...(statusFilter && statusFilter !== 'all' && { statusFilter: statusFilter as ExecutionStatus }),
      maxResults
    });

    const response = await sfnClient.send(listCommand);
    
    // Enhance executions with agent names and parsed data
    const executions: Execution[] = await Promise.all(
      (response.executions || []).map(async (exec) => {
        let input, output, error, agentName;
        
        try {
          // Get detailed execution info to access input/output
          const describeCommand = new DescribeExecutionCommand({
            executionArn: exec.executionArn
          });
          const details = await sfnClient.send(describeCommand);
          
          // Parse input
          if (details.input) {
            try {
              input = JSON.parse(details.input);
              // Try to get agent name from input
              agentName = input.agent_name || extractAgentName(exec.name!, exec.stateMachineArn!, input);
            } catch {
              input = details.input;
              agentName = extractAgentName(exec.name!, exec.stateMachineArn!);
            }
          } else {
            agentName = extractAgentName(exec.name!, exec.stateMachineArn!);
          }

          // Parse output
          if (details.output) {
            try {
              output = JSON.parse(details.output);
            } catch {
              output = details.output;
            }
          }

          // Extract error if failed
          if (details.status === 'FAILED' && details.error) {
            error = details.error;
          }
        } catch (e) {
          console.error('Failed to get execution details:', e);
          // Fall back to basic agent name extraction
          agentName = extractAgentName(exec.name!, exec.stateMachineArn!);
        }

        return {
          executionArn: exec.executionArn!,
          name: exec.name!,
          stateMachineArn: exec.stateMachineArn!,
          status: exec.status!,
          startDate: exec.startDate!.toISOString(),
          stopDate: exec.stopDate?.toISOString(),
          input,
          output,
          error,
          agentName
        };
      })
    );

    return executions;
  } catch (error) {
    console.error('Error listing executions:', error);
    throw error;
  }
};