import { SecretsManagerClient, PutSecretValueCommand, GetSecretValueCommand, CreateSecretCommand, ResourceNotFoundException } from '@aws-sdk/client-secrets-manager';
const secretsManager = new SecretsManagerClient({});
const SECRET_NAME = process.env.SECRET_PREFIX || '/ai-agent/llm-secrets/prod';
// Mapping of provider names to API key names in the secret
const PROVIDER_KEY_MAPPING = {
    // OpenAI compatible providers
    'openai': 'OPENAI_API_KEY',
    'xai': 'XAI_API_KEY',
    'grok': 'XAI_API_KEY', // Grok uses XAI
    'deepseek': 'DEEPSEEK_API_KEY',
    // Anthropic
    'anthropic': 'ANTHROPIC_API_KEY',
    'claude': 'ANTHROPIC_API_KEY', // Alias
    // Google
    'google': 'GEMINI_API_KEY',
    'gemini': 'GEMINI_API_KEY', // Alias
    // AWS Bedrock
    'bedrock': 'AWS_BEARER_TOKEN_BEDROCK',
    'amazon': 'AWS_BEARER_TOKEN_BEDROCK', // Alias
    'aws': 'AWS_BEARER_TOKEN_BEDROCK', // Alias
    // Additional providers can be added here
};
export const handler = async (event) => {
    const { provider, apiKey } = event.arguments;
    if (!provider || !apiKey) {
        return {
            success: false,
            error: 'Provider and API key are required'
        };
    }
    // Get the API key name for this provider
    const keyName = PROVIDER_KEY_MAPPING[provider.toLowerCase()];
    if (!keyName) {
        return {
            success: false,
            error: `Unknown provider: ${provider}. Supported providers: ${Object.keys(PROVIDER_KEY_MAPPING).join(', ')}`
        };
    }
    try {
        let existingSecrets = {};
        // Try to get the existing secret
        try {
            const getResponse = await secretsManager.send(new GetSecretValueCommand({
                SecretId: SECRET_NAME
            }));
            if (getResponse.SecretString) {
                existingSecrets = JSON.parse(getResponse.SecretString);
            }
        }
        catch (error) {
            if (error instanceof ResourceNotFoundException || error.name === 'ResourceNotFoundException') {
                console.log('Secret does not exist, will create new one');
            }
            else {
                throw error;
            }
        }
        // Update the specific API key
        existingSecrets[keyName] = apiKey;
        // Add metadata
        existingSecrets[`${keyName}_UPDATED_AT`] = new Date().toISOString();
        existingSecrets[`${keyName}_PROVIDER`] = provider;
        // Check if secret exists to decide between create and update
        const secretExists = await secretsManager.send(new GetSecretValueCommand({
            SecretId: SECRET_NAME
        })).then(() => true).catch(() => false);
        if (secretExists) {
            // Update existing secret
            await secretsManager.send(new PutSecretValueCommand({
                SecretId: SECRET_NAME,
                SecretString: JSON.stringify(existingSecrets, null, 2)
            }));
            return {
                success: true,
                message: `API key for ${provider} (${keyName}) updated successfully`,
                keyName: keyName
            };
        }
        else {
            // Create new secret
            await secretsManager.send(new CreateSecretCommand({
                Name: SECRET_NAME,
                Description: 'API keys for LLM providers',
                SecretString: JSON.stringify(existingSecrets, null, 2)
            }));
            return {
                success: true,
                message: `Secret created and API key for ${provider} (${keyName}) added successfully`,
                keyName: keyName
            };
        }
    }
    catch (error) {
        console.error('Error updating API key:', error);
        return {
            success: false,
            error: `Failed to update API key: ${error.message}`
        };
    }
};
