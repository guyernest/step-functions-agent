import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { PutItemCommand, GetItemCommand } from "@aws-sdk/client-dynamodb";
import { createHash, randomBytes } from 'crypto';

const client = new DynamoDBClient({});

// Event type for generateAPIKey
interface GenerateAPIKeyEvent {
  arguments: {
    clientName: string;
    clientId: string;
    expiresInDays?: number;
    permissions?: string[];
  };
  identity?: {
    sub?: string;
    username?: string;
  };
  request?: {
    headers?: Record<string, string>;
  };
}

export const handler = async (event: GenerateAPIKeyEvent) => {
  console.log("Generate API Key request:", JSON.stringify(event, null, 2));

  const { clientName, clientId, expiresInDays = 90, permissions = ["start_agent", "list_agents", "get_execution"] } = event.arguments;

  if (!clientName || !clientId) {
    throw new Error("clientName and clientId are required");
  }

  try {
    // Generate a secure API key with prefix
    const keyBytes = randomBytes(32);
    const apiKey = `sfaf_${keyBytes.toString('base64url')}`;
    
    // Hash the API key for storage
    const apiKeyHash = createHash('sha256').update(apiKey).digest('hex');
    
    // Calculate expiration date
    const now = new Date();
    const expiresAt = new Date(now.getTime() + (expiresInDays * 24 * 60 * 60 * 1000));
    
    // Get the requesting user's identity from context
    const userId = event.identity?.sub || event.identity?.username || 'unknown';
    const keyId = apiKeyHash.substring(0, 8); // Short identifier
    
    // Store the API key record in DynamoDB
    const tableName = process.env.API_KEY_TABLE_NAME;
    if (!tableName) {
      throw new Error("API_KEY_TABLE_NAME environment variable not set");
    }

    await client.send(new PutItemCommand({
      TableName: tableName,
      Item: {
        api_key_hash: { S: apiKeyHash },
        key_id: { S: keyId },
        client_name: { S: clientName },
        client_id: { S: clientId },
        created_at: { S: now.toISOString() },
        expires_at: { S: expiresAt.toISOString() },
        is_active: { BOOL: true },
        permissions: { SS: permissions },
        usage_count: { N: "0" },
        created_by: { S: userId },
        metadata: { M: {
          created_from: { S: "ui" },
          user_agent: { S: event.request?.headers?.["user-agent"] || "unknown" }
        }}
      }
    }));

    console.log(`Generated API key for client: ${clientId} (key ID: ${keyId})`);

    return {
      success: true,
      apiKey: apiKey, // Only returned once
      keyId: keyId,
      clientName: clientName,
      clientId: clientId,
      expiresAt: expiresAt.toISOString(),
      permissions: permissions,
      message: "API key generated successfully. Store this key securely - it will not be shown again."
    };

  } catch (error) {
    console.error("Error generating API key:", error);
    throw new Error(`Failed to generate API key: ${error instanceof Error ? error.message : String(error)}`);
  }
};