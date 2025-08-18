# Model Management Guide

This guide provides instructions for managing LLM models across different providers in the Step Functions Agent system.

## Table of Contents
- [Overview](#overview)
- [Finding Model IDs](#finding-model-ids)
  - [OpenAI Models](#openai-models)
  - [Anthropic Claude Models](#anthropic-claude-models)
  - [Google Gemini Models](#google-gemini-models)
  - [Amazon Bedrock Models](#amazon-bedrock-models)
- [Adding Models to the System](#adding-models-to-the-system)
- [Configuring API Keys](#configuring-api-keys)
- [Dynamic Provider Switching](#dynamic-provider-switching)

## Overview

The system supports multiple LLM providers through a unified interface:
- **OpenAI** - GPT-4, GPT-4 Turbo, GPT-3.5
- **Anthropic** - Claude 3.5, Claude 3, Claude Instant
- **Google** - Gemini Pro, Gemini Flash
- **Amazon Bedrock** - Nova, Claude (via Bedrock), Llama, and more

## Finding Model IDs

### OpenAI Models

Model IDs for OpenAI are standardized and can be found in the [OpenAI API documentation](https://platform.openai.com/docs/models).

Common model IDs:
- `gpt-4o` - Latest GPT-4 Optimized
- `gpt-4o-mini` - Smaller, faster GPT-4 variant
- `gpt-4-turbo-preview` - GPT-4 Turbo with vision
- `gpt-3.5-turbo` - Latest GPT-3.5 Turbo

### Anthropic Claude Models

Model IDs for Anthropic follow a consistent naming pattern. See the [Anthropic API documentation](https://docs.anthropic.com/claude/docs/models-overview).

Common model IDs:
- `claude-3-5-sonnet-20241022` - Latest Claude 3.5 Sonnet
- `claude-3-opus-20240229` - Claude 3 Opus (most capable)
- `claude-3-sonnet-20240229` - Claude 3 Sonnet (balanced)
- `claude-3-haiku-20240307` - Claude 3 Haiku (fastest)

### Google Gemini Models

Model IDs for Google Gemini can be found in the [Google AI documentation](https://ai.google.dev/models/gemini).

Common model IDs:
- `gemini-2.0-flash-exp` - Latest experimental Gemini 2.0 Flash
- `gemini-1.5-pro-002` - Gemini 1.5 Pro with 2M context
- `gemini-1.5-flash-002` - Faster Gemini 1.5 Flash

### Amazon Bedrock Models

**⚠️ IMPORTANT: Amazon Bedrock Model IDs**

For Amazon Bedrock, you must use **Inference Profiles** instead of base model IDs. Inference profiles provide optimized endpoints for model inference.

#### Finding Bedrock Model IDs:

1. **Access the Bedrock Console:**
   - Navigate to the [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
   - Select your region (e.g., `eu-west-1`)

2. **Go to Inference Profiles:**
   - In the left sidebar, click on **"Inference profiles"**
   - Direct link for eu-west-1: [Bedrock Inference Profiles](https://console.aws.amazon.com/bedrock/home?region=eu-west-1#inference-profiles)

3. **Identify the Model ID:**
   - Each inference profile shows the **Profile ARN**
   - The model ID is the last part of the ARN
   - Format: `arn:aws:bedrock:region::foundation-model/MODEL_ID`
   
   Example:
   - Profile ARN: `arn:aws:bedrock:eu-west-1::foundation-model/eu.amazon.nova-lite-v1:0`
   - Model ID: `eu.amazon.nova-lite-v1:0`

4. **Common Bedrock Model IDs:**
   
   **Amazon Nova Models (EU Region):**
   - `eu.amazon.nova-micro-v1:0` - Smallest, fastest Nova model
   - `eu.amazon.nova-lite-v1:0` - Lightweight Nova model
   - `eu.amazon.nova-pro-v1:0` - Professional-grade Nova model
   
   **Amazon Nova Models (US Regions):**
   - `us.amazon.nova-micro-v1:0` - Smallest, fastest Nova model
   - `us.amazon.nova-lite-v1:0` - Lightweight Nova model
   - `us.amazon.nova-pro-v1:0` - Professional-grade Nova model
   
   **Claude via Bedrock:**
   - `anthropic.claude-3-5-sonnet-20241022-v2:0` - Claude 3.5 Sonnet
   - `anthropic.claude-3-opus-20240229-v1:0` - Claude 3 Opus
   - `anthropic.claude-3-sonnet-20240229-v1:0` - Claude 3 Sonnet
   - `anthropic.claude-3-haiku-20240307-v1:0` - Claude 3 Haiku
   
   **Meta Llama Models:**
   - `meta.llama3-1-405b-instruct-v1:0` - Llama 3.1 405B
   - `meta.llama3-1-70b-instruct-v1:0` - Llama 3.1 70B
   - `meta.llama3-1-8b-instruct-v1:0` - Llama 3.1 8B

5. **Enable Models:**
   - Before using a model, ensure it's enabled in your AWS account
   - Go to **"Model access"** in the Bedrock console
   - Request access to the models you want to use
   - Wait for approval (some models are instant, others require review)

## Adding Models to the System

Models are stored in the DynamoDB `LLMModels` table. To add or update models:

1. **Use the populate script:**
   ```bash
   python scripts/populate_llm_models.py
   ```

2. **Manual addition via AWS Console:**
   - Navigate to DynamoDB → Tables → LLMModels-prod
   - Add item with structure:
   ```json
   {
     "pk": "provider#model_id",
     "provider": "bedrock",
     "model_id": "eu.amazon.nova-pro-v1:0",
     "display_name": "Amazon Nova Pro",
     "input_price": 0.80,
     "output_price": 3.20,
     "max_tokens": 300000,
     "supports_tools": true,
     "supports_vision": true,
     "is_default": false
   }
   ```

## Configuring API Keys

### For Bedrock with Bearer Token

1. **Generate Bearer Token:**
   - Use AWS STS to generate temporary credentials
   - Convert to Bearer token format
   - Store in AWS Secrets Manager

2. **Update via UI:**
   - Go to Model Management page
   - Select "Bedrock" provider
   - Enter Bearer token
   - Click "Update API Key"

3. **Secret Storage:**
   - Secrets are stored in: `/ai-agent/llm-secrets/prod`
   - Key name: `AWS_BEARER_TOKEN_BEDROCK`

### For Other Providers

- **OpenAI:** Use key name `OPENAI_API_KEY`
- **Anthropic:** Use key name `ANTHROPIC_API_KEY`
- **Google:** Use key name `GEMINI_API_KEY`

## Dynamic Provider Switching

For Rust-based agents, you can switch providers dynamically:

1. **Via UI:**
   - Open agent details
   - Select new provider/model from dropdown
   - Changes apply immediately without redeployment

2. **Via DynamoDB:**
   - Update `AgentRegistry` table
   - Modify `llm_provider` and `llm_model` fields
   - Changes take effect on next invocation

## Troubleshooting

### Common Issues

1. **"Missing field endpoint" error:**
   - Ensure the Step Functions template includes Bedrock provider mappings
   - Verify the endpoint URL includes the correct region

2. **"Unexpected field type" error:**
   - Check that the model ID matches the inference profile exactly
   - Verify the model is enabled in your AWS account

3. **Authentication failures:**
   - Ensure Bearer token is valid and not expired
   - Check IAM permissions for Bedrock access
   - Verify secret key names match expected values

### Bedrock-Specific Notes

- **Region:** Bedrock models are region-specific. Ensure you're using the correct region endpoint
- **Inference Profiles:** Always use inference profile IDs, not base model IDs
- **Quotas:** Check your Bedrock service quotas for rate limits and concurrent requests
- **Cross-Region:** Some models may not be available in all regions

## Best Practices

1. **Model Selection:**
   - Use smaller models (mini, lite, haiku) for simple tasks
   - Reserve larger models (opus, pro) for complex reasoning
   - Consider cost vs. performance tradeoffs

2. **Provider Configuration:**
   - Keep API keys in AWS Secrets Manager
   - Rotate keys regularly
   - Use separate keys for dev/prod environments

3. **Monitoring:**
   - Track token usage via CloudWatch metrics
   - Monitor costs per provider
   - Set up alerts for unusual usage patterns

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Model Comparison Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/model-comparison.html)
- [API Rate Limits](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas.html)