# MCP Server Deployment Guide - Control Plane Integration

## Overview

This guide walks through deploying MCP servers with control plane integration using the enhanced infrastructure created in `step-functions-agent`.

## Architecture Created

```
Control Plane (step-functions-agent)
├── Enhanced MCPRegistryStack
│   ├── DynamoDB with deployment/observability fields
│   ├── GSIs for deployment_type, health_status queries
│   └── Health monitoring infrastructure
├── McpServerConstruct (reusable)
│   ├── Auto-registration in DynamoDB
│   ├── CloudWatch logs, metrics, alarms
│   └── IAM for tool delegation
└── ReinventMcpStack (example)
    ├── Lambda function (ARM64 Rust)
    ├── Function URL
    └── Control plane registration

MCP Server Code (mcp-template)
└── reinvent-server (Rust)
    ├── Pure MCP logic (portable)
    └── No AWS dependencies
```

## Deployment Steps

### 1. Deploy Enhanced MCP Registry

```bash
cd ~/projects/step-functions-agent

# Deploy the enhanced registry stack (already exists, this updates it)
ENVIRONMENT=prod cdk deploy MCPRegistryStack-prod
```

This creates/updates:
- DynamoDB table: `MCPServerRegistry-prod`
- GSIs for querying by deployment type, health status
- Enhanced schema with observability fields

### 2. Build Reinvent MCP Server

```bash
cd ~/projects/step-functions-agent

# Build the Rust binary and copy to lambda directory
make build-mcp-reinvent
```

This:
- Builds `reinvent-server` for ARM64 Lambda
- Copies bootstrap to `lambda/mcp-servers/reinvent/`
- Ready for CDK deployment

### 3. Deploy Reinvent MCP Stack

```bash
cd ~/projects/step-functions-agent

# Deploy the MCP server with control plane integration
ENVIRONMENT=prod cdk deploy ReinventMcpStack-prod
```

This creates:
- Lambda function: `mcp-reinvent-prod`
- Function URL (public endpoint)
- CloudWatch Log Group: `/mcp-servers/mcp-reinvent-prod`
- Metrics namespace: `MCP/AWSreInventConferencePlanner`
- DynamoDB entry in `MCPServerRegistry-prod`

### 4. Test the Deployment

```bash
# Get the function URL from CloudFormation outputs
aws cloudformation describe-stacks \
  --stack-name ReinventMcpStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text

# Test health endpoint
curl https://<function-url>/health

# Test MCP initialize
curl -X POST https://<function-url> \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'

# Test tools/list
curl -X POST https://<function-url> \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Test find_sessions tool
curl -X POST https://<function-url> \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "find_sessions",
      "arguments": {"query": "serverless", "level": 300, "limit": 3}
    }
  }'
```

### 5. Verify DynamoDB Registration

```bash
# Query the registry
aws dynamodb get-item \
  --table-name MCPServerRegistry-prod \
  --key '{"server_id": {"S": "mcp-reinvent-prod"}, "version": {"S": "1.0.0"}}'

# Or query all active MCP servers
aws dynamodb query \
  --table-name MCPServerRegistry-prod \
  --index-name MCPServersByStatus \
  --key-condition-expression "status = :status" \
  --expression-attribute-values '{":status": {"S": "active"}}'
```

Expected fields in registry:
- `server_id`, `version`, `server_name`, `description`
- `deployment_type`: "aws-lambda"
- `lambda_arn`, `function_url`, `endpoint_url`
- `available_tools`, `available_resources`, `available_prompts` (JSON)
- `health_status`, `health_check_url`, `last_health_check`
- `cloudwatch_log_group`, `metrics_namespace`, `traces_enabled`
- `status`: "active"

### 6. Monitor in CloudWatch

```bash
# View logs
aws logs tail /mcp-servers/mcp-reinvent-prod --follow

# View metrics
aws cloudwatch get-metric-statistics \
  --namespace MCP/AWSreInventConferencePlanner \
  --metric-name ToolInvocations \
  --dimensions Name=ServerName,Value="AWS re:Invent Conference Planner" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## Files Created

### In step-functions-agent:

1. **`stacks/shared/mcp_registry_stack.py`** (enhanced)
   - Added GSIs for deployment_type, health_status
   - Enhanced registry schema
   - Added observability fields

2. **`stacks/shared/mcp_server_construct.py`** (new)
   - Reusable CDK construct for MCP registration
   - CloudWatch observability integration
   - Lifecycle management

3. **`stacks/mcp/reinvent_mcp_stack.py`** (new)
   - Example MCP server stack
   - Demonstrates control plane integration
   - Tool/resource/prompt specifications

4. **`app.py`** (updated)
   - Added import for ReinventMcpStack
   - Added stack instantiation with dependency on MCPRegistryStack

5. **`Makefile`** (updated)
   - `make build-mcp-reinvent` - Build Rust binary
   - `make clean-mcp-reinvent` - Clean artifacts
   - `make build-mcp-all` - Build all MCP servers

## Control Plane Features

### Automatic Registration

When you deploy `ReinventMcpStack`, it automatically:
1. Registers server in DynamoDB with full metadata
2. Sets up CloudWatch logs with retention policy
3. Creates custom metrics namespace
4. Configures error rate alarms
5. Enables X-Ray tracing (if configured)

### Observability

**CloudWatch Logs**: `/mcp-servers/mcp-reinvent-prod`
- Structured JSON logs from Rust server
- 30-day retention
- Searchable/filterable

**CloudWatch Metrics**: `MCP/AWSreInventConferencePlanner`
- `ToolInvocations` - Total tool calls
- Lambda standard metrics (errors, duration, throttles)

**CloudWatch Alarms**:
- High error rate alarm (>10 errors in 5 minutes)

### Tool Delegation (Future)

The infrastructure supports remote tool delegation:
```python
# In CDK stack
registration.add_tool_lambda_permission(
    "execute_sql",
    "arn:aws:lambda:...:function:db-tool"
)
```

```rust
// In Rust MCP server (future with mcp-tool-delegation crate)
use mcp_tool_delegation::RemoteLambdaTool;

server.tool_remote(RemoteLambdaTool::new(
    "execute_sql",
    env::var("SQL_TOOL_ARN")?
)?)
```

## Standalone Deployment (Optional)

To deploy WITHOUT control plane integration:

```python
# In ReinventMcpStack
reinvent_mcp = ReinventMcpStack(
    app,
    f"ReinventMcpStack-{environment}",
    env_name=environment,
    enable_control_plane=False,  # <-- Disable control plane
    ...
)
# Don't add dependency on mcp_registry_stack
```

This deploys pure Lambda + Function URL without DynamoDB registration.

## Next Steps

1. **Deploy the stacks** following steps above
2. **Test functionality** with curl commands
3. **Verify registration** in DynamoDB
4. **Monitor** in CloudWatch
5. **Add more MCP servers** using the same pattern
6. **Extend Management UI** to display MCP servers (Phase 1.3)

## Troubleshooting

### Build Fails
- Check `cargo-lambda` is installed: `cargo install cargo-lambda`
- Verify mcp-template path in Makefile
- Ensure Rust toolchain is up to date

### Deploy Fails
- Check AWS credentials and region
- Verify MCPRegistryStack-prod exists
- Check CDK bootstrap is done

### Registration Not Showing
- Verify stack deployed successfully
- Check CloudFormation custom resource logs
- Ensure `enable_control_plane=True`

### Health Check Fails
- Check Lambda logs
- Verify function is responding
- Test function URL directly

## Architecture Benefits

✅ **Separation**: MCP logic independent of deployment
✅ **Reusability**: McpServerConstruct works for any MCP server
✅ **Observability**: Unified CloudWatch integration
✅ **Flexibility**: Can deploy with or without control plane
✅ **Tool Composition**: Foundation for Lambda tool delegation
✅ **Multi-Platform**: Registry tracks Lambda, Cloudflare, Docker deployments

## Related Documentation

- [MCP Server Construct Usage](./stacks/shared/MCP_SERVER_CONSTRUCT_USAGE.md)
- [MCPRegistryStack](./stacks/shared/mcp_registry_stack.py)
- [ReinventMcpStack](./stacks/mcp/reinvent_mcp_stack.py)
