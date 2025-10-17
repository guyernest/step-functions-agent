# AgentCore Browser Tool - CDK Migration Guide

## Overview

This document describes the migration from CLI-based AgentCore deployment (using `agentcore launch`) to CDK-based infrastructure-as-code deployment.

## Background

### Previous Approach (CLI-based)

The browser automation agents were previously deployed using the AWS Bedrock AgentCore starter toolkit:

- **Deployment Method**: Manual `agentcore launch` CLI command
- **Configuration**: `.bedrock_agentcore.yaml` file
- **Location**: Separate `nova-act` project
- **Agent ARNs**: Hardcoded in `agent_config.py`
- **Build Process**: Custom buildspec.yml with CodeBuild
- **Pros**: Simple for quick prototyping
- **Cons**: Not infrastructure-as-code, manual steps, configuration drift

### New Approach (CDK-based)

All AgentCore deployments are now managed through AWS CDK:

- **Deployment Method**: `cdk deploy` via Makefile
- **Configuration**: CDK constructs in TypeScript/Python
- **Location**: Integrated in `step-functions-agent` project
- **Agent ARNs**: Dynamically passed via environment variables
- **Build Process**: Automated Docker build with ECR push
- **Pros**: Infrastructure-as-code, automated, version-controlled
- **Cons**: More complex initial setup

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS CDK App (app.py)                     │
└──────────────┬──────────────────────────────────┬───────────┘
               │                                  │
               ▼                                  ▼
    ┌──────────────────────────┐    ┌──────────────────────────┐
    │ AgentCoreBrowserRuntime  │    │ AgentCoreBrowserTool     │
    │        Stack             │    │        Stack             │
    └──────────────────────────┘    └──────────────────────────┘
               │                                  │
               │ Creates 3 runtimes               │ Creates Lambda
               ├──────────────┐                   │
               ▼              ▼                   ▼
    ┌─────────────────┐  ┌────────┐   ┌──────────────────────┐
    │ ECR Repository  │  │ IAM    │   │ Lambda Function      │
    │ (ARM64 images)  │  │ Roles  │   │ Routes to agents     │
    └─────────────────┘  └────────┘   └──────────────────────┘
               │              │                   │
               ▼              ▼                   ▼
    ┌─────────────────────────────────────────────────────────┐
    │          AWS Bedrock AgentCore Service                  │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
    │  │ Broadband    │  │ Shopping     │  │ Search       │ │
    │  │ Agent        │  │ Agent        │  │ Agent        │ │
    │  └──────────────┘  └──────────────┘  └──────────────┘ │
    └─────────────────────────────────────────────────────────┘
