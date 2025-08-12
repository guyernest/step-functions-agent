/**
 * Tool Secrets Helper Module (TypeScript)
 * Provides easy access to tool secrets from the consolidated secret
 */

import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

// Initialize AWS client
const secretsManager = new SecretsManagerClient({});

// Cache for secrets
let cachedSecrets: Record<string, Record<string, string>> | null = null;

/**
 * Get the consolidated secret name from environment or default
 */
function getConsolidatedSecretName(): string {
    const envName = process.env.ENVIRONMENT || 'prod';
    return process.env.CONSOLIDATED_SECRET_NAME || `/ai-agent/tool-secrets/${envName}`;
}

/**
 * Get all secrets from the consolidated secret
 * Results are cached for the Lambda execution context
 */
export async function getAllSecrets(): Promise<Record<string, Record<string, string>>> {
    // Return cached value if available
    if (cachedSecrets) {
        return cachedSecrets;
    }

    const secretName = getConsolidatedSecretName();
    
    try {
        const command = new GetSecretValueCommand({ SecretId: secretName });
        const response = await secretsManager.send(command);
        
        if (response.SecretString) {
            cachedSecrets = JSON.parse(response.SecretString);
            return cachedSecrets || {};
        }
        return {};
    } catch (error) {
        console.error(`Error retrieving consolidated secrets: ${error}`);
        return {};
    }
}

/**
 * Get secrets for a specific tool from the consolidated secret
 * @param toolName - Name of the tool (e.g., 'google-maps', 'execute-code')
 * @returns Object containing secret key-value pairs for the tool
 */
export async function getToolSecrets(toolName: string): Promise<Record<string, string>> {
    const allSecrets = await getAllSecrets();
    return allSecrets[toolName] || {};
}

/**
 * Get a specific secret value for a tool
 * @param toolName - Name of the tool
 * @param secretKey - Key of the secret (e.g., 'GOOGLE_MAPS_API_KEY')
 * @param defaultValue - Default value if secret not found
 * @returns Secret value or default
 */
export async function getSecretValue(
    toolName: string, 
    secretKey: string, 
    defaultValue?: string
): Promise<string | undefined> {
    const toolSecrets = await getToolSecrets(toolName);
    const value = toolSecrets[secretKey] || defaultValue;
    
    // Check if it's a placeholder
    if (value && value.startsWith('PLACEHOLDER_')) {
        console.warn(`Warning: Using placeholder value for ${toolName}/${secretKey}`);
        return defaultValue;
    }
    
    return value;
}

/**
 * Get secrets from a legacy individual secret path
 * This function provides backward compatibility for tools that haven't been migrated yet
 * @param secretPath - Legacy secret path (e.g., '/ai-agent/tools/google-maps/prod')
 * @returns Object containing secret key-value pairs
 */
export async function getLegacySecret(secretPath: string): Promise<Record<string, string>> {
    try {
        // First try the legacy path
        const command = new GetSecretValueCommand({ SecretId: secretPath });
        const response = await secretsManager.send(command);
        
        if (response.SecretString) {
            return JSON.parse(response.SecretString);
        }
        return {};
    } catch (error: any) {
        // Fall back to consolidated secret
        if (error.name === 'ResourceNotFoundException') {
            // Extract tool name from path
            const parts = secretPath.split('/');
            const toolIdx = parts.indexOf('tools');
            if (toolIdx !== -1 && toolIdx + 1 < parts.length) {
                const toolName = parts[toolIdx + 1];
                return await getToolSecrets(toolName);
            }
        }
        console.error(`Error retrieving legacy secret from ${secretPath}: ${error}`);
        return {};
    }
}

/**
 * Load tool secrets into environment variables
 * Useful for tools that expect secrets in env vars
 * @param toolName - Name of the tool
 */
export async function loadSecretsToEnv(toolName: string): Promise<void> {
    const secrets = await getToolSecrets(toolName);
    for (const [key, value] of Object.entries(secrets)) {
        if (!value.startsWith('PLACEHOLDER_')) {
            process.env[key] = value;
        }
    }
}

/**
 * Clear the cached secrets (useful for testing)
 */
export function clearCache(): void {
    cachedSecrets = null;
}