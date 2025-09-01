import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { PutItemCommand, QueryCommand, UpdateItemCommand } from "@aws-sdk/client-dynamodb";
import * as crypto from 'crypto';
const client = new DynamoDBClient({});
export const handler = async (event) => {
    console.log("Rotate API Key request:", JSON.stringify(event, null, 2));
    const { keyId, expiresInDays = 90 } = event.arguments;
    if (!keyId) {
        throw new Error("keyId is required");
    }
    try {
        const tableName = process.env.API_KEY_TABLE_NAME;
        if (!tableName) {
            throw new Error("API_KEY_TABLE_NAME environment variable not set");
        }
        // First, find the existing API key by keyId
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
        const oldRecord = queryResult.Items[0];
        const oldApiKeyHash = oldRecord.api_key_hash?.S;
        const clientName = oldRecord.client_name?.S;
        const clientId = oldRecord.client_id?.S;
        const permissions = oldRecord.permissions?.SS || [];
        if (!oldApiKeyHash || !clientName || !clientId) {
            throw new Error("Invalid API key record");
        }
        // Generate a new API key
        const keyBytes = crypto.randomBytes(32);
        const newApiKey = `sfaf_${keyBytes.toString('base64url')}`;
        const newApiKeyHash = crypto.createHash('sha256').update(newApiKey).digest('hex');
        // Calculate expiration date
        const now = new Date();
        const expiresAt = new Date(now.getTime() + (expiresInDays * 24 * 60 * 60 * 1000));
        const userId = event.identity?.sub || event.identity?.username || 'unknown';
        const newKeyId = newApiKeyHash.substring(0, 8);
        // Create the new API key record
        await client.send(new PutItemCommand({
            TableName: tableName,
            Item: {
                api_key_hash: { S: newApiKeyHash },
                key_id: { S: newKeyId },
                client_name: { S: clientName },
                client_id: { S: clientId },
                created_at: { S: now.toISOString() },
                expires_at: { S: expiresAt.toISOString() },
                is_active: { BOOL: true },
                permissions: { SS: permissions },
                usage_count: { N: "0" },
                created_by: { S: userId },
                metadata: { M: {
                        created_from: { S: "rotation" },
                        rotated_from: { S: keyId },
                        user_agent: { S: event.request?.headers?.["user-agent"] || "unknown" }
                    } }
            }
        }));
        // Mark the old API key as rotated (keep it for a grace period)
        await client.send(new UpdateItemCommand({
            TableName: tableName,
            Key: {
                api_key_hash: { S: oldApiKeyHash }
            },
            UpdateExpression: "SET is_active = :inactive, rotated_at = :now, rotated_to = :newKeyId",
            ExpressionAttributeValues: {
                ":inactive": { BOOL: false },
                ":now": { S: now.toISOString() },
                ":newKeyId": { S: newKeyId }
            }
        }));
        console.log(`Rotated API key: ${keyId} -> ${newKeyId}`);
        return {
            success: true,
            newApiKey: newApiKey, // Only returned once
            newKeyId: newKeyId,
            oldKeyId: keyId,
            clientName: clientName,
            clientId: clientId,
            expiresAt: expiresAt.toISOString(),
            permissions: permissions,
            message: "API key rotated successfully. Update your integration with the new key. The old key is now inactive."
        };
    }
    catch (error) {
        console.error("Error rotating API key:", error);
        throw new Error(`Failed to rotate API key: ${error instanceof Error ? error.message : String(error)}`);
    }
};
