#!/usr/bin/env node
/**
 * Automatic MCP Server Registration Script
 * 
 * This script reads the amplify_outputs.json file and automatically registers
 * the MCP server in the registry. It can be used as part of the deployment pipeline.
 */

const fs = require('fs');
const path = require('path');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');

// Configuration
const AMPLIFY_OUTPUTS_PATH = path.join(__dirname, '../amplify_outputs.json');
const TABLE_NAME = 'MCPServerRegistry-prod'; // This should be environment-aware in production

// Initialize DynamoDB client
const ddbClient = new DynamoDBClient({
  region: process.env.AWS_REGION || 'eu-west-1'
});
const docClient = DynamoDBDocumentClient.from(ddbClient);

/**
 * Read and parse amplify_outputs.json
 */
function readAmplifyOutputs() {
  try {
    if (!fs.existsSync(AMPLIFY_OUTPUTS_PATH)) {
      throw new Error(`amplify_outputs.json not found at ${AMPLIFY_OUTPUTS_PATH}`);
    }

    const content = fs.readFileSync(AMPLIFY_OUTPUTS_PATH, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    console.error('❌ Error reading amplify_outputs.json:', error.message);
    process.exit(1);
  }
}

/**
 * Extract MCP server information from amplify outputs
 */
function extractMCPServerInfo(amplifyOutputs) {
  const mcpEndpoint = amplifyOutputs.custom?.mcpServerEndpoint;
  const region = amplifyOutputs.data?.aws_region;
  const functionName = amplifyOutputs.custom?.functions?.mcpServer;
  const logGroup = amplifyOutputs.custom?.logGroups?.mcpServer;

  if (!mcpEndpoint) {
    throw new Error('MCP server endpoint not found in amplify_outputs.json');
  }

  if (!region) {
    throw new Error('AWS region not found in amplify_outputs.json');
  }

  return {
    endpoint: mcpEndpoint,
    region,
    functionName: functionName || 'Unknown',
    logGroup: logGroup || 'Unknown',
    environment: process.env.NODE_ENV || 'development'
  };
}

/**
 * Generate server ID based on environment
 */
function generateServerId(environment) {
  return `step-functions-agents-mcp-${environment}`;
}

/**
 * Create MCP server registration data
 */
function createServerRegistrationData(mcpInfo) {
  const serverId = generateServerId(mcpInfo.environment);
  const timestamp = new Date().toISOString();

  return {
    server_id: serverId,
    version: '1.0.0',
    server_name: `Step Functions Agents MCP Server (${mcpInfo.environment})`,
    description: `MCP server providing access to AWS Step Functions agents for AI-powered task execution and automation in ${mcpInfo.environment} environment`,
    endpoint_url: mcpInfo.endpoint,
    protocol_type: 'jsonrpc',
    authentication_type: 'api_key',
    api_key_header: 'x-api-key',
    available_tools: JSON.stringify([
      {
        name: 'start_agent',
        description: 'Start execution of a Step Functions agent',
        inputSchema: {
          type: 'object',
          properties: {
            agent_name: {
              type: 'string',
              description: 'Name of the agent to execute'
            },
            input_message: {
              type: 'string',
              description: 'Input message for the agent'
            },
            execution_name: {
              type: 'string',
              description: 'Optional execution name'
            }
          },
          required: ['agent_name', 'input_message']
        }
      },
      {
        name: 'get_execution_status',
        description: 'Get status of an agent execution',
        inputSchema: {
          type: 'object',
          properties: {
            execution_arn: {
              type: 'string',
              description: 'ARN of the execution to check'
            }
          },
          required: ['execution_arn']
        }
      },
      {
        name: 'list_available_agents',
        description: 'List all available agents from the registry',
        inputSchema: {
          type: 'object',
          properties: {}
        }
      }
    ]),
    status: 'active',
    health_check_url: mcpInfo.endpoint.replace('/mcp', '/health'),
    health_check_interval: 300,
    configuration: JSON.stringify({
      timeout_seconds: 30,
      max_retries: 3,
      supports_batch: false,
      protocol_version: '2024-11-05',
      lambda_function: mcpInfo.functionName
    }),
    metadata: JSON.stringify({
      managed_by: 'amplify',
      team: 'platform',
      environment: mcpInfo.environment,
      cost_center: 'engineering',
      tags: [mcpInfo.environment, 'mcp', 'step-functions', 'auto-registered'],
      implementation: 'rust',
      aws_region: mcpInfo.region,
      deployment_method: 'amplify',
      registered_by: 'deployment-script',
      registration_timestamp: timestamp
    }),
    deployment_stack: `amplify-${mcpInfo.environment}`,
    deployment_region: mcpInfo.region,
    created_at: timestamp,
    updated_at: timestamp,
    created_by: 'amplify-deployment'
  };
}

/**
 * Check if server is already registered
 */
async function isServerRegistered(serverId, version) {
  try {
    const command = new GetCommand({
      TableName: TABLE_NAME,
      Key: {
        server_id: serverId,
        version: version
      }
    });

    const result = await docClient.send(command);
    return !!result.Item;
  } catch (error) {
    console.error('Error checking server registration:', error);
    return false;
  }
}

/**
 * Register MCP server in DynamoDB
 */
async function registerMCPServer(serverData) {
  try {
    const command = new PutCommand({
      TableName: TABLE_NAME,
      Item: serverData
    });

    await docClient.send(command);
    return true;
  } catch (error) {
    console.error('Error registering MCP server:', error);
    return false;
  }
}

/**
 * Main registration function
 */
async function main() {
  console.log('🚀 Starting MCP Server Auto-Registration...');
  console.log('');

  try {
    // Read amplify outputs
    console.log('📖 Reading amplify_outputs.json...');
    const amplifyOutputs = readAmplifyOutputs();

    // Extract MCP server info
    console.log('🔍 Extracting MCP server information...');
    const mcpInfo = extractMCPServerInfo(amplifyOutputs);

    console.log('📋 MCP Server Details:');
    console.log(`   Environment: ${mcpInfo.environment}`);
    console.log(`   Endpoint: ${mcpInfo.endpoint}`);
    console.log(`   Region: ${mcpInfo.region}`);
    console.log(`   Function: ${mcpInfo.functionName}`);
    console.log('');

    // Generate registration data
    const serverData = createServerRegistrationData(mcpInfo);
    const serverId = serverData.server_id;
    const version = serverData.version;

    // Check if already registered
    console.log('🔎 Checking if server is already registered...');
    const alreadyRegistered = await isServerRegistered(serverId, version);

    if (alreadyRegistered) {
      console.log('ℹ️  Server is already registered. Updating...');
    } else {
      console.log('✨ Registering new MCP server...');
    }

    // Register/update the server
    const success = await registerMCPServer(serverData);

    if (success) {
      console.log('✅ MCP Server registration completed successfully!');
      console.log(`   Server ID: ${serverId}`);
      console.log(`   Version: ${version}`);
      console.log(`   Status: ${serverData.status}`);
      console.log(`   Tools: ${JSON.parse(serverData.available_tools).length} available`);
    } else {
      console.warn('⚠️  Failed to register MCP server in registry');
      console.warn('   This is expected if the build role lacks DynamoDB permissions.');
      console.warn('   The MCP server will still be deployed and functional.');
      console.warn('   You can manually register it from the UI later.');
      // Don't fail the build - registration is optional
    }

  } catch (error) {
    console.warn('⚠️  Registration encountered an error:', error.message);
    console.warn('   This is expected if the build role lacks permissions.');
    console.warn('   The MCP server will still be deployed and functional.');
    // Don't fail the build - registration is optional
  }
}

// Run the script if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Unexpected error:', error);
    process.exit(1);
  });
}

module.exports = {
  readAmplifyOutputs,
  extractMCPServerInfo,
  createServerRegistrationData,
  registerMCPServer
};