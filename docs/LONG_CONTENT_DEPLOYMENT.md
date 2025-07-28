# Long Content Support Deployment Guide

This guide explains how to deploy and configure long content support for Step Functions agents, including resource sharing with existing infrastructure.

## Overview

Long content support allows Step Functions to handle messages larger than the 256KB limit by:
1. Using Lambda Runtime API Proxy extension to intercept large messages
2. Storing large content in DynamoDB 
3. Passing references instead of actual content through Step Functions
4. Transparently retrieving content when needed

The infrastructure supports flexible deployment with resource sharing capabilities.

## Architecture Components

### 1. Lambda Extension Layer Stack (`LambdaExtensionLayerStack`)
- **Purpose**: Builds the Lambda Runtime API Proxy extension using Rust
- **Creates**: Lambda layers for both x86_64 and ARM64 architectures
- **Build Process**: Uses Makefile-based build for consistency (replaced CodeBuild approach)
- **Exports**: 
  - `SharedProxyLayerX86ExtensionBuild-{env}`
  - `SharedProxyLayerArmExtensionBuild-{env}`

### 2. Shared Long Content Infrastructure (`SharedLongContentInfrastructureStack`)
- **Purpose**: Core DynamoDB storage and layer management
- **DynamoDB Table**: `AgentContext-{env}` with TTL and point-in-time recovery
- **Re-exports**: Proxy layers with LongContent naming convention
- **Exports**:
  - `SharedContentTableLongContent-{env}`
  - `SharedContentTableArnLongContent-{env}`
  - `SharedProxyLayerX86LongContent-{env}`
  - `SharedProxyLayerArmLongContent-{env}`

### 3. Shared LLM with Long Content (`SharedLLMWithLongContentStack`)
- **Purpose**: LLM Lambda functions with proxy extension support
- **Key Features**:
  - ARM64 architecture with correct layer selection
  - Imports existing secrets instead of creating new ones
  - Environment variables for 500-character threshold
  - Direct role creation to handle imported secrets properly

### 4. Tool Stacks with Long Content
- **Example**: `SqlWithLongContentToolStack`
- **Key Learnings**:
  - Must use `PythonFunction` for dependency management (pandas, etc.)
  - Architecture must match extension layer (x86_64 or ARM64)
  - Uses actual tool code (e.g., db-interface) with proxy layer added
  - Tool registry registration with `BaseToolConstruct`

### 5. Agent Stacks with Long Content
- **Example**: `SqlWithLongContentAgentStack`
- **Key Features**:
  - Inherits from `FlexibleLongContentAgentStack`
  - Uses `AgentRegistryMixin` for code reuse
  - Agent registry requires composite key (agent_name + version)
  - CloudWatch permissions needed for Step Functions metrics

## Key Troubleshooting Lessons

### Architecture Mismatch Issues
- **Problem**: "cannot execute binary file" errors
- **Cause**: Lambda function architecture doesn't match extension layer architecture
- **Solution**: Ensure Lambda and layer use same architecture (ARM64 or x86_64)
- **Example**: ARM64 Lambda must use ARM64 extension layer

### Agent Registry Deletion Issues
- **Problem**: "The provided key element does not match the schema"
- **Cause**: Custom resource trying to delete with incomplete key
- **Solution**: Agent registry uses composite key (agent_name + version)
- **Fix**: Update `BaseAgentConstruct` to include both keys in delete operation

### Import Secret Issues  
- **Problem**: IAM permissions failed for imported secrets
- **Cause**: `from_secret_name_v2` doesn't provide proper ARN for permissions
- **Solution**: Create IAM role directly with wildcard secret ARN pattern
- **Pattern**: `arn:aws:secretsmanager:{region}:{account}:secret:/ai-agent/llm-secrets/{env}*`

### Dependency Management
- **Problem**: "No module named 'pandas'" errors
- **Cause**: Using `Code.from_asset` doesn't install Python dependencies
- **Solution**: Use `PythonFunction` which automatically handles requirements.txt

### Tool Registry Schema
- **Important**: ToolRegistry uses single key (tool_name), AgentRegistry uses composite key
- **Versioning**: Currently not used for tools, but implemented for agents
- **Tool Names**: Use simple names like `get_db_schema`, `execute_sql_query`

## Prerequisites

- AWS CDK installed
- Rust toolchain with `cargo-lambda`
- Python 3.9+
- AWS credentials configured

## Deployment Options

### Standalone Deployment (Default)
Deploy all long content resources together:

```bash
cdk deploy --all --app 'python long_content_app.py' --profile YOUR_PROFILE
```

### Resource Sharing with Existing Infrastructure

The long content stacks support reusing existing agent and tool registries from your main infrastructure. This is accomplished through direct code configuration:

#### Reusing Agent Registry

In `long_content_app.py`, all agents are configured to use the existing agent registry:

```python
agent_config = {
    "use_agent_registry": True,  # Use existing agent registry
    "import_registry_from": None  # Will use standard export name
}
```

#### Reusing Tool Registry

Tool stacks are configured to import the existing tool registry:

```python
tool_config = {
    "use_tool_registry": True,  # Use existing tool registry
    "import_from_exports": True  # Import from CloudFormation exports
}
```

### Custom Resource Sharing

For more advanced scenarios, you can directly modify the stack code to import specific resources:

```python
# Example: Import specific agent registry by name
self.agent_registry_table = dynamodb.Table.from_table_name(
    self,
    "ImportedAgentRegistry",
    "agent-registry-prod"  # Your existing table name
)

# Example: Import LLM function by ARN
self.llm_function = lambda_.Function.from_function_arn(
    self,
    "ImportedLLM",
    "arn:aws:lambda:us-east-1:123456789:function:claude-llm-prod"
)
```

## Configuration Options

### Content Size Thresholds

Configure when content is stored in DynamoDB vs passed directly:

```python
# For testing - use low threshold to trigger extension easily
max_content_size=500  # 500 characters - good for testing

# For production - use higher thresholds
max_content_size=8000   # 8KB threshold
max_content_size=50000  # 50KB threshold for large datasets
```

**Testing Recommendation**: Start with 500 characters to easily test the long content functionality with simple database schemas or query results.

### Environment Variables

The proxy extension uses these environment variables:
- `AWS_LAMBDA_EXEC_WRAPPER`: Points to the proxy wrapper script
- `AGENT_CONTEXT_TABLE`: DynamoDB table name for content storage
- `MAX_CONTENT_SIZE`: Size threshold for content transformation
- `LRAP_DEBUG`: Enable debug logging (set to "true")

## Deployment Steps

### 1. Deploy Extension Layer Stack
```bash
cdk deploy LambdaExtensionLayerStack-dev --app 'python long_content_app.py'
```

### 2. Deploy Shared Infrastructure
```bash
cdk deploy SharedLongContentInfrastructure-dev --app 'python long_content_app.py'
```

### 3. Deploy LLM Stack
```bash
cdk deploy SharedLLMWithLongContent-dev --app 'python long_content_app.py'
```

### 4. Deploy Tool Stacks
```bash
cdk deploy WebScraperLongContentTools-dev SqlLongContentTools-dev --app 'python long_content_app.py'
```

### 5. Deploy Agent Stacks
```bash
cdk deploy WebScraperLongContentAgent-dev SqlLongContentAgent-dev --app 'python long_content_app.py'
```

### Or deploy all at once:
```bash
cdk deploy --all --app 'python long_content_app.py' --profile YOUR_PROFILE
```

## Verifying Deployment

1. Check Lambda functions have the proxy extension layer attached
2. Verify environment variables are set correctly
3. Test with large content to ensure DynamoDB storage works
4. Monitor CloudWatch logs for proxy extension activity

## Troubleshooting

### Build Failures
- Ensure Rust and cargo-lambda are installed
- Check Makefile exists in `lambda/extensions/long-content`
- Verify Docker is running for CDK bundling

### Runtime Issues
- Enable `LRAP_DEBUG=true` for detailed logging
- Check DynamoDB table permissions
- Verify content size thresholds are appropriate
- Monitor Lambda memory and timeout settings

### Resource Import Issues
- Ensure main infrastructure stacks export required resources
- Verify export names match import expectations
- Check CloudFormation export limits (200 per region)

## Best Practices

1. **Content Size Thresholds**: Set appropriately based on your data
   - Too low: Unnecessary DynamoDB operations
   - Too high: Risk hitting Step Functions limits

2. **TTL Configuration**: Set DynamoDB TTL based on workflow duration
   - Default: 24 hours
   - Adjust based on longest expected workflow time

3. **Architecture Selection**: Match Lambda architecture to workload
   - ARM64: Better price/performance for most workloads
   - x86_64: Required for specific dependencies

4. **Resource Sharing**: Reuse existing resources when possible
   - Reduces deployment time
   - Maintains consistency
   - Simplifies management

5. **Monitoring**: Set up CloudWatch alarms for:
   - DynamoDB throttling
   - Lambda errors
   - Content size metrics

## Developer-Focused Design

The long content support is designed for developers who prefer direct code modification over complex configuration:

1. **No Complex Config Files**: Import resources by modifying stack code directly
2. **Clear Patterns**: Follow existing patterns in the codebase
3. **Type Safety**: Use CDK's type system to prevent errors
4. **Flexibility**: Mix and match resources as needed

## Integration with Main Infrastructure

The long content stacks are designed to work seamlessly with the main Step Functions agent infrastructure:

- **Agent Registry**: Automatically imports from main infrastructure
- **Tool Registry**: Reuses existing tool definitions
- **LLM Functions**: Creates new LLM functions with long content support (not shared)
- **Monitoring**: Integrates with existing CloudWatch dashboards