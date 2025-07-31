import type { Handler } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, ScanCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({});
const ddbDocClient = DynamoDBDocumentClient.from(client);

export const handler: Handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  const tableName = process.env.AGENT_REGISTRY_TABLE_NAME;
  
  if (!tableName) {
    throw new Error('AGENT_REGISTRY_TABLE_NAME environment variable not set');
  }
  
  try {
    const command = new ScanCommand({
      TableName: tableName
    });
    
    const response = await ddbDocClient.send(command);
    
    // Transform the DynamoDB items to match our GraphQL schema
    const agents = (response.Items || []).map((item: any) => {
      // Parse tools JSON string
      let tools: string[] = [];
      try {
        const toolsData = JSON.parse(item.tools || '[]');
        tools = toolsData.map((tool: any) => tool.tool_name || tool.name || '');
      } catch (e) {
        console.warn('Failed to parse tools for agent:', item.agent_name, e);
      }
      
      // Parse parameters for capabilities
      let capabilities = {};
      try {
        capabilities = JSON.parse(item.parameters || '{}');
      } catch (e) {
        console.warn('Failed to parse parameters for agent:', item.agent_name, e);
      }
      
      return {
        id: `${item.agent_name}-${item.version}`,
        name: item.agent_name,
        version: item.version || 'v1.0',
        description: item.description || '',
        tools: tools,
        status: item.status || 'ACTIVE',
        capabilities: capabilities, // Keep as object
        maxIterations: (capabilities as any)?.max_iterations || 10
      };
    });
    
    return agents;
  } catch (error) {
    console.error('Error listing agents:', error);
    throw new Error(`Failed to list agents: ${error instanceof Error ? error.message : String(error)}`);
  }
};