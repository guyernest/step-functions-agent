# AgentCore Browser Tool - Quick Start

## TL;DR - Simplest Deployment

```bash
# One command to deploy everything!
make deploy-agentcore-browser-tools ENV_NAME=prod AWS_REGION=us-west-2

# Test it
make test-agentcore-broadband ENV_NAME=prod AWS_REGION=us-west-2
```

## What Just Happened?

The `agentcore` CLI automatically:
- ✅ Configured 3 browser agents (broadband, shopping, search)
- ✅ Built ARM64 containers in AWS CodeBuild (no local Docker!)
- ✅ Created ECR repositories and pushed images
- ✅ Deployed AgentCore runtimes
- ✅ Updated Lambda with runtime ARNs

**No manual Docker builds. No architecture issues. Just works.**

## Prerequisites

Install the AgentCore CLI:
```bash
pip install bedrock-agentcore
```

Verify Nova Act API key exists:
```bash
aws secretsmanager get-secret-value \
  --secret-id /ai-agent/tool-secrets/prod \
  --region us-west-2 \
  --query SecretString \
  --output text | jq .browser_broadband
```

## Step-by-Step (If You Want Control)

### 1. Configure Agents (One-Time Setup)

```bash
# Configure all three agents at once
make agentcore-configure-all AWS_REGION=us-west-2

# Or individually:
make agentcore-configure-broadband AWS_REGION=us-west-2
make agentcore-configure-shopping AWS_REGION=us-west-2
make agentcore-configure-search AWS_REGION=us-west-2
```

This creates `.agentcore/config.json` files for each agent.

### 2. Launch Agents (Build + Deploy)

```bash
# Launch all agents (uses CodeBuild automatically!)
make agentcore-launch-all AWS_REGION=us-west-2

# Or launch individually:
make agentcore-launch-broadband AWS_REGION=us-west-2
make agentcore-launch-shopping AWS_REGION=us-west-2
make agentcore-launch-search AWS_REGION=us-west-2
```

Each launch:
- Builds container in CodeBuild (ARM64, ~600MB)
- Pushes to ECR
- Creates/updates AgentCore runtime
- Takes ~3-5 minutes per agent

### 3. Update Lambda with Runtime ARNs

```bash
make update-agentcore-lambda-arns ENV_NAME=prod AWS_REGION=us-west-2
```

This auto-discovers the runtime ARNs and updates the Lambda function.

### 4. Test!

```bash
make test-agentcore-broadband ENV_NAME=prod AWS_REGION=us-west-2
```

## Available Tools

| Tool Name | Agent Type | Example Use |
|-----------|------------|-------------|
| `browser_broadband` | UK broadband checker | Check fiber availability at an address |
| `browser_shopping` | E-commerce search | Find products on Amazon/eBay |
| `browser_search` | General web scraping | Extract data from any website |

## Modifying Browser Instructions

```bash
# 1. Edit the instruction YAML files
vim lambda/tools/agentcore_browser/agents/instructions/broadband/bt_checker.yaml

# 2. Re-launch the agent (rebuilds + redeploys)
make agentcore-launch-broadband AWS_REGION=us-west-2

# Done! New instructions are live in ~3 minutes
```

## Common Commands

```bash
# Check status of all agents
make agentcore-status AWS_REGION=us-west-2

# List all deployed runtimes
make list-agentcore-runtimes AWS_REGION=us-west-2

# Get runtime ARNs
make get-agentcore-runtime-arns AWS_REGION=us-west-2

# View Lambda logs
make tail-agentcore-browser-logs ENV_NAME=prod AWS_REGION=us-west-2

# Full redeploy (if needed)
make deploy-agentcore-browser-tools ENV_NAME=prod AWS_REGION=us-west-2
```

## Testing Each Tool

### Broadband Checker
```bash
aws lambda invoke \
  --function-name agentcore-browser-tool-prod \
  --payload '{"id":"test1","name":"browser_broadband","input":{"postcode":"E8 4LX","building_number":"13"}}' \
  --region us-west-2 \
  response.json && cat response.json | jq
```

### Shopping Search
```bash
aws lambda invoke \
  --function-name agentcore-browser-tool-prod \
  --payload '{"id":"test2","name":"browser_shopping","input":{"query":"laptop","site":"amazon.co.uk","max_results":5}}' \
  --region us-west-2 \
  response.json && cat response.json | jq
```

