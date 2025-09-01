import { SFNClient, DescribeStateMachineCommand, ListStateMachinesCommand, ListTagsForResourceCommand } from '@aws-sdk/client-sfn';
const client = new SFNClient({ region: process.env.AWS_REGION });
export const handler = async (event) => {
    console.log('Received event:', JSON.stringify(event, null, 2));
    try {
        const { agentName } = event.arguments || {};
        if (!agentName) {
            return {
                success: false,
                error: 'Agent name is required'
            };
        }
        // List all state machines and find the one for this agent
        const listCommand = new ListStateMachinesCommand({});
        const listResponse = await client.send(listCommand);
        let stateMachine = null;
        let stateMachineArn = null;
        // Search for state machine by tags
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
                // Check if this state machine matches the agent name
                const hasAgentTag = tags.some(tag => tag.key === 'Type' && tag.value === 'Agent');
                const hasApplicationTag = tags.some(tag => tag.key === 'Application' && tag.value === 'StepFunctionsAgent');
                const agentNameTag = tags.find(tag => tag.key === 'AgentName');
                if (hasAgentTag && hasApplicationTag && agentNameTag?.value &&
                    agentNameTag.value.toLowerCase() === agentName.toLowerCase()) {
                    stateMachine = sm;
                    stateMachineArn = sm.stateMachineArn;
                    break;
                }
            }
            catch (error) {
                console.log('Error getting tags for state machine:', sm.stateMachineArn, error);
            }
        }
        if (!stateMachine || !stateMachineArn) {
            return {
                success: false,
                error: `No state machine found for agent: ${agentName}`,
                searchedCount: listResponse.stateMachines?.length || 0
            };
        }
        // Get detailed information about the state machine
        const describeCommand = new DescribeStateMachineCommand({
            stateMachineArn: stateMachineArn
        });
        const describeResponse = await client.send(describeCommand);
        // Build console URL for the state machine
        const region = process.env.AWS_REGION || 'us-west-2';
        const accountId = stateMachineArn.split(':')[4];
        const stateMachineName = stateMachineArn.split(':').pop();
        const consoleUrl = `https://console.aws.amazon.com/states/home?region=${region}#/statemachines/view/${stateMachineArn}`;
        const executionsUrl = `https://console.aws.amazon.com/states/home?region=${region}#/statemachines/view/${stateMachineArn}/executions`;
        // Parse the ASL definition for visualization
        let asl = null;
        try {
            if (describeResponse.definition) {
                asl = JSON.parse(describeResponse.definition);
            }
        }
        catch (error) {
            console.error('Error parsing state machine definition:', error);
            // Keep the raw definition if parsing fails
            asl = describeResponse.definition;
        }
        return {
            success: true,
            stateMachine: {
                arn: describeResponse.stateMachineArn,
                name: describeResponse.name,
                status: describeResponse.status,
                type: describeResponse.type,
                creationDate: describeResponse.creationDate?.toISOString(),
                roleArn: describeResponse.roleArn,
                loggingConfiguration: describeResponse.loggingConfiguration,
                tracingConfiguration: describeResponse.tracingConfiguration,
                definition: describeResponse.definition, // Raw JSON string
                asl: asl // Parsed ASL for visualization
            },
            urls: {
                console: consoleUrl,
                executions: executionsUrl
            },
            metadata: {
                region,
                accountId,
                stateMachineName
            }
        };
    }
    catch (error) {
        console.error('Error getting state machine info:', error);
        return {
            success: false,
            error: error.message || 'Failed to get state machine information',
            details: error
        };
    }
};
