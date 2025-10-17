# AgentCore Browser Agents

This directory contains the containerized browser automation agents that run on AWS Bedrock AgentCore.

## Structure

```
agents/
├── simple_nova_agent.py  # Main agent handler (supports multiple agent types)
├── Dockerfile            # Container definition for AgentCore runtime
├── requirements.txt      # Python dependencies
└── .dockerignore        # Files to exclude from Docker build
```

## Agent Types

The agent supports multiple browser automation tasks via the `AGENT_TYPE` environment variable:

### 1. Broadband Agent (`AGENT_TYPE=broadband`)
- **Purpose**: UK broadband availability checking using BT Wholesale portal
- **Input**: Postcode, building number, street, town
- **Output**: Speed, availability, technology, provider
- **Tool Name**: `browser_broadband`

### 2. Shopping Agent (`AGENT_TYPE=shopping`)
- **Purpose**: E-commerce product search and price comparison
- **Input**: Search query, site (amazon/ebay), max results
- **Output**: Product listings with prices, ratings, URLs
- **Tool Name**: `browser_shopping`

### 3. Search Agent (`AGENT_TYPE=search`)
- **Purpose**: General web search and information extraction
- **Input**: Search query, URL (optional), extract fields
- **Output**: Extracted content from web pages
- **Tool Name**: `browser_search`

## Configuration

### Environment Variables (set by CDK)

- `AWS_REGION`: AWS region (default: us-west-2)
- `AGENT_TYPE`: Type of agent (broadband, shopping, search)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `DOCKER_CONTAINER`: Signal running in container (1)

### Secrets Management

Credentials are injected at the Lambda layer and passed through to the agent in the payload:

```json
{
  "input": {
    "postcode": "SW1A 1AA",
    "credentials": {
      "username": "user@example.com",
      "password": "decrypted_password"
    }
  }
}
```

The agent code checks for the `credentials` field and uses it for authenticated operations.

## Building and Deploying

### Build Container

```bash
# From project root
make build-agentcore-containers ENV_NAME=prod
```

This will:
1. Build ARM64 Docker image
2. Push to all 3 ECR repositories
3. AgentCore runtimes automatically use new image

### Local Testing

```bash
# Build locally
cd lambda/tools/agentcore_browser/agents
docker build --platform linux/arm64 -t agentcore-test .

# Run locally (requires AWS credentials)
docker run -p 8080:8080 \
  -e AWS_REGION=us-west-2 \
  -e AGENT_TYPE=broadband \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  agentcore-test
```

## Health Check Endpoints

The agent implements standard AgentCore health check endpoints:

### Health Check
```bash
GET /health
# Response: {"status": "healthy", "agent": "nova-act-browser-agent", "version": "1.0.0"}
```

### Readiness Check
```bash
GET /ready
# Response: {"ready": true, "agent": "nova-act-browser-agent"}
```

## Request/Response Flow

### 1. Lambda Tool receives request
```json
{
  "name": "browser_broadband",
  "input": {
    "postcode": "SW1A 1AA"
  }
}
```

### 2. Lambda retrieves credentials from Secrets Manager
```python
credentials = get_tool_credentials("browser_broadband")
# /agentcore/browser/browser_broadband/credentials-prod
```

### 3. Lambda invokes AgentCore with enriched payload
```json
{
  "input": {
    "postcode": "SW1A 1AA",
    "credentials": {
      "username": "user@example.com",
      "password": "password"
    }
  }
}
```

### 4. AgentCore runtime invokes container
```http
POST /invoke
Content-Type: application/json

{
  "input": {
    "postcode": "SW1A 1AA",
    "credentials": {...}
  }
}
```

### 5. Agent processes request and returns result
```json
{
  "success": true,
  "data": {
    "results": {
      "max_download_speed_mbps": 1000,
      "availability": "Available"
    }
  }
}
```

## Implementation Status

### Current State
- ✅ Container structure
- ✅ Health check endpoints
- ✅ Multi-agent type support
- ✅ Credentials handling
- ✅ Mock responses

### TODO
- ⏳ Actual Nova Act browser automation
- ⏳ Error handling and retry logic
- ⏳ Logging and telemetry
- ⏳ Performance optimization

## Extending the Agent

### Adding a New Agent Type

1. **Add handler function** in `simple_nova_agent.py`:
```python
def handle_new_type(body: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    # Your implementation
    pass
```

2. **Route in main handler**:
```python
if agent_type == "new_type":
    result = handle_new_type(body, credentials)
```

3. **Update CDK** to deploy new runtime with `AGENT_TYPE=new_type`

4. **Register tool** in `agentcore_browser_tool_stack.py`

## Troubleshooting

### Container fails to start
- Check CloudWatch Logs for AgentCore runtime
- Verify health check endpoint responds
- Check `AGENT_TYPE` environment variable

### Agent not receiving credentials
- Verify secret exists in Secrets Manager
- Check Lambda IAM permissions for `secretsmanager:GetSecretValue`
- Enable debug logging in Lambda

### Old code being used
- Rebuild and push container: `make build-agentcore-containers`
- AgentCore runtimes automatically pick up new images
- No CDK redeployment needed

## Architecture

```
Step Functions Agent
    ↓
Lambda Tool (agentcore_browser)
    ↓ (retrieves credentials)
Secrets Manager
    ↓
AgentCore Runtime
    ↓ (invokes container)
Browser Agent Container
    ↓ (uses Nova Act)
Web Browser Automation
```

## References

- [AgentCore Documentation](docs/AGENTCORE_CHAIN_ARCHITECTURE.md)
- [Deployment Guide](docs/AGENTCORE_BROWSER_AGENT_GUIDE.md)
- [Quick Reference](docs/AGENTCORE_QUICK_REFERENCE.md)
