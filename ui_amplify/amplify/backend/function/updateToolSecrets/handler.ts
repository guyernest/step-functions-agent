import { SecretsManagerClient, GetSecretValueCommand, UpdateSecretCommand } from '@aws-sdk/client-secrets-manager';

declare const process: {
  env: {
    AWS_REGION?: string;
    ENVIRONMENT?: string;
  };
};

const secretsManager = new SecretsManagerClient({ region: process.env.AWS_REGION || 'us-west-2' });
const ENVIRONMENT = process.env.ENVIRONMENT || 'prod';

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
    
    // Update with new values for the specific tool
    currentValues[toolName] = secrets;
    
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