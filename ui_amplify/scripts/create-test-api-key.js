#!/usr/bin/env node

const { DynamoDBClient, PutItemCommand } = require('@aws-sdk/client-dynamodb');
const crypto = require('crypto');

// Configuration
const TABLE_NAME = 'step-functions-agents-prod-api-keys';
const REGION = 'eu-west-1'; // Update this to match your deployment region

// Generate a random API key
function generateApiKey() {
  return 'mcp_' + crypto.randomBytes(32).toString('hex');
}

// Hash the API key
function hashApiKey(apiKey) {
  return crypto.createHash('sha256').update(apiKey).digest('hex');
}

async function createApiKey() {
  const client = new DynamoDBClient({ region: REGION });
  
  const apiKey = generateApiKey();
  const apiKeyHash = hashApiKey(apiKey);
  const clientId = 'test-client-' + Date.now();
  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + 30); // Expires in 30 days

  const params = {
    TableName: TABLE_NAME,
    Item: {
      api_key_hash: { S: apiKeyHash },
      client_id: { S: clientId },
      client_name: { S: 'Test Client for n8n' },
      created_at: { S: new Date().toISOString() },
      expires_at: { S: expiresAt.toISOString() },
      is_active: { BOOL: true },
      permissions: { SS: ['tools/list', 'tools/call'] },
      usage_count: { N: '0' },
      created_by: { S: 'script' },
      metadata: { M: {
        purpose: { S: 'Testing MCP server with n8n' }
      }}
    }
  };

  try {
    await client.send(new PutItemCommand(params));
    console.log('✅ API Key created successfully!');
    console.log('=====================================');
    console.log('API Key (save this, it won\'t be shown again):');
    console.log(apiKey);
    console.log('=====================================');
    console.log('Client ID:', clientId);
    console.log('Expires:', expiresAt.toISOString());
    console.log('\nTo test the MCP server:');
    console.log('curl -X POST https://YOUR_API_GATEWAY_URL/mcp \\');
    console.log('  -H "Content-Type: application/json" \\');
    console.log(`  -H "x-api-key: ${apiKey}" \\`);
    console.log('  -d \'{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}\'');
  } catch (error) {
    console.error('❌ Error creating API key:', error);
    process.exit(1);
  }
}

// Check if AWS credentials are configured
if (!process.env.AWS_REGION && !process.env.AWS_DEFAULT_REGION) {
  console.log('⚠️  AWS_REGION not set, using default:', REGION);
}

createApiKey();