# Amplify Backend Architecture

## Overview
This Amplify application provides the management UI for the Step Functions Agent Framework. It follows a clear separation of concerns:

- **Core CDK Application**: Manages all AI agent infrastructure (agents, tools, registries)
- **Amplify UI Application**: Provides management interface and API access layer

## Resource Discovery Strategy

### Production and Dev Environments
- References existing DynamoDB tables from Core CDK by predictable names
- Tables must exist before Amplify deployment
- Uses pattern: `{TableName}-{Environment}`

### Sandbox Environments
- Can create local lightweight tables for isolated development
- Allows UI development without Core CDK deployment
- Tables are automatically destroyed when sandbox is terminated

## Deployment Strategies

### 1. Production Deployment (via Amplify Hosting)
```bash
# Core CDK must be deployed first
cd /Users/guy/projects/step-functions-agent
ENVIRONMENT=prod make deploy-all

# Then deploy Amplify via GitHub push
git push origin main
```

### 2. Development Environment
```bash
# Deploy Core CDK for dev
cd /Users/guy/projects/step-functions-agent
ENVIRONMENT=dev make deploy-all

# Run Amplify sandbox connected to dev tables
cd ui_amplify
make sandbox-dev  # Creates .amplify-env with "dev"
```

### 3. Isolated Sandbox (Local Tables)
```bash
# No Core CDK required
cd ui_amplify
make sandbox  # Creates .amplify-env with "sandbox-{USER}"
```

### 4. Sandbox with Existing Tables
```bash
# If Core CDK is deployed for your sandbox
cd /Users/guy/projects/step-functions-agent
ENVIRONMENT=sandbox-guy make deploy-all

# Then run Amplify with existing tables
cd ui_amplify
USE_EXISTING_TABLES=true make sandbox
```

## Environment Configuration

### Environment Detection
1. Checks `.amplify-env` file (created by Makefile)
2. Falls back to `sandbox-{USER}` if file doesn't exist

### Table Strategy Control
- `USE_EXISTING_TABLES=true`: Force use of existing Core CDK tables
- Default behavior:
  - `prod` → Use existing tables
  - `dev` → Use existing tables
  - `sandbox-*` → Create local tables

## Resource Naming Conventions

All resources follow predictable naming patterns:

| Resource | Pattern | Example |
|----------|---------|---------|
| AgentRegistry | `AgentRegistry-{env}` | `AgentRegistry-prod` |
| ToolRegistry | `ToolRegistry-{env}` | `ToolRegistry-dev` |
| MCPServerRegistry | `MCPServerRegistry-{env}` | `MCPServerRegistry-sandbox-guy` |
| ToolSecrets | `ToolSecrets-{env}` | `ToolSecrets-prod` |
| TestEvents | `TestEvents-{env}` | `TestEvents-dev` |
| TestResults | `TestResults-{env}` | `TestResults-sandbox-guy` |
| LLMModels (UI only) | `LLMModels-UI-{env}` | `LLMModels-UI-prod` |

## Benefits of This Approach

1. **Flexible Deployment**: Works with both Amplify Hosting and local sandbox
2. **No Hard Dependencies**: Amplify can deploy independently for sandboxes
3. **Clear Separation**: Core infrastructure vs UI concerns
4. **Predictable Names**: No need for CloudFormation exports
5. **Environment Isolation**: Each environment has separate resources

## Troubleshooting

### Tables Not Found Error
If you get "Table does not exist" errors:
1. Check if Core CDK is deployed: `aws dynamodb list-tables`
2. Verify environment suffix matches: Check `.amplify-env` file
3. For sandbox, let it create local tables: Don't set `USE_EXISTING_TABLES`

### Permission Errors
Lambda functions need permissions to access tables:
- Production/Dev: IAM roles from Core CDK should have access
- Sandbox: Local tables grant permissions automatically

### Environment Mismatch
Ensure environment names match between:
- Core CDK: `ENVIRONMENT` variable
- Amplify: `.amplify-env` file content
- Resources will have suffix matching environment

## Migration Path

For existing deployments:
1. Core CDK continues to work unchanged
2. Amplify UI references existing tables by name
3. No CloudFormation export dependencies
4. Sandbox developers can work independently