```

### Stack Responsibilities

#### 1. `AgentCoreBrowserRuntimeStack`

Creates AgentCore runtime infrastructure:
- ECR repositories for Docker images
- IAM execution roles with Bedrock permissions
- CfnRuntime resources for each agent
- Outputs agent ARNs for Lambda consumption

**File**: `stacks/mcp/agentcore_browser_runtime_stack.py`

#### 2. `AgentCoreBrowserToolStack`

Creates Lambda tool for routing:
- Lambda function with AgentCore invocation permissions
- Environment variables with agent ARNs
- DynamoDB tool registry entries
- IAM permissions for S3 (browser recordings)

**File**: `stacks/tools/agentcore_browser_tool_stack.py`

#### 3. `AgentCoreRuntimeConstruct` (Reusable)

Reusable L2-like construct that encapsulates:
- ECR repository creation
- IAM role with AgentCore permissions
- CfnRuntime deployment
- CloudFormation outputs

**File**: `stacks/shared/agentcore_runtime_construct.py`

## Deployment Process

### Prerequisites

1. **AWS CLI configured** with proper credentials
2. **Docker installed** with ARM64 support (for Apple Silicon Macs or Linux ARM)
3. **CDK installed**: `npm install -g aws-cdk`
4. **Profile configured**: `assume CGI-PoC` (or your AWS profile)

### Step-by-Step Deployment

#### 1. Deploy Runtime Infrastructure

```bash
make deploy-agentcore-runtime ENV_NAME=prod
```

This creates:
- ECR repositories for the 3 agents
- AgentCore runtime placeholders (no containers yet)
- IAM roles and permissions

**Output**: ECR repository URIs printed to console

#### 2. Build and Push Containers

```bash
make build-agentcore-containers ENV_NAME=prod
```

This:
- Retrieves ECR repository URIs from CloudFormation
- Logs in to ECR
- Builds ARM64 Docker image from nova-act/agent_core
- Tags and pushes to all 3 repositories

**Note**: Currently uses the same container for all 3 agents. In the future, each agent will have its own specialized container.

#### 3. Deploy Lambda Tool

```bash
make deploy-agentcore-tool ENV_NAME=prod
```

This:
- Imports agent ARNs from runtime stack
- Creates Lambda with environment variables
- Registers 3 tools in DynamoDB:
  - `browser_broadband`
  - `browser_shopping`
  - `browser_search`

#### 4. Full Deployment (All Steps)

```bash
make deploy-agentcore-full ENV_NAME=prod
```

Runs all three steps in sequence.

### Testing

```bash
# Test Lambda invocation
make test-agentcore-browser ENV_NAME=prod

# View Lambda logs
make logs-agentcore-browser ENV_NAME=prod
```

## Migration from Legacy Deployment

### For Existing Deployments

If you have agents deployed via `agentcore launch`:

1. **Keep existing agents running** (no downtime)
2. Deploy new CDK-managed agents with the same agent names
3. CDK will create new runtime instances
4. Test new deployment thoroughly
5. Update Lambda environment variable `USE_DYNAMIC_AGENT_ARNS=true`
6. Verify Lambda uses new agents
7. Decommission old agents manually via AWS Console

### Configuration Comparison

#### Old: `.bedrock_agentcore.yaml`

```yaml
agents:
  broadband_checker_agent:
    name: broadband_checker_agent
    entrypoint: simple_nova_agent.py
    platform: linux/arm64
    aws:
      execution_role: BedrockAgentCoreExecutionRole-xxx
      region: us-west-2
      ecr_repository: bedrock-agentcore-broadband_checker_agent
```

#### New: CDK Construct

```python
AgentCoreRuntimeConstruct(
    self, "BroadbandAgent",
    runtime_name="broadband_checker_agent",
    description="UK broadband availability checker",
    environment_variables={"AWS_REGION": "us-west-2"},
    protocol="HTTP",
    network_mode="PUBLIC",
    create_ecr_repository=True
)
```

### Agent ARN Resolution

The Lambda function now supports two modes:

#### Dynamic Mode (Recommended - CDK)

```python
# Lambda environment variables
USE_DYNAMIC_AGENT_ARNS=true
AGENT_ARN_BROADBAND=arn:aws:bedrock-agentcore:us-west-2:...
AGENT_ARN_SHOPPING=arn:aws:bedrock-agentcore:us-west-2:...
AGENT_ARN_SEARCH=arn:aws:bedrock-agentcore:us-west-2:...
```

The Lambda reads ARNs from environment variables set by CDK.

#### Legacy Mode (Fallback)

```python
# Hardcoded in agent_config.py
AGENT_CONFIGS = {
    'browser_broadband': {
        'agent_id': 'broadband_checker_agent-KcXxkNFCkG',
        'agent_arn_suffix': 'runtime/broadband_checker_agent-KcXxkNFCkG'
    }
}
```

Falls back to hardcoded ARNs if `USE_DYNAMIC_AGENT_ARNS` is not set.

## Container Development

### Current State

All 3 agents currently use the same container from `nova-act/agent_core/simple_nova_agent.py`:

```python
def handler(event, context):
    # Generic handler that echoes requests
    # Health checks on /health and /ready
    # Invocations on /invoke
    return {"statusCode": 200, "body": json.dumps(result)}
