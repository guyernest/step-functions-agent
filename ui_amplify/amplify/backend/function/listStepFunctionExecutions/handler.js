import { SFNClient, ListExecutionsCommand, ListStateMachinesCommand, ListTagsForResourceCommand } from '@aws-sdk/client-sfn';
const client = new SFNClient({ region: process.env.AWS_REGION });
export const handler = async (event) => {
    console.log('Received event:', JSON.stringify(event, null, 2));
    try {
        const { stateMachineArn, status, maxResults } = event.arguments || {};
        // If no specific state machine ARN is provided, list all agent state machines
        let stateMachineArns = [];
        if (stateMachineArn) {
            stateMachineArns = [stateMachineArn];
        }
        else {
            // List all state machines
            const listSMCommand = new ListStateMachinesCommand({});
            const listSMResponse = await client.send(listSMCommand);
            // Filter state machines by checking tags
            const filteredStateMachines = [];
            for (const sm of listSMResponse.stateMachines || []) {
                if (!sm.stateMachineArn)
                    continue;
                try {
                    // Get tags for this state machine
                    const tagsCommand = new ListTagsForResourceCommand({
                        resourceArn: sm.stateMachineArn
                    });
                    const tagsResponse = await client.send(tagsCommand);
                    const tags = tagsResponse.tags || [];
                    // Check if this state machine has the required tags
                    const hasAgentTag = tags.some(tag => tag.key === 'Type' && tag.value === 'Agent');
                    const hasApplicationTag = tags.some(tag => tag.key === 'Application' && tag.value === 'StepFunctionsAgent');
                    if (hasAgentTag && hasApplicationTag) {
                        filteredStateMachines.push(sm.stateMachineArn);
                    }
                }
                catch (error) {
                    console.log('Error getting tags for state machine:', sm.stateMachineArn, error);
                }
            }
            stateMachineArns = filteredStateMachines;
            console.log('Found state machines:', stateMachineArns.length);
        }
        // Collect executions from all state machines
        const allExecutions = [];
        for (const arn of stateMachineArns) {
            const command = new ListExecutionsCommand({
                stateMachineArn: arn,
                statusFilter: status,
                maxResults: maxResults || 50
            });
            const response = await client.send(command);
            // Get agent name from tags
            let agentName = 'unknown';
            try {
                const tagsCommand = new ListTagsForResourceCommand({
                    resourceArn: arn
                });
                const tagsResponse = await client.send(tagsCommand);
                const agentNameTag = tagsResponse.tags?.find(tag => tag.key === 'AgentName');
                if (agentNameTag?.value) {
                    agentName = agentNameTag.value;
                }
            }
            catch (error) {
                console.log('Error getting agent name from tags:', error);
                // Fallback to extracting from ARN
                const arnParts = arn.split(':');
                const smName = arnParts[arnParts.length - 1];
                agentName = smName;
            }
            const executions = (response.executions || []).map((exec) => ({
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
        allExecutions.sort((a, b) => new Date(b.startDate).getTime() - new Date(a.startDate).getTime());
        // Limit results if maxResults is specified
        const limitedExecutions = maxResults
            ? allExecutions.slice(0, maxResults)
            : allExecutions;
        return {
            executions: limitedExecutions
        };
    }
    catch (error) {
        console.error('Error listing executions:', error);
        return {
            error: 'Failed to list executions',
            details: error instanceof Error ? error.message : 'Unknown error'
        };
    }
};
