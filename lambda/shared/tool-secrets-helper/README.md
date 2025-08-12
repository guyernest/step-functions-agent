# Tool Secrets Helper Module

This module provides easy access to tool secrets from the consolidated secrets store across multiple programming languages.

## Features

- **Consolidated Secrets**: Access all tool secrets from a single AWS Secrets Manager secret
- **Multi-Language Support**: Helper libraries for Python, TypeScript, and Go
- **Caching**: Secrets are cached for the Lambda execution context to minimize API calls
- **Backward Compatibility**: Fallback support for legacy individual secrets
- **Placeholder Detection**: Automatically detects and warns about placeholder values

## Installation

### Python
```python
# Copy tool_secrets.py to your Lambda function
from tool_secrets import get_tool_secrets, get_secret_value
```

### TypeScript
```typescript
// Copy toolSecrets.ts to your Lambda function
import { getToolSecrets, getSecretValue } from './toolSecrets';
```

### Go
```go
// Copy toolsecrets.go to your Lambda function
import "path/to/toolsecrets"
```

## Usage Examples

### Python
```python
from tool_secrets import get_tool_secrets, get_secret_value, load_secrets_to_env

# Get all secrets for a tool
secrets = get_tool_secrets('google-maps')
api_key = secrets.get('GOOGLE_MAPS_API_KEY')

# Get a specific secret value
api_key = get_secret_value('google-maps', 'GOOGLE_MAPS_API_KEY', default='')

# Load secrets into environment variables
load_secrets_to_env('google-maps')
# Now access via os.environ['GOOGLE_MAPS_API_KEY']
```

### TypeScript
```typescript
import { getToolSecrets, getSecretValue, loadSecretsToEnv } from './toolSecrets';

// Get all secrets for a tool
const secrets = await getToolSecrets('google-maps');
const apiKey = secrets['GOOGLE_MAPS_API_KEY'];

// Get a specific secret value
const apiKey = await getSecretValue('google-maps', 'GOOGLE_MAPS_API_KEY', '');

// Load secrets into environment variables
await loadSecretsToEnv('google-maps');
// Now access via process.env.GOOGLE_MAPS_API_KEY
```

### Go
```go
import (
    "context"
    "github.com/your-org/toolsecrets"
)

ctx := context.Background()

// Get all secrets for a tool
secrets, err := toolsecrets.GetToolSecrets(ctx, "web-research")
apiKey := secrets["PPLX_API_KEY"]

// Get a specific secret value
apiKey, err := toolsecrets.GetSecretValue(ctx, "web-research", "PPLX_API_KEY", "")

// Load secrets into environment variables
err := toolsecrets.LoadSecretsToEnv(ctx, "web-research")
// Now access via os.Getenv("PPLX_API_KEY")
```

## Environment Variables

The helper modules use the following environment variables:

- `ENVIRONMENT`: The environment name (default: 'prod')
- `CONSOLIDATED_SECRET_NAME`: Override the default consolidated secret path

## Migration from Legacy Secrets

For tools that haven't been migrated yet, the helper provides backward compatibility:

```python
# Python
from tool_secrets import get_legacy_secret
secrets = get_legacy_secret('/ai-agent/tools/google-maps/prod')
```

```typescript
// TypeScript
import { getLegacySecret } from './toolSecrets';
const secrets = await getLegacySecret('/ai-agent/tools/google-maps/prod');
```

```go
// Go
secrets, err := toolsecrets.GetLegacySecret(ctx, "/ai-agent/tools/web-research/prod")
```

## Secret Structure

The consolidated secret has the following JSON structure:

```json
{
  "google-maps": {
    "GOOGLE_MAPS_API_KEY": "actual-api-key"
  },
  "execute-code": {
    "E2B_API_KEY": "actual-api-key"
  },
  "web-research": {
    "PPLX_API_KEY": "actual-api-key"
  }
}
```

## Best Practices

1. **Use Tool Name Consistently**: Always use the same tool name across registration and access
2. **Handle Placeholders**: Check for placeholder values and provide appropriate defaults
3. **Cache Wisely**: The helpers cache secrets per Lambda execution context
4. **Error Handling**: Always handle errors when retrieving secrets
5. **Environment Variables**: Only use `loadSecretsToEnv` if your tool expects env vars

## Security Considerations

- Secrets are only accessible to Lambda functions with appropriate IAM permissions
- Never log or expose secret values
- Use AWS IAM roles to control access to the consolidated secret
- Rotate secrets regularly through AWS Secrets Manager