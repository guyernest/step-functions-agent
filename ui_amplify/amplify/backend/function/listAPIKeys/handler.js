import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { ScanCommand } from "@aws-sdk/client-dynamodb";
import { unmarshall } from "@aws-sdk/util-dynamodb";
const client = new DynamoDBClient({});
export const handler = async (event) => {
    console.log("List API Keys request:", JSON.stringify(event, null, 2));
    try {
        const tableName = process.env.API_KEY_TABLE_NAME;
        if (!tableName) {
            throw new Error("API_KEY_TABLE_NAME environment variable not set");
        }
        // Get the requesting user's identity
        const userId = event.identity?.sub || event.identity?.username || 'unknown';
        // Scan the table for API keys (in production, you might want to add pagination)
        const result = await client.send(new ScanCommand({
            TableName: tableName,
            // Optional: Filter by created_by if you want users to only see their own keys
            // FilterExpression: "created_by = :userId",
            // ExpressionAttributeValues: marshall({ ":userId": userId }),
        }));
        const apiKeys = [];
        if (result.Items) {
            for (const item of result.Items) {
                const record = unmarshall(item);
                // Transform DynamoDB record to API key model format
                apiKeys.push({
                    id: record.api_key_hash, // Use hash as unique ID
                    keyId: record.key_id || record.api_key_hash?.substring(0, 8),
                    clientName: record.client_name,
                    clientId: record.client_id,
                    createdAt: record.created_at,
                    expiresAt: record.expires_at,
                    lastUsed: record.last_used,
                    isActive: record.is_active || false,
                    permissions: record.permissions || [],
                    usageCount: record.usage_count || 0,
                    createdBy: record.created_by,
                    metadata: record.metadata || {}
                });
            }
        }
        // Sort by creation date (newest first)
        apiKeys.sort((a, b) => {
            const dateA = new Date(a.createdAt || 0);
            const dateB = new Date(b.createdAt || 0);
            return dateB.getTime() - dateA.getTime();
        });
        console.log(`Found ${apiKeys.length} API keys for user: ${userId}`);
        return apiKeys;
    }
    catch (error) {
        console.error("Error listing API keys:", error);
        throw new Error(`Failed to list API keys: ${error instanceof Error ? error.message : String(error)}`);
    }
};
