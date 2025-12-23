import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

declare const process: {
  env: {
    AWS_REGION?: string;
    ENVIRONMENT?: string;
  };
};

const secretsManager = new SecretsManagerClient({ region: process.env.AWS_REGION || 'us-west-2' });
const ENVIRONMENT = 'prod'; // Always use prod for now

/**
 * Mask a sensitive string value for display
 */
function maskValue(value: string): string {
  if (value.startsWith('PLACEHOLDER_')) {
    return value;
  } else if (value.length <= 8) {
    return '••••••••';
  } else {
    return value.substring(0, 4) + '••••••••' + value.substring(value.length - 4);
  }
}

export const handler = async (event: any) => {
  console.log('Get tool secret values request:', event);

  try {
    // Get the consolidated secret
    const result = await secretsManager.send(new GetSecretValueCommand({
      SecretId: `/ai-agent/tool-secrets/${ENVIRONMENT}`
    }));

    if (!result.SecretString) {
      return {
        success: false,
        error: 'No secret values found'
      };
    }

    // Parse the secret values
    const secretValues = JSON.parse(result.SecretString);

    // Mask sensitive values for security
    // Supports both flat secrets and nested endpoint secrets (like graphql-interface)
    const maskedValues: any = {};
    for (const [toolName, secrets] of Object.entries(secretValues)) {
      maskedValues[toolName] = {};
      if (typeof secrets === 'object' && secrets !== null) {
        for (const [key, value] of Object.entries(secrets as any)) {
          if (typeof value === 'string') {
            // Simple string value (standard tools like google-maps)
            maskedValues[toolName][key] = maskValue(value);
          } else if (typeof value === 'object' && value !== null) {
            // Nested object value (tools like graphql-interface with multiple endpoints)
            // Flatten to dot-notation: "LogisticY.endpoint", "LogisticY.api_key"
            for (const [subKey, subValue] of Object.entries(value as any)) {
              if (typeof subValue === 'string') {
                maskedValues[toolName][`${key}.${subKey}`] = maskValue(subValue);
              }
              // Could handle deeper nesting if needed in the future
            }
          }
        }
      }
    }

    return {
      success: true,
      values: maskedValues
      // SECURITY: Never return raw values to the UI
      // Users can update secrets but should not read existing full values
    };
  } catch (error) {
    console.error('Error getting tool secret values:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get secret values'
    };
  }
};