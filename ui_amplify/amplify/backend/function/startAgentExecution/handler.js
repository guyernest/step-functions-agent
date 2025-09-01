import { SFNClient, StartExecutionCommand, ListStateMachinesCommand, ListTagsForResourceCommand } from '@aws-sdk/client-sfn';
const client = new SFNClient({ region: process.env.AWS_REGION });
export const handler = async (event) => {
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
        // Find the state machine that matches the agent name by checking tags
        let stateMachine = null;
        for (const sm of listResponse.stateMachines || []) {
            if (!sm.stateMachineArn)
                continue;
            try {
                // Get tags for this state machine
                const tagsCommand = new ListTagsForResourceCommand({
                    resourceArn: sm.stateMachineArn
                });
                const tagsResponse = await client.send(tagsCommand);
                const tags = tagsResponse.tags || [];
                // Check if this state machine has the required tags and matches the agent name
                const hasAgentTag = tags.some(tag => tag.key === 'Type' && tag.value === 'Agent');
                const hasApplicationTag = tags.some(tag => tag.key === 'Application' && tag.value === 'StepFunctionsAgent');
                const agentNameTag = tags.find(tag => tag.key === 'AgentName');
                if (hasAgentTag && hasApplicationTag && agentNameTag?.value &&
                    agentNameTag.value.toLowerCase() === agentName.toLowerCase()) {
                    stateMachine = sm;
                    break;
                }
            }
            catch (error) {
                console.log('Error getting tags for state machine:', sm.stateMachineArn, error);
            }
        }
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
    }
    catch (error) {
        console.error('Error starting execution:', error);
        return {
            error: 'Failed to start execution',
            details: error instanceof Error ? error.message : 'Unknown error'
        };
    }
};
