import { DynamoDBClient, PutItemCommand, GetItemCommand } from "@aws-sdk/client-dynamodb";

const client = new DynamoDBClient({});

interface RegisterMCPServerEvent {
  arguments: {
    endpoint: string;
    environment?: string;
  };
}

export const handler = async (event: RegisterMCPServerEvent) => {
  console.log("Register MCP Server request:", JSON.stringify(event, null, 2));

  const { endpoint, environment = process.env.ENV_NAME || 'prod' } = event.arguments;

  if (!endpoint) {
    throw new Error("MCP endpoint is required");
  }

  const tableName = process.env.MCP_REGISTRY_TABLE_NAME;
  if (!tableName) {
    throw new Error("MCP_REGISTRY_TABLE_NAME environment variable not set");
  }

  try {
    // Generate server data
    const serverId = `step-functions-agents-mcp-${environment}`;
    const version = "1.0.0";
    const now = new Date().toISOString();

    // Check if already registered
    const getCommand = new GetItemCommand({
      TableName: tableName,
      Key: {
        server_id: { S: serverId },
        version: { S: version }
      }
    });

    const existing = await client.send(getCommand);
    if (existing.Item) {
      console.log(`MCP server ${serverId} v${version} already registered, updating...`);
    }

    // Create registration data with DynamoDB attribute format
    const putCommand = new PutItemCommand({
      TableName: tableName,
      Item: {
        server_id: { S: serverId },
        version: { S: version },
        server_name: { S: `Step Functions Agents MCP Server (${environment})` },
        description: { S: "MCP server providing access to AWS Step Functions agents and execution management" },
        endpoint_url: { S: endpoint },
        protocol_type: { S: "jsonrpc" },
        authentication_type: { S: "api_key" },
        api_key_header: { S: "x-api-key" },
        available_tools: { S: JSON.stringify([
          {
            name: "start_agent",
            description: "Start execution of a Step Functions agent",
            inputSchema: {
              type: "object",
              properties: {
                agent_name: { type: "string", description: "Name of the agent to execute" },
                input: { type: "object", description: "Input parameters for the agent" }
              },
              required: ["agent_name", "input"]
            }
          },
          {
            name: "get_execution_status",
            description: "Get the status of an agent execution",
            inputSchema: {
              type: "object",
              properties: {
                execution_arn: { type: "string", description: "ARN of the execution" }
              },
              required: ["execution_arn"]
            }
          },
          {
            name: "list_available_agents",
            description: "List all available agents from the registry",
            inputSchema: {
              type: "object",
              properties: {}
            }
          }
        ])},
        status: { S: "active" },
        health_check_url: { S: endpoint.replace('/mcp', '/health') },
        configuration: { S: JSON.stringify({
          max_concurrent_executions: 10,
          timeout_seconds: 3600,
          retry_attempts: 3
        })},
        metadata: { S: JSON.stringify({
          managed_by: "amplify",
          environment: environment,
          deployment_method: "amplify",
          aws_region: process.env.AWS_REGION || "us-west-2",
          registered_at: now,
          tags: [environment, "mcp", "step-functions", "auto-registered"]
        })},
        created_at: { S: now },
        updated_at: { S: now },
        created_by: { S: "amplify-backend" }
      }
    });

    await client.send(putCommand);

    console.log(`✅ Successfully registered MCP server: ${serverId} v${version}`);

    return {
      success: true,
      serverId: serverId,
      version: version,
      endpoint: endpoint,
      message: `MCP server registered successfully`
    };

  } catch (error) {
    console.error("Error registering MCP server:", error);
    throw new Error(`Failed to register MCP server: ${error instanceof Error ? error.message : String(error)}`);
  }
};