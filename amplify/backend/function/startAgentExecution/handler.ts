import { SFNClient, StartExecutionCommand } from '@aws-sdk/client-sfn';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand } from '@aws-sdk/lib-dynamodb';

const sfnClient = new SFNClient({});
const ddbClient = new DynamoDBClient({});
const ddbDocClient = DynamoDBDocumentClient.from(ddbClient);

export const handler = async (event: any) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  const { agentName, input } = event.arguments || {};
  
  if (!agentName) {
    throw new Error('Agent name is required');
  }
  
  const tableName = process.env.AGENT_REGISTRY_TABLE_NAME || 'AgentRegistry-prod';
  
  try {
    // Get agent details from DynamoDB
    const getCommand = new GetCommand({
      TableName: tableName,
      Key: {
        agent_name: agentName,
        version: 'v1.0' // Default version
      }
    });
    
    const agentResponse = await ddbDocClient.send(getCommand);
    
    if (!agentResponse.Item) {
      throw new Error(`Agent ${agentName} not found`);
    }
    
    const agent = agentResponse.Item;
    
    if (!agent.state_machine_arn) {
      throw new Error(`Agent ${agentName} does not have a state machine ARN`);
    }
    
    // Prepare execution input
    const executionInput = {
      agentName: agent.agent_name,
      version: agent.version,
      userInput: input || {},
      parameters: JSON.parse(agent.parameters || '{}'),
      tools: JSON.parse(agent.tools || '[]')
    };
    
    // Start Step Functions execution
    const executionName = `${agentName}-${Date.now()}`;
    const startCommand = new StartExecutionCommand({
      stateMachineArn: agent.state_machine_arn,
      name: executionName,
      input: JSON.stringify(executionInput)
    });
    
    const executionResponse = await sfnClient.send(startCommand);
    
    return {
      executionArn: executionResponse.executionArn,
      executionName: executionName,
      startDate: executionResponse.startDate?.toISOString() || new Date().toISOString(),
      status: 'RUNNING',
      agentName: agent.agent_name,
      agentVersion: agent.version
    };
    
  } catch (error) {
    console.error('Error starting agent execution:', error);
    throw error;
  }
};