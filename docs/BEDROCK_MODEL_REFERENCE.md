# Amazon Bedrock Model Quick Reference

## ⚠️ Critical Information

**ALWAYS use Inference Profile IDs, not base model IDs!**

Find your inference profiles here:
- [EU West 1 (Ireland)](https://console.aws.amazon.com/bedrock/home?region=eu-west-1#inference-profiles)
- [US East 1 (N. Virginia)](https://console.aws.amazon.com/bedrock/home?region=us-east-1#inference-profiles)
- [US West 2 (Oregon)](https://console.aws.amazon.com/bedrock/home?region=us-west-2#inference-profiles)

## How to Find Model IDs

1. Open AWS Console → Bedrock → Inference Profiles
2. Look for the **Profile ARN**
3. Extract the model ID from the end of the ARN

Example:
```
ARN: arn:aws:bedrock:eu-west-1::foundation-model/eu.amazon.nova-pro-v1:0
Model ID: eu.amazon.nova-pro-v1:0  ← Use this in the system
```

## Available Models by Provider

### Amazon Nova (Native)

**Note:** Model IDs include region prefix (eu., us., etc.)

| Model ID (EU Region) | Model ID (US Regions) | Description | Context | Tools | Vision |
|----------------------|------------------------|-------------|---------|-------|--------|
| `eu.amazon.nova-micro-v1:0` | `us.amazon.nova-micro-v1:0` | Fastest, most cost-effective | 128K | ✅ | ❌ |
| `eu.amazon.nova-lite-v1:0` | `us.amazon.nova-lite-v1:0` | Balanced performance | 300K | ✅ | ✅ |
| `eu.amazon.nova-pro-v1:0` | `us.amazon.nova-pro-v1:0` | Advanced reasoning | 300K | ✅ | ✅ |

### Anthropic Claude (via Bedrock)
| Model ID | Description | Context | Tools | Vision |
|----------|-------------|---------|-------|--------|
| `anthropic.claude-3-5-sonnet-20241022-v2:0` | Latest, most capable | 200K | ✅ | ✅ |
| `anthropic.claude-3-opus-20240229-v1:0` | Most powerful Claude 3 | 200K | ✅ | ✅ |
| `anthropic.claude-3-sonnet-20240229-v1:0` | Balanced Claude 3 | 200K | ✅ | ✅ |
| `anthropic.claude-3-haiku-20240307-v1:0` | Fast, efficient | 200K | ✅ | ✅ |
| `anthropic.claude-instant-1.2` | Legacy fast model | 100K | ❌ | ❌ |

### Meta Llama (via Bedrock)
| Model ID | Description | Context | Tools | Vision |
|----------|-------------|---------|-------|--------|
| `meta.llama3-1-405b-instruct-v1:0` | Largest Llama | 128K | ✅ | ❌ |
| `meta.llama3-1-70b-instruct-v1:0` | Large Llama | 128K | ✅ | ❌ |
| `meta.llama3-1-8b-instruct-v1:0` | Efficient Llama | 128K | ✅ | ❌ |
| `meta.llama3-2-90b-instruct-v1:0` | Latest large Llama | 128K | ✅ | ✅ |
| `meta.llama3-2-11b-instruct-v1:0` | Latest medium Llama | 128K | ✅ | ✅ |
| `meta.llama3-2-3b-instruct-v1:0` | Latest small Llama | 128K | ✅ | ✅ |

### Mistral AI (via Bedrock)
| Model ID | Description | Context | Tools | Vision |
|----------|-------------|---------|-------|--------|
| `mistral.mistral-large-2407-v1:0` | Large Mistral | 128K | ✅ | ❌ |
| `mistral.mixtral-8x7b-instruct-v0:1` | MoE model | 32K | ✅ | ❌ |
| `mistral.mistral-7b-instruct-v0:2` | Efficient | 32K | ❌ | ❌ |

### Cohere (via Bedrock)
| Model ID | Description | Context | Tools | Vision |
|----------|-------------|---------|-------|--------|
| `cohere.command-r-plus-v1:0` | Advanced RAG | 128K | ✅ | ❌ |
| `cohere.command-r-v1:0` | Efficient RAG | 128K | ✅ | ❌ |
| `cohere.command-text-v14` | Legacy | 4K | ❌ | ❌ |

### AI21 Labs (via Bedrock)
| Model ID | Description | Context | Tools | Vision |
|----------|-------------|---------|-------|--------|
| `ai21.jamba-1-5-large-v1:0` | Large Jamba | 256K | ✅ | ❌ |
| `ai21.jamba-1-5-mini-v1:0` | Mini Jamba | 256K | ✅ | ❌ |
| `ai21.j2-ultra-v1` | Legacy J2 | 8K | ❌ | ❌ |
| `ai21.j2-mid-v1` | Legacy J2 | 8K | ❌ | ❌ |

## Configuration Example

When adding to the system:

```python
{
    'provider': 'bedrock',  # or 'amazon' - both work
    'model_id': 'eu.amazon.nova-pro-v1:0',  # Use exact inference profile ID with region prefix
    'display_name': 'Amazon Nova Pro',
    'input_price': 0.80,  # Per million tokens
    'output_price': 3.20,  # Per million tokens
    'max_tokens': 300000,
    'supports_tools': True,
    'supports_vision': True,
    'is_default': False
}
```

## Endpoint Configuration

The system automatically configures endpoints based on region:

- **EU West 1:** `https://bedrock-runtime.eu-west-1.amazonaws.com/model/{model_id}/converse`
- **US East 1:** `https://bedrock-runtime.us-east-1.amazonaws.com/model/{model_id}/converse`
- **US West 2:** `https://bedrock-runtime.us-west-2.amazonaws.com/model/{model_id}/converse`

## Authentication

Bedrock models use Bearer token authentication:
- Secret path: `/ai-agent/llm-secrets/prod`
- Secret key: `AWS_BEARER_TOKEN_BEDROCK`
- Header: `Authorization: Bearer {token}`

## Enabling Models

Before using any model:

1. Go to AWS Console → Bedrock → Model access
2. Click "Manage model access"
3. Select the models you want to use
4. Submit request (some are instant, others need approval)
5. Wait for "Access granted" status

## Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "Model not found" | Wrong model ID | Use inference profile ID, not base model ID |
| "Access denied" | Model not enabled | Enable model in Bedrock console |
| "Invalid region" | Model not available | Check model availability in your region |
| "Unexpected field type" | Format mismatch | Verify using Converse API format |

## Testing Models

Quick test via AWS CLI:
```bash
aws bedrock-runtime converse \
  --model-id "eu.amazon.nova-lite-v1:0" \
  --messages '[{"role":"user","content":[{"text":"Hello"}]}]' \
  --region eu-west-1
```

## Cost Optimization Tips

1. **Development:** Use Nova Micro or Claude Haiku
2. **Production Simple:** Use Nova Lite or Llama 8B
3. **Production Complex:** Use Nova Pro or Claude Sonnet
4. **Advanced Reasoning:** Use Claude Opus or Llama 405B

## Links

- [Bedrock Pricing Calculator](https://calculator.aws/#/addService/Bedrock)
- [Model Comparison](https://docs.aws.amazon.com/bedrock/latest/userguide/model-comparison.html)
- [Service Quotas](https://console.aws.amazon.com/servicequotas/home/services/bedrock/quotas)