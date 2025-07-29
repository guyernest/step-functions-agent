import type { Handler } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, ScanCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({});
const ddbDocClient = DynamoDBDocumentClient.from(client);

export const handler: Handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  const tableName = process.env.TOOL_REGISTRY_TABLE_NAME;
  
  if (!tableName) {
    throw new Error('TOOL_REGISTRY_TABLE_NAME environment variable not set');
  }
  
  try {
    const command = new ScanCommand({
      TableName: tableName
    });
    
    const response = await ddbDocClient.send(command);
    
    // Transform the DynamoDB items to match our GraphQL schema
    const tools = (response.Items || []).map((item: any) => {
      // Parse input schema JSON string
      let inputSchema = {};
      try {
        inputSchema = JSON.parse(item.input_schema || '{}');
      } catch (e) {
        console.warn('Failed to parse input_schema for tool:', item.tool_name, e);
      }
      
      return {
        id: `${item.tool_name}-${item.version || 'latest'}`,
        name: item.tool_name,
        version: item.version || 'latest',
        description: item.description || '',
        inputSchema: inputSchema,
        outputSchema: {}, // Not stored in the current schema
        status: item.status || 'ACTIVE'
      };
    });
    
    return tools;
  } catch (error) {
    console.error('Error listing tools:', error);
    throw new Error(`Failed to list tools: ${error instanceof Error ? error.message : String(error)}`);
  }
};