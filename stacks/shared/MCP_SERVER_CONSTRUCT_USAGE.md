# MCP Server Construct Usage Guide

## Overview

The `McpServerConstruct` is a reusable CDK construct that enables any MCP server deployment to integrate with the centralized control plane. It provides:

- ✅ **Automatic registration** in DynamoDB registry
- ✅ **CloudWatch observability** (logs, metrics, alarms)
- ✅ **Health monitoring** integration
- ✅ **Tool delegation** IAM permissions
- ✅ **Lifecycle management** (create/update/delete)

**Key Feature:** Control plane integration is **completely optional** - you can deploy MCP servers standalone without using this construct.

## Prerequisites

1. Deploy `MCPRegistryStack` first:
   ```bash
   cd ~/projects/step-functions-agent
   make deploy-mcp-registry ENV=prod
   ```

2. Ensure your MCP server has:
   - AWS Lambda function deployed
   - Function URL or API Gateway endpoint
   - MCP server specification (tools, resources, prompts)

## Basic Usage

### Example: Deploying an MCP Server with Control Plane Integration

```python
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    Duration
)
from constructs import Construct
from stacks.shared.mcp_server_construct import McpServerConstruct


class ReinventMcpStack(Stack):
    """CDK stack for re:Invent MCP Server"""

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 1. Deploy Lambda function
        self.mcp_lambda = _lambda.Function(
            self,
            "ReinventMcpFunction",
            function_name=f"mcp-reinvent-{env_name}",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            handler="bootstrap",
            code=_lambda.Code.from_asset("path/to/bootstrap"),
            timeout=Duration.seconds(30),
            memory_size=512,
            architecture=_lambda.Architecture.ARM_64,
            environment={
                "RUST_LOG": "info",
                "REINVENT_API_KEY": "...",
            }
        )

        # 2. Add Function URL
        fn_url = self.mcp_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )

        # 3. OPTIONAL: Register in control plane
        #    This is completely optional - you can skip this for standalone deployment
        McpServerConstruct(
            self,
            "McpServerRegistration",
            server_id=f"mcp-reinvent-{env_name}",
            version="1.0.0",
            server_name="AWS re:Invent Planner",
            server_spec={
                "description": "Conference planning MCP server with intelligent day planning workflow",
                "protocol_version": "2024-11-05",
                "protocol_type": "jsonrpc",
                "endpoint_url": fn_url.url,
                "health_check_url": fn_url.url.replace("/", "/health"),
                "health_check_interval": 300,

                # MCP capabilities
                "tools": [
                    {
                        "name": "find_sessions",
                        "description": "Find re:Invent sessions with flexible filtering",
                        "implementation": "local",
                        "inputSchema": {...}
                    },
                    {
                        "name": "get_session_details",
                        "description": "Get comprehensive details about a specific session",
                        "implementation": "local",
                        "inputSchema": {...}
                    }
                ],
                "resources": [
                    {
                        "uri": "reinvent://guide/levels",
                        "name": "Session Levels Guide",
                        "description": "Learn about session levels (100/200/300/400/500)",
                        "mimeType": "text/markdown"
                    },
                    # ... more resources
                ],
                "prompts": [
                    {
                        "name": "plan_day_agenda",
                        "description": "Intelligently plan your re:Invent conference day",
                        "arguments": [...]
                    }
                ],

                # Observability configuration
                "traces_enabled": True,
                "log_level": "INFO",

                # Authentication
                "authentication_type": "none",  # or "jwt", "api_key"

                # Metadata
                "metadata": {
                    "team": "platform",
                    "cost_center": "engineering",
                    "tags": ["production", "conference", "planning"]
                }
            },
            lambda_function=self.mcp_lambda,
            env_name=env_name,
            enable_observability=True,       # Enable CloudWatch integration
            enable_health_monitoring=True    # Enable health checks
        )
```

## Advanced: Tool Delegation (Calling Remote Lambda Tools)

Enable your MCP server to call existing Lambda tools from the step-functions-agent infrastructure:

```python
# In your MCP server stack
mcp_registration = McpServerConstruct(
    self,
    "McpServerRegistration",
    server_id=f"mcp-reinvent-{env_name}",
    version="1.0.0",
    server_name="AWS re:Invent Planner",
    server_spec={
        ...
        "tools": [
            # Local MCP tool
            {
                "name": "find_sessions",
                "description": "Find re:Invent sessions",
                "implementation": "local",
                "inputSchema": {...}
            },
            # Remote Lambda tool delegation!
            {
                "name": "execute_sql_query",
                "description": "Execute SQL query against database",
                "implementation": "remote",
                "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:db-interface-tool",
                "inputSchema": {...}
            },
            {
                "name": "research_company",
                "description": "Research company information using AI search",
                "implementation": "remote",
                "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:web-research-tool",
                "inputSchema": {...}
            }
        ]
    },
    ...
)

# Grant permission to invoke remote tools
mcp_registration.add_tool_lambda_permission(
    "execute_sql_query",
    "arn:aws:lambda:us-east-1:123456789012:function:db-interface-tool"
)
mcp_registration.add_tool_lambda_permission(
    "research_company",
    "arn:aws:lambda:us-east-1:123456789012:function:web-research-tool"
)
```

