import { SecretsManagerClient, PutSecretValueCommand, GetSecretValueCommand, CreateSecretCommand, ResourceNotFoundException } from '@aws-sdk/client-secrets-manager';
import { AppSyncResolverHandler } from 'aws-lambda';

declare const process: { env: { SECRET_PREFIX?: string } };

const secretsManager = new SecretsManagerClient({});
const SECRET_PREFIX = process.env.SECRET_PREFIX || '/ai-agent/llm-secrets/prod';

interface UpdateProviderAPIKeyArgs {
  provider: string;
  apiKey: string;
}

interface APIResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export const handler: AppSyncResolverHandler<UpdateProviderAPIKeyArgs, APIResponse> = async (event) => {
  const { provider, apiKey } = event.arguments;

  if (!provider || !apiKey) {
    return {
      success: false,
      error: 'Provider and API key are required'
    };
  }

  const secretName = `${SECRET_PREFIX}/${provider}`;

  try {
    // Try to get the existing secret first
    try {
      await secretsManager.send(new GetSecretValueCommand({
        SecretId: secretName
      }));

      // Secret exists, update it
      await secretsManager.send(new PutSecretValueCommand({
        SecretId: secretName,
        SecretString: JSON.stringify({
          apiKey: apiKey,
          provider: provider,
          updatedAt: new Date().toISOString()
        })
      }));

      return {
        success: true,
        message: `API key for ${provider} updated successfully`
      };
    } catch (error: any) {
      if (error instanceof ResourceNotFoundException || error.name === 'ResourceNotFoundException') {
        // Secret doesn't exist, create it
        await secretsManager.send(new CreateSecretCommand({
          Name: secretName,
          Description: `API key for ${provider} LLM provider`,
          SecretString: JSON.stringify({
            apiKey: apiKey,
            provider: provider,
            createdAt: new Date().toISOString()
          })
        }));

        return {
          success: true,
          message: `API key for ${provider} created successfully`
        };
      }
      throw error;
    }
  } catch (error: any) {
    console.error('Error updating API key:', error);
    return {
      success: false,
      error: `Failed to update API key: ${error.message}`
    };
  }
};