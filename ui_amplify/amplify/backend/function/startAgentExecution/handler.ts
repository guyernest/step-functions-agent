import { SFNClient, StartExecutionCommand, ListStateMachinesCommand } from '@aws-sdk/client-sfn';

declare const process: { env: { AWS_REGION?: string } };

const client = new SFNClient({ region: process.env.AWS_REGION });

export const handler = async (event: any): Promise<any> => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  try {
    const { agentName, input, executionName } = event.arguments || {};
    
    if (!agentName) {
      return {
        error: 'Agent name is required'
      };
    }

    // First, find the state machine ARN for this agent
    // State machines are tagged with application=ai-agents
    const listCommand = new ListStateMachinesCommand({});
    const listResponse = await client.send(listCommand);
    
    console.log('Found state machines:', listResponse.stateMachines?.length);
    
    // Find the state machine that matches the agent name
    const stateMachine = listResponse.stateMachines?.find(sm => 
      sm.name && (
        sm.name.toLowerCase() === agentName.toLowerCase() ||
        sm.name.toLowerCase() === `${agentName.toLowerCase()}-prod`
      )
    );
    
    if (!stateMachine) {
      return {
        error: 'Agent not found',
        details: `No state machine found for agent: ${agentName}`
      };
    }

    console.log('Found state machine:', stateMachine.stateMachineArn);

    // Prepare the input for the state machine
    const executionInput = typeof input === 'string' ? input : JSON.stringify({
      messages: [
        {
          role: "user",
          content: input || "What can you do?"
        }
      ]
    });

    // Start the execution
    const startCommand = new StartExecutionCommand({
      stateMachineArn: stateMachine.stateMachineArn,
      input: executionInput,
      name: executionName // Optional custom name
    });

    const response = await client.send(startCommand);
    console.log('Execution started:', response.executionArn);

    return {
      executionArn: response.executionArn,
      startDate: response.startDate?.toISOString()
    };
  } catch (error) {
    console.error('Error starting execution:', error);
    return {
      error: 'Failed to start execution',
      details: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};