### Web Search
```bash
aws lambda invoke \
  --function-name agentcore-browser-tool-prod \
  --payload '{"id":"test3","name":"browser_search","input":{"url":"https://example.com","query":"prices","extract_fields":["price","title"]}}' \
  --region us-west-2 \
  response.json && cat response.json | jq
```

## How It Works

```
┌────────────────────────────────────────┐
│ agentcore launch                       │  ← One command!
├────────────────────────────────────────┤
│ 1. Packages your code                  │
│ 2. Triggers CodeBuild (ARM64)          │
│ 3. Builds container with Chrome        │
│ 4. Pushes to ECR                       │
│ 5. Creates AgentCore runtime           │
│ 6. Runtime ready to serve requests     │
└────────────────────────────────────────┘
         ▼
┌────────────────────────────────────────┐
│ Lambda (agentcore-browser-tool)        │
├────────────────────────────────────────┤
│ Routes requests to correct runtime     │
│ based on tool name                     │
└────────────────────────────────────────┘
         ▼
┌────────────────────────────────────────┐
│ AgentCore Runtime Container            │
├────────────────────────────────────────┤
│ • BedrockAgentCoreApp (HTTP server)    │
│ • /ping - Health checks                │
│ • /invocations - Process requests      │
│ • Nova Act + Chrome browser            │
│ • Your instructions (YAML files)       │
└────────────────────────────────────────┘
```

## Architecture Details

**Container (~600MB):**
- Python 3.12 (UV package manager)
- bedrock-agentcore SDK
- Nova Act browser automation
- Playwright Chrome browser
- Your agent code + instructions

**AgentCore Runtime:**
- ARM64 architecture (Graviton)
- Automatic health checks via `/ping`
- HTTP protocol
- Public network mode
- 15-minute session timeout

**Lambda Function:**
- Routes tool requests to runtimes
- Gets runtime ARNs from environment variables
- Handles credentials from consolidated secrets

## Why This Is Better

| Old Approach | New Approach (agentcore CLI) |
|--------------|------------------------------|
| Manual Docker builds | ✅ CodeBuild handles it |
| Architecture confusion (ARM64 vs AMD64) | ✅ Always ARM64 |
| Manual ECR push | ✅ Automatic |
| Manual runtime deployment | ✅ One command |
| CDK CloudFormation issues | ✅ No CDK for runtimes |
| Complex Makefile scripts | ✅ Simple CLI commands |

## Troubleshooting

### "bedrock-agentcore: command not found"
```bash
pip install bedrock-agentcore
```

### "Runtime not found"
```bash
# Check if runtime exists
make agentcore-status AWS_REGION=us-west-2

# Re-launch if needed
make agentcore-launch-broadband AWS_REGION=us-west-2
```

### "Health check failed or timed out"
This means the container didn't start properly. Check:
```bash
# View runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/cdk_broadband_checker_agent-XXXXX-DEFAULT \
  --follow --region us-west-2

# Common causes:
# - Missing bedrock-agentcore in requirements.txt
# - Wrong entrypoint file
# - Missing @app.entrypoint decorator
```

### "Architecture incompatible"
The `agentcore launch` command always builds ARM64. If you see this error, you're not using the CLI properly.

## Adding a New Browser Tool

1. **Edit the agent code** to add a new handler function
2. **Create instruction YAML** files for the new task
3. **Re-launch** the appropriate agent:
   ```bash
   make agentcore-launch-broadband AWS_REGION=us-west-2
   ```
4. **Test** via Lambda

## Local Development (Optional)

Test locally before deploying:
```bash
cd lambda/tools/agentcore_browser/agents

# Run locally
agentcore launch --local --runtime-name cdk_broadband_checker_agent

# Test
agentcore invoke '{"input": {"postcode": "E8 4LX", "building_number": "13"}}' \
  --runtime-name cdk_broadband_checker_agent
```

## Full Documentation

- **This guide** - Quick start and common tasks
- [AGENTCORE_BROWSER_SIMPLIFIED_DEPLOYMENT.md](./AGENTCORE_BROWSER_SIMPLIFIED_DEPLOYMENT.md) - Complete details
- [AgentCore SDK Docs](https://docs.aws.amazon.com/bedrock-agentcore/) - Official AWS documentation

## Summary

The AgentCore CLI makes browser tool deployment incredibly simple:

1. **One-time setup**: `make agentcore-configure-all`
2. **Deploy**: `make agentcore-launch-all`
3. **Update Lambda**: `make update-agentcore-lambda-arns`
4. **Test**: `make test-agentcore-broadband`

That's it! No Docker, no architecture issues, no CloudFormation complexity.
