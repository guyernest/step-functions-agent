import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { UpdateItemCommand, QueryCommand } from "@aws-sdk/client-dynamodb";

const client = new DynamoDBClient({});

// Event type for revokeAPIKey
interface RevokeAPIKeyEvent {
  arguments: {
    keyId: string;
  };
  identity?: {
    sub?: string;
    username?: string;
  };
}

export const handler = async (event: RevokeAPIKeyEvent) => {
  console.log("Revoke API Key request:", JSON.stringify(event, null, 2));

  const { keyId } = event.arguments;

  if (!keyId) {
    throw new Error("keyId is required");
  }

  try {
    const tableName = process.env.API_KEY_TABLE_NAME;
    if (!tableName) {
      throw new Error("API_KEY_TABLE_NAME environment variable not set");
    }

    // First, find the API key by keyId (using GSI)
    const queryResult = await client.send(new QueryCommand({
      TableName: tableName,
      IndexName: "client-id-index",
      FilterExpression: "begins_with(api_key_hash, :keyId)",
      ExpressionAttributeValues: {
        ":keyId": { S: keyId }
      }
    }));

    if (!queryResult.Items || queryResult.Items.length === 0) {
      throw new Error("API key not found");
    }

    const apiKeyHash = queryResult.Items[0].api_key_hash?.S;
    if (!apiKeyHash) {
      throw new Error("Invalid API key record");
    }

    // Update the API key to inactive
    await client.send(new UpdateItemCommand({
      TableName: tableName,
      Key: {
        api_key_hash: { S: apiKeyHash }
      },
      UpdateExpression: "SET is_active = :inactive, revoked_at = :now",
      ExpressionAttributeValues: {
        ":inactive": { BOOL: false },
        ":now": { S: new Date().toISOString() }
      }
    }));

    console.log(`Revoked API key: ${keyId}`);

    return {
      success: true,
      keyId: keyId,
      message: "API key has been revoked successfully"
    };

  } catch (error) {
    console.error("Error revoking API key:", error);
    throw new Error(`Failed to revoke API key: ${error instanceof Error ? error.message : String(error)}`);
  }
};