import { SecretsManagerClient, GetSecretValueCommand, UpdateSecretCommand } from '@aws-sdk/client-secrets-manager';

declare const process: {
  env: {
    AWS_REGION?: string;
    ENVIRONMENT?: string;
  };
};

const secretsManager = new SecretsManagerClient({ region: process.env.AWS_REGION || 'us-west-2' });
const ENVIRONMENT = 'prod'; // Always use prod for now

/**
 * Unflatten dot-notation keys back to nested objects
 * Example: {"LogisticY.endpoint": "url", "LogisticY.api_key": "key"}
 * Becomes: {"LogisticY": {"endpoint": "url", "api_key": "key"}}
 */
function unflattenSecrets(secrets: Record<string, string>): Record<string, any> {
  const result: Record<string, any> = {};

  for (const [key, value] of Object.entries(secrets)) {
    if (key.includes('.')) {
      // Dot-notation key - unflatten to nested structure
      const [parent, child] = key.split('.', 2);
      if (!result[parent]) {
        result[parent] = {};
      }
      result[parent][child] = value;
    } else {
      // Simple key - keep as is
      result[key] = value;
    }
  }

  return result;
}

/**
 * Deep merge two objects, preserving nested structures
 */
function deepMerge(target: Record<string, any>, source: Record<string, any>): Record<string, any> {
  const result = { ...target };

  for (const [key, value] of Object.entries(source)) {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      // Nested object - merge recursively
      result[key] = deepMerge(result[key] || {}, value);
    } else {
      // Simple value - overwrite
      result[key] = value;
    }
  }

  return result;
}

export const handler = async (event: any) => {
  console.log('Update tool secrets request:', event);

  const { toolName, secrets } = event.arguments || {};

  if (!toolName || !secrets) {
    return {
      success: false,
      error: 'toolName and secrets are required'
    };
  }

  try {
    const secretId = `/ai-agent/tool-secrets/${ENVIRONMENT}`;

    // First get the current secret values
    const currentResult = await secretsManager.send(new GetSecretValueCommand({
      SecretId: secretId
    }));

    if (!currentResult.SecretString) {
      return {
        success: false,
        error: 'No existing secret found'
      };
    }

    // Parse current values
    const currentValues = JSON.parse(currentResult.SecretString);

    // Unflatten dot-notation keys (e.g., "LogisticY.endpoint" -> nested object)
    const unflattenedSecrets = unflattenSecrets(secrets);

    // Initialize tool entry if it doesn't exist
    if (!currentValues[toolName]) {
      currentValues[toolName] = {};
    }

    // Deep merge new values with existing ones (preserves nested structures)
    currentValues[toolName] = deepMerge(currentValues[toolName], unflattenedSecrets);

    // Update the secret
    await secretsManager.send(new UpdateSecretCommand({
      SecretId: secretId,
      SecretString: JSON.stringify(currentValues)
    }));

    return {
      success: true,
      message: `Successfully updated secrets for ${toolName}`,
      toolName
    };
  } catch (error) {
    console.error('Error updating tool secrets:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to update secrets'
    };
  }
};