import { DynamoDBClient, ScanCommand } from '@aws-sdk/client-dynamodb';

declare const process: {
  env: {
    AWS_REGION?: string;
    ENVIRONMENT?: string;
  };
};

const dynamoDB = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-west-2' });
const ENVIRONMENT = process.env.ENVIRONMENT || 'prod';

export const handler = async (event: any) => {
  console.log('List tool secrets request:', event);
  
  try {
    // Scan the ToolSecrets table
    const result = await dynamoDB.send(new ScanCommand({
      TableName: `ToolSecrets-${ENVIRONMENT}`
    }));
    
    // Transform DynamoDB items to clean JSON
    const tools = (result.Items || []).map(item => ({
      tool_name: item.tool_name?.S || '',
      secret_keys: item.secret_keys?.L?.map(k => k.S || '') || [],
      description: item.description?.S,
      registered_at: item.registered_at?.S,
      environment: item.environment?.S
    }));
    
    // Sort by tool name
    tools.sort((a, b) => a.tool_name.localeCompare(b.tool_name));
    
    return {
      success: true,
      tools,
      count: tools.length
    };
  } catch (error) {
    console.error('Error listing tool secrets:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to list tool secrets'
    };
  }
};