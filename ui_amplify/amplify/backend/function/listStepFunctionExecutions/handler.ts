// @ts-ignore - AWS SDK is provided by Lambda runtime
const { SFNClient, ListExecutionsCommand, ListStateMachinesCommand } = require('@aws-sdk/client-sfn');

declare const process: { env: { AWS_REGION?: string } };

const client = new SFNClient({ region: process.env.AWS_REGION });

interface Execution {
  executionArn: string;
  stateMachineArn: string;
  name: string;
  status: string;
  startDate: string;
  stopDate?: string;
  agentName?: string;
}

export const handler = async (event: any): Promise<any> => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  try {
    const { stateMachineArn, status, maxResults } = event.arguments || {};
    
    // If no specific state machine ARN is provided, list all agent state machines
    let stateMachineArns: string[] = [];
    
    if (stateMachineArn) {
      stateMachineArns = [stateMachineArn];
    } else {
      // List all state machines that are agents (by naming convention or tags)
      const listSMCommand = new ListStateMachinesCommand({});
      const listSMResponse = await client.send(listSMCommand);
      
      stateMachineArns = listSMResponse.stateMachines
        ?.map((sm: any) => sm.stateMachineArn)
        ?.filter((arn: any): arn is string => arn !== undefined) || [];
      
      console.log('Found state machines:', stateMachineArns.length);
    }
    
    // Collect executions from all state machines
    const allExecutions: Execution[] = [];
    
    for (const arn of stateMachineArns) {
      const command = new ListExecutionsCommand({
        stateMachineArn: arn,
        statusFilter: status,
        maxResults: maxResults || 50
      });
      
      const response = await client.send(command);
      
      // Extract agent name from state machine ARN
      // Example: arn:aws:states:us-west-2:123456789012:stateMachine:weather-agent-prod
      const arnParts = arn.split(':');
      const smName = arnParts[arnParts.length - 1];
      const agentName = smName.replace('-prod', '');
      
      const executions = (response.executions || []).map((exec: any) => ({
        executionArn: exec.executionArn || '',
        stateMachineArn: exec.stateMachineArn || arn,
        name: exec.name || '',
        status: exec.status || 'UNKNOWN',
        startDate: exec.startDate?.toISOString() || '',
        stopDate: exec.stopDate?.toISOString(),
        agentName
      }));
      
      allExecutions.push(...executions);
    }
    
    // Sort by start date (most recent first)
    allExecutions.sort((a, b) => 
      new Date(b.startDate).getTime() - new Date(a.startDate).getTime()
    );
    
    // Limit results if maxResults is specified
    const limitedExecutions = maxResults 
      ? allExecutions.slice(0, maxResults)
      : allExecutions;
    
    return {
      executions: limitedExecutions
    };
  } catch (error) {
    console.error('Error listing executions:', error);
    return {
      error: 'Failed to list executions',
      details: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};