```

### Future Development

Each agent should have its own specialized container:

1. **Broadband Agent**: BT Wholesale portal automation
2. **Shopping Agent**: Amazon/eBay product search
3. **Search Agent**: General web scraping

To implement specialized containers:

1. Create agent-specific entrypoints in nova-act project
2. Update `build-agentcore-containers` Makefile target
3. Build separate Docker images for each agent
4. Update container URIs in runtime stack

### Container Requirements

- **Platform**: `linux/arm64` (AWS Graviton)
- **Health endpoint**: `/health` returning 200 OK
- **Readiness endpoint**: `/ready` returning 200 OK
- **Invocation endpoint**: `/invoke` accepting POST with JSON body
- **Port**: 8080 (exposed in Dockerfile)
- **User**: Non-root user (`bedrock_agentcore`)
- **Observability**: OpenTelemetry instrumentation

## Troubleshooting

### Common Issues

#### 1. ECR Repository Not Found

**Error**: "Repository not found during docker push"

**Solution**: Deploy runtime stack first:
```bash
make deploy-agentcore-runtime
```

#### 2. Container Build Fails

**Error**: "platform mismatch" or "exec format error"

**Solution**: Ensure Docker is building for ARM64:
```bash
docker buildx build --platform linux/arm64 ...
```

#### 3. AgentCore Runtime Not Found

**Error**: Lambda logs show "Agent not found"

**Solution**: Check containers are pushed to ECR:
```bash
aws ecr list-images --repository-name bedrock-agentcore-broadband_checker_agent
```

#### 4. Permission Denied

**Error**: "AccessDeniedException when invoking agent"

**Solution**: Verify IAM role has bedrock-agentcore:* permissions:
```bash
aws iam get-role-policy --role-name BedrockAgentCoreRuntime-broadband_checker_agent-prod
```

### Debugging Commands

```bash
# Check CloudFormation stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Get agent ARNs
aws cloudformation describe-stacks \
  --stack-name AgentCoreBrowserRuntimeStack-prod \
  --query 'Stacks[0].Outputs'

# View Lambda environment
aws lambda get-function-configuration \
  --function-name agentcore-browser-tool-prod \
  --query 'Environment.Variables'

# Test agent directly (bypassing Lambda)
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "arn:aws:bedrock-agentcore:..." \
  --payload '{"test": true}'
```

## Benefits of CDK Approach

### Infrastructure as Code

- Version controlled in Git
- Code review for infrastructure changes
- Reproducible deployments across environments

### Automation

- Single command deployment: `make deploy-agentcore-full`
- Automated container builds and ECR pushes
- Dependency management (runtime → containers → Lambda)

### Integration

- Seamless integration with other CDK stacks
- Shared IAM roles and permissions
- Cross-stack references for agent ARNs

### Maintainability

- Reusable constructs (`AgentCoreRuntimeConstruct`)
- Clear separation of concerns
- Documented deployment process

## Next Steps

1. **Specialize Containers**: Create agent-specific Docker images
2. **Add Monitoring**: CloudWatch dashboards for agent performance
3. **Implement Caching**: Cache agent responses for common queries
4. **Add Tests**: Integration tests for agent invocations
5. **Document Agents**: Create agent-specific documentation

## Related Documentation

- [AgentCore Runtime Construct Usage](../stacks/shared/MCP_SERVER_CONSTRUCT_USAGE.md)
- [Lambda Tools Architecture](./LAMBDA_TOOLS_ARCHITECTURE.md)
- [Browser Tool README](../lambda/tools/agentcore_browser/README.md)
- [AWS Bedrock AgentCore Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review CloudWatch logs: `make logs-agentcore-browser`
3. Consult AWS Bedrock AgentCore documentation
4. Review CDK construct source code for detailed implementation
