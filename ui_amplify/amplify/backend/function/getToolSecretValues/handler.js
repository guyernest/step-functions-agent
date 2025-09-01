import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';
const secretsManager = new SecretsManagerClient({ region: process.env.AWS_REGION || 'us-west-2' });
const ENVIRONMENT = 'prod'; // Always use prod for now
export const handler = async (event) => {
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
        const maskedValues = {};
        for (const [toolName, secrets] of Object.entries(secretValues)) {
            maskedValues[toolName] = {};
            if (typeof secrets === 'object' && secrets !== null) {
                for (const [key, value] of Object.entries(secrets)) {
                    if (typeof value === 'string') {
                        // Keep placeholders visible, mask actual values
                        if (value.startsWith('PLACEHOLDER_')) {
                            maskedValues[toolName][key] = value;
                        }
                        else if (value.length <= 8) {
                            maskedValues[toolName][key] = '••••••••';
                        }
                        else {
                            maskedValues[toolName][key] = value.substring(0, 4) + '••••••••' + value.substring(value.length - 4);
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
    }
    catch (error) {
        console.error('Error getting tool secret values:', error);
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Failed to get secret values'
        };
    }
};
