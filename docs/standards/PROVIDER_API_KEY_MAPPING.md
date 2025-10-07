# LLM Provider API Key Mapping

## Overview
All LLM provider API keys are stored in a single AWS Secrets Manager secret at `/ai-agent/llm-secrets/prod/` as a JSON object.

## Provider to API Key Mapping

| Provider Name | API Key Name in Secret | Authentication Type | Notes |
|--------------|------------------------|-------------------|--------|
| openai | OPENAI_API_KEY | Bearer Token | OpenAI GPT models |
| anthropic | ANTHROPIC_API_KEY | X-API-Key Header | Claude models |
| google/gemini | GEMINI_API_KEY | X-Goog-Api-Key Header | Gemini models |
| bedrock/amazon/aws | AWS_BEARER_TOKEN_BEDROCK | Bearer Token | Bedrock REST API |
| xai/grok | XAI_API_KEY | Bearer Token | Grok models |
| deepseek | DEEPSEEK_API_KEY | Bearer Token | DeepSeek models |

## Secret Structure Example

```json
{
  "OPENAI_API_KEY": "sk-...",
  "ANTHROPIC_API_KEY": "sk-ant-...",
  "GEMINI_API_KEY": "AIza...",
  "AWS_BEARER_TOKEN_BEDROCK": "eyJ...",
  "XAI_API_KEY": "xai-...",
  "DEEPSEEK_API_KEY": "sk-..."
}
```

## Bedrock Configuration

### Using Bearer Token (Recommended)
For Bedrock, we use Bearer token authentication for consistency with other providers:

```json
{
  "provider_config": {
    "provider_id": "bedrock",
    "model_id": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "endpoint": "https://bedrock-runtime.us-east-1.amazonaws.com/model/us.anthropic.claude-3-5-haiku-20241022-v1:0/converse",
    "auth_header_name": "Authorization",
    "auth_header_prefix": "Bearer ",
    "secret_path": "/ai-agent/llm-secrets/prod",
    "secret_key_name": "AWS_BEARER_TOKEN_BEDROCK",
    "request_transformer": "bedrock_converse_v1",
    "response_transformer": "bedrock_converse_v1"
  }
}
```

### Getting Bedrock Bearer Token
You can obtain a Bearer token for Bedrock using AWS STS:

```bash
# Using AWS CLI to get temporary credentials
aws sts get-session-token --duration-seconds 3600

# Or use a custom Lambda to generate and refresh tokens periodically
```

## Provider Configuration in DynamoDB

When adding models to the LLMModels table, use these configurations:

### OpenAI
```json
{
  "provider": "openai",
  "secret_key_name": "OPENAI_API_KEY",
  "auth_header_name": "Authorization",
  "auth_header_prefix": "Bearer "
}
```

### Anthropic
```json
{
  "provider": "anthropic", 
  "secret_key_name": "ANTHROPIC_API_KEY",
  "auth_header_name": "x-api-key",
  "auth_header_prefix": ""
}
```

### Bedrock (REST API)
```json
{
  "provider": "bedrock",
  "secret_key_name": "AWS_BEARER_TOKEN_BEDROCK",
  "auth_header_name": "Authorization", 
  "auth_header_prefix": "Bearer "
}
```

## UI Integration

When updating API keys through the UI:
1. Select the provider (e.g., "bedrock", "openai", "anthropic")
2. Enter the API key or Bearer token
3. The system will automatically map it to the correct key name in the secret

## Migration from Old Format

If you have secrets in the old format (separate secrets per provider), migrate them:

```bash
# Get old secret
aws secretsmanager get-secret-value --secret-id /ai-agent/llm-secrets/prod/amazon

# Update new consolidated secret
aws secretsmanager put-secret-value \
  --secret-id /ai-agent/llm-secrets/prod \
  --secret-string '{
    "OPENAI_API_KEY": "sk-...",
    "AWS_BEARER_TOKEN_BEDROCK": "eyJ..."
  }'
```