Then in your Rust MCP server code (see `mcp-tool-delegation` crate for implementation):

```rust
// In your MCP server (e.g., mcp-reinvent-core/src/lib.rs)
use mcp_tool_delegation::RemoteLambdaTool;

pub fn build_reinvent_server() -> pmcp::Result<Server> {
    let server = Server::builder()
        // Local tool
        .tool_typed("find_sessions", |args, _| {
            // Local implementation
        })

        // Remote Lambda tool delegation
        .tool_remote(RemoteLambdaTool::new(
            "execute_sql_query",
            env::var("SQL_TOOL_ARN")?,
        )?)

        .tool_remote(RemoteLambdaTool::new(
            "research_company",
            env::var("RESEARCH_TOOL_ARN")?,
        )?)

        .build()?;

    Ok(server)
}
```

## Deployment Patterns

### Pattern 1: Full Control Plane Integration

Best for: Production MCP servers that need centralized management, observability, and tool composition.

```python
McpServerConstruct(
    self, "Registration",
    ...,
    enable_observability=True,
    enable_health_monitoring=True
)
```

**Benefits:**
- Unified dashboard in management UI
- Centralized logs and metrics
- Health monitoring and alerting
- Tool delegation capabilities

### Pattern 2: Standalone Deployment (No Control Plane)

Best for: Development, testing, or independent deployments.

```python
# Simply don't use McpServerConstruct!
# Just deploy Lambda + Function URL

self.mcp_lambda = _lambda.Function(...)
fn_url = self.mcp_lambda.add_function_url(...)

# That's it - pure standalone MCP server
```

**Benefits:**
- No dependencies on control plane infrastructure
- Simpler deployment
- Portable to other platforms (Cloudflare, Docker, etc.)

### Pattern 3: Partial Integration (Observability Only)

Best for: Servers that want observability but not full control plane features.

```python
McpServerConstruct(
    self, "Registration",
    ...,
    enable_observability=True,
    enable_health_monitoring=False
)
```

## Viewing MCP Servers in Management UI

Once registered, your MCP server will appear in the Step Functions Agent Management UI:

1. Navigate to: `https://your-ui-domain.amplifyapp.com/mcp-servers`
2. See all registered MCP servers with:
   - Status and health
   - Available tools, resources, prompts
   - CloudWatch logs link
   - Metrics dashboard
   - Test endpoint functionality

## Environment Variables for Tool Delegation

If using remote tool delegation, pass Lambda ARNs as environment variables:

```python
self.mcp_lambda = _lambda.Function(
    ...,
    environment={
        "SQL_TOOL_ARN": "arn:aws:lambda:...:function:db-interface-tool",
        "RESEARCH_TOOL_ARN": "arn:aws:lambda:...:function:web-research-tool",
    }
)
```

## Observability Features

When `enable_observability=True`:

1. **CloudWatch Logs**: `/mcp-servers/{server_id}`
2. **Metrics Namespace**: `MCP/{ServerName}`
3. **Custom Metrics**:
   - `ToolInvocations` - Total tool calls
   - Lambda standard metrics (errors, duration, throttles)
4. **Alarms**:
   - High error rate (>10 errors in 5 min)
5. **X-Ray Tracing** (if enabled in spec)

## Migration Guide

### From Standalone to Control Plane

1. Deploy control plane infrastructure:
   ```bash
   make deploy-mcp-registry ENV=prod
   ```

2. Add `McpServerConstruct` to your existing stack:
   ```python
   # Add this to your existing MCP server stack
   McpServerConstruct(self, "Registration", ...)
   ```

3. Redeploy your MCP server stack

4. Verify registration in UI

### From Control Plane Back to Standalone

1. Remove `McpServerConstruct` from your stack
2. Redeploy
3. Server continues working independently

## Best Practices

1. **Use Semantic Versioning**: Increment version on breaking changes
2. **Include All Tool Schemas**: Helps UI display capabilities correctly
3. **Set Appropriate Health Check Intervals**: Default 300s (5 min)
4. **Tag Your Servers**: Use metadata for team/cost tracking
5. **Test Tool Delegation Locally**: Before deploying remote tool calls
6. **Monitor CloudWatch Alarms**: Set up SNS notifications

## Troubleshooting

### Server Not Appearing in UI

- Check `MCPRegistryStack` is deployed in same env
- Verify `env_name` matches between stack and registry
- Check CloudFormation events for errors

### Tool Delegation Failing

- Verify Lambda ARN is correct
- Check IAM permissions (use `add_tool_lambda_permission`)
- Ensure environment variables are set

### Health Checks Failing

- Verify `health_check_url` is accessible
- Check Lambda function logs
- Ensure health endpoint returns 200 status

## Next Steps

1. Deploy your MCP server with control plane integration
2. View it in the management UI
3. Test tool delegation with existing Lambda tools
4. Set up CloudWatch alarms for production monitoring
5. Explore creating your own reusable MCP tools

## Related Documentation

- [MCPRegistryStack](./mcp_registry_stack.py) - Control plane infrastructure
- [mcp-tool-delegation crate](TODO) - Rust library for remote tool calling
- [Management UI Guide](TODO) - Using the MCP Servers dashboard
