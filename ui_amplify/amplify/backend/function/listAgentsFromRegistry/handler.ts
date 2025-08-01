// @ts-ignore - AWS SDK is provided by Lambda runtime
const { DynamoDBClient, ScanCommand } = require('@aws-sdk/client-dynamodb');

declare const process: { env: { AWS_REGION?: string } };

const client = new DynamoDBClient({ region: process.env.AWS_REGION });

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
        details: 'Please configure the agent registry table name in Settings'
      };
    }
    
    console.log('Using table name:', tableName);
    
    // Scan the DynamoDB table for all agents
    // First, let's scan without filter to see what's in the table
    const command = new ScanCommand({
      TableName: tableName
    });

    const response = await client.send(command);
    console.log('DynamoDB response:', JSON.stringify(response, null, 2));

    // Log the first item to see the structure
    if (response.Items && response.Items.length > 0) {
      console.log('First item structure:', JSON.stringify(response.Items[0], null, 2));
    }

    // Transform the DynamoDB items to a cleaner format
    // The agents might be stored in the same table as tools, so check for both patterns
    const agents = (response.Items || [])
      .filter((item: any) => {
        // Check if this is an agent (might have type field or be determined by name pattern)
        const itemType = item.type?.S;
        const hasAgentName = item.agent_name?.S;
        const isNotTool = !item.tool_name?.S;
        
        console.log('Item check:', { 
          itemType, 
          hasAgentName, 
          isNotTool,
          keys: Object.keys(item) 
        });
        
        return itemType === 'AGENT' || itemType === 'agent' || (hasAgentName && isNotTool);
      })
      .map((item: any) => {
        // Parse tools if they exist
        let tools: string[] = [];
        if (item.tools?.S) {
          try {
            const toolsData = JSON.parse(item.tools.S);
            tools = toolsData.map((tool: any) => tool.tool_name || tool.name || '');
          } catch (e) {
            console.error('Error parsing tools:', e);
          }
        }
        
        return {
          id: item.agent_name?.S || item.name?.S || '',
          name: item.agent_name?.S || item.name?.S || '',
          description: item.description?.S || '',
          version: item.version?.S || '1.0.0',
          type: 'agent',
          createdAt: item.created_at?.S || item.createdAt?.S || new Date().toISOString(),
          tools: tools
        };
      });

    return {
      agents: agents.sort((a: any, b: any) => a.name.localeCompare(b.name))
    };
  } catch (error) {
    console.error('Error listing agents:', error);
    return {
      error: 'Failed to list agents',
      details: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};