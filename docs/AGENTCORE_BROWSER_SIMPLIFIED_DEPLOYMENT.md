# AgentCore Browser Tool - Simplified Deployment Guide

## Overview

This guide describes the simplified deployment workflow for AgentCore browser automation tools using Nova Act. This approach uses CDK for stable components (CodeBuild, Lambda) and manual deployment via the AgentCore starter toolkit for runtime management.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Manual Deployment (AgentCore Starter Toolkit)          │
├─────────────────────────────────────────────────────────┤
│ • AgentCore Runtimes (ARM64 containers)                │
│ • Uses bedrock-agentcore CLI                           │
│ • Stable and proven approach                            │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ invokes via ARN
                        │
┌─────────────────────────────────────────────────────────┐
│ CDK-Managed Infrastructure                              │
├─────────────────────────────────────────────────────────┤
│ • CodeBuild project (builds ARM64 containers)          │
│ • Lambda function (agentcore-browser-tool)             │
│ • Tool registration with Step Functions                │
│ • Secrets management (Nova Act API key)                │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ builds
                        │
┌─────────────────────────────────────────────────────────┐
│ Source Code (Easy to Modify)                           │
├─────────────────────────────────────────────────────────┤
│ • instructions/ - Browser automation YAML files        │
│ • simple_nova_agent.py - Agent handler                 │
│ • Dockerfile - ARM64 container with Chrome             │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **AgentCore Starter Toolkit installed**:
   ```bash
   pip install bedrock-agentcore
   ```
3. **Nova Act API key** stored in AWS Secrets Manager at `/ai-agent/tool-secrets/prod`
4. **Docker** (optional, for local testing)

## Project Structure

```
lambda/tools/agentcore_browser/agents/
├── instructions/              # Browser automation YAML files
│   ├── broadband/            # UK broadband checker instructions
│   ├── browse/               # General web browsing
│   └── forms/                # Form filling examples
├── nova_act_agent/           # Nova Act integration code
├── simple_nova_agent.py      # Main agent handler
├── Dockerfile                # ARM64 container definition
├── requirements.txt          # Python dependencies
└── buildspec.yml            # CodeBuild configuration
```

## Deployment Workflow

### Step 1: Build Containers with CodeBuild

Build all three agent containers (broadband, shopping, search) using AWS CodeBuild:

```bash
make build-agentcore-containers-codebuild ENV_NAME=prod AWS_REGION=us-west-2
```

This will:
- Package the agent code into a zip file
- Upload to S3
- Trigger CodeBuild to build ARM64 containers
- Push containers to ECR with `:latest` tag

**Built containers:**
- `bedrock-agentcore-cdk_broadband_checker_agent:latest`
- `bedrock-agentcore-cdk_shopping_agent:latest`
- `bedrock-agentcore-cdk_web_search_agent:latest`

### Step 2: Deploy AgentCore Runtimes Manually

Use the AgentCore starter toolkit to deploy each runtime:

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-west-2

# Deploy Broadband Checker Agent
bedrock-agentcore deploy-runtime \
  --runtime-name cdk_broadband_checker_agent \
  --container-uri ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/bedrock-agentcore-cdk_broadband_checker_agent:latest \
  --network-mode PUBLIC \
  --protocol HTTP \
  --region ${AWS_REGION}

# Deploy Shopping Agent
bedrock-agentcore deploy-runtime \
  --runtime-name cdk_shopping_agent \
  --container-uri ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/bedrock-agentcore-cdk_shopping_agent:latest \
  --network-mode PUBLIC \
  --protocol HTTP \
  --region ${AWS_REGION}

# Deploy Web Search Agent
bedrock-agentcore deploy-runtime \
  --runtime-name cdk_web_search_agent \
  --container-uri ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/bedrock-agentcore-cdk_web_search_agent:latest \
  --network-mode PUBLIC \
  --protocol HTTP \
  --region ${AWS_REGION}
```

**Or use the Makefile helper:**

```bash
make deploy-agentcore-runtimes-manual ENV_NAME=prod AWS_REGION=us-west-2
```

### Step 3: Get Runtime ARNs

After deployment, get the runtime ARNs and update your Lambda function environment variables:

```bash
# List all runtimes
bedrock-agentcore list-runtimes --region us-west-2

# Get specific runtime ARN
bedrock-agentcore describe-runtime \
  --runtime-name cdk_broadband_checker_agent \
  --region us-west-2 \
  --query 'runtimeArn' \
  --output text
```

### Step 4: Update Lambda Environment Variables

Update the Lambda function with the runtime ARNs:

```bash
aws lambda update-function-configuration \
  --function-name agentcore-browser-tool-prod \
  --environment Variables='{
    "BROADBAND_AGENT_ARN": "arn:aws:bedrock-agentcore:us-west-2:ACCOUNT:runtime/cdk_broadband_checker_agent-XXXXX",
    "SHOPPING_AGENT_ARN": "arn:aws:bedrock-agentcore:us-west-2:ACCOUNT:runtime/cdk_shopping_agent-XXXXX",
    "SEARCH_AGENT_ARN": "arn:aws:bedrock-agentcore:us-west-2:ACCOUNT:runtime/cdk_web_search_agent-XXXXX"
  }' \
  --region us-west-2
```

**Or use the Makefile helper to auto-discover and update:**

```bash
make update-agentcore-lambda-arns ENV_NAME=prod AWS_REGION=us-west-2
```

## Modifying Browser Instructions

### Adding New Browser Automation Tasks

1. **Create a new instruction file** in `instructions/` directory:

```yaml
# instructions/my_task/custom_action.yaml
description: "Description of what this does"
url: "https://example.com"
steps:
  - action: navigate
    target: "https://example.com/page"
  - action: fill
    selector: "#search-input"
    value: "{query}"
  - action: click
    selector: "button[type='submit']"
  - action: wait
    duration: 2000
  - action: extract
    selector: ".results"
    name: "results"
```

2. **Update the agent handler** (if needed) in `simple_nova_agent.py`

3. **Rebuild and redeploy**:
```bash
make build-agentcore-containers-codebuild ENV_NAME=prod
make update-agentcore-runtimes-manual ENV_NAME=prod
```

### Modifying Existing Instructions

Simply edit the YAML files in `instructions/` and rebuild:

```bash
# Edit the file
vim lambda/tools/agentcore_browser/agents/instructions/broadband/bt_checker.yaml

# Rebuild containers
make build-agentcore-containers-codebuild ENV_NAME=prod

# Runtimes will automatically pull new :latest tag on next cold start
# Or force update manually:
make update-agentcore-runtimes-manual ENV_NAME=prod
```

## Adding a New Browser Tool

To add a completely new browser-based tool:

1. **Add new agent type** in `simple_nova_agent.py`:

```python
def handle_my_new_tool(body: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Handle my new browser automation task"""
    agent = NovaActAgent()
    task = {
        "url": body.get("url"),
        "instructions": "Do something...",
        "extract_data": ["field1", "field2"]
    }
    result = agent.execute(task)
    return {
        "success": result.get("success"),
        "data": result.get("extracted_data")
    }
```

2. **Add routing** in the handler:

```python
if agent_type == "my_new_tool":
    result = handle_my_new_tool(event, credentials)
```

3. **Create new ECR repository**:

```bash
aws ecr create-repository \
  --repository-name bedrock-agentcore-my_new_tool \
  --region us-west-2
```

4. **Update buildspec** or Makefile to build new container

5. **Deploy new runtime**:

```bash
bedrock-agentcore deploy-runtime \
  --runtime-name cdk_my_new_tool \
  --container-uri ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/bedrock-agentcore-my_new_tool:latest \
  --network-mode PUBLIC \
  --protocol HTTP \
  --region ${AWS_REGION}
```

6. **Update Lambda** to include new runtime ARN

## Testing

### Test Locally (Optional)

Build and run the container locally:

```bash
cd lambda/tools/agentcore_browser/agents

# Build for ARM64 (if on ARM Mac) or AMD64 (for local testing)
docker build --platform linux/arm64 -t agentcore-browser-test .

# Run locally
docker run -p 8080:8080 \
  -e AGENT_TYPE=broadband \
  -e AWS_REGION=us-west-2 \
  -e NOVA_ACT_API_KEY=your-key \
  agentcore-browser-test

# Test health check
curl http://localhost:8080/ping

# Test invocation
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": {"postcode": "E8 4LX", "building_number": "13"}}'
```

### Test in AWS

Use the Lambda test console or AWS CLI:

```bash
aws lambda invoke \
  --function-name agentcore-browser-tool-prod \
  --payload '{"id":"test1","name":"browser_broadband","input":{"postcode":"E8 4LX","building_number":"13"}}' \
  --region us-west-2 \
  response.json

cat response.json | jq
```

## Troubleshooting

### Container Won't Start

Check CloudWatch logs:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/cdk_broadband_checker_agent-XXXXX-DEFAULT \
  --follow --region us-west-2
```

### Architecture Mismatch

Ensure containers are built for ARM64:
```bash
# Check buildspec.yml has: --platform linux/arm64
grep "platform" lambda/tools/agentcore_browser/agents/buildspec.yml
```

### Runtime Not Found

List all runtimes:
```bash
bedrock-agentcore list-runtimes --region us-west-2
```

### Nova Act API Key Issues

Verify secret exists and has correct format:
```bash
aws secretsmanager get-secret-value \
  --secret-id /ai-agent/tool-secrets/prod \
  --region us-west-2 \
  --query SecretString \
  --output text | jq .browser_broadband
```

## Maintenance

### Updating to Latest Nova Act Version

1. Update `requirements.txt`:
```
nova-act>=1.1.0
```

2. Rebuild containers:
```bash
make build-agentcore-containers-codebuild ENV_NAME=prod
```

3. Runtimes auto-update on next invocation or force update manually

### Cleaning Up Old Images

```bash
# List images
aws ecr describe-images \
  --repository-name bedrock-agentcore-cdk_broadband_checker_agent \
  --region us-west-2

# Delete untagged images
aws ecr batch-delete-image \
  --repository-name bedrock-agentcore-cdk_broadband_checker_agent \
  --image-ids imageDigest=sha256:... \
  --region us-west-2
```

## Why This Approach?

**Advantages:**
- ✅ **Stable**: Uses proven AgentCore starter toolkit
- ✅ **Simple**: No complex CDK runtime management
- ✅ **Fast iteration**: Easy to modify instructions and rebuild
- ✅ **Production-ready**: No CloudFormation stuck states
- ✅ **Future-proof**: Easy to migrate to CDK when it matures

**When to Use CDK for Runtimes:**
- When AWS CDK support for BedrockAgentCore::Runtime is more mature
- When you need infrastructure-as-code for compliance/audit
- When you have many environments to manage

## Additional Resources

- [AgentCore Starter Toolkit Documentation](https://github.com/awslabs/bedrock-agentcore-starter-toolkit)
- [Nova Act Documentation](https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova-act.html)
- [AgentCore Runtime Service Contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-service-contract.html)
