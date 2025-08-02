// @ts-ignore - AWS SDK is provided by Lambda runtime
const AWS = require('aws-sdk');

declare const process: { env: { AWS_REGION?: string } };

const dynamodb = new AWS.DynamoDB({ region: process.env.AWS_REGION });

export const handler = async (event: any): Promise<any> => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  console.log('Event arguments:', event.arguments);
  console.log('Event tableName:', event.arguments?.tableName);

  try {
    // Get table name from event arguments
    const tableName = event.arguments?.tableName;
    
    if (!tableName) {
      console.error('No table name provided');
      return {
        error: 'Table name is required',
        details: 'Please configure the tool registry table name in Settings'
      };
    }
    
    console.log('Using table name:', tableName);
    
    // Scan the DynamoDB table for all tools
    // The tool-registry table uses tool_name as the key, not agent_name
    const params = {
      TableName: tableName
    };

    const response = await dynamodb.scan(params).promise();
    console.log('DynamoDB response:', JSON.stringify(response, null, 2));

    // Transform the DynamoDB items to a cleaner format
    // tool-registry table structure: tool_name, description, input_schema, etc.
    const tools = (response.Items || []).map((item: any) => ({
      id: item.tool_name?.S || '',
      name: item.tool_name?.S || '',
      description: item.description?.S || '',
      version: item.version?.S || '1.0.0',
      type: 'tool',
      createdAt: item.created_at?.S || new Date().toISOString()
    }));

    return {
      tools: tools.sort((a: any, b: any) => a.name.localeCompare(b.name))
    };
  } catch (error) {
    console.error('Error listing tools:', error);
    return {
      error: 'Failed to list tools',
      details: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};