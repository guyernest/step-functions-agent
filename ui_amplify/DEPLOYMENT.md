# UI Amplify Deployment Guide

## Architecture Overview

The UI Amplify application connects to **Core CDK stacks** which can be deployed to multiple environments (prod, dev, etc.). Each core environment is independent.

**Key Separation**:
- **Core Tables**: AgentRegistry, ToolRegistry, MCPServerRegistry, ToolSecrets (from core-{env})
- **UI Tables**: LLMModels, ExecutionIndex, TestEvents, TestResults (UI-specific)

## Quick Start

### For Production
```bash
# Ensure Core CDK is deployed to prod
cd /Users/guy/projects/step-functions-agent
ENVIRONMENT=prod make deploy-all

# Deploy UI via GitHub push (Amplify Hosting)
git push origin main
```

### For Local Development
```bash
# Default: Connect to core-prod, create isolated UI tables
npx ampx sandbox

# Connect to core-dev instead
CORE_ENV=dev npx ampx sandbox
```

## How It Works

### Environment Variables

**CORE_ENV**: Specifies which core environment to connect to
- Default: `prod`
- Options: `prod`, `dev`, or any deployed core environment
- Controls which core tables (registries) to import

**Examples**:
```bash
# Connect to core-prod (default)
npx ampx sandbox

# Connect to core-dev
CORE_ENV=dev npx ampx sandbox
```

### Table Strategy

**Remote Amplify Builds** (prod, dev):
- Import core tables from matching environment (prod → core-prod, dev → core-dev)
- Import UI tables from matching environment (LLMModels-prod, ExecutionIndex-prod)

**Local Sandbox**:
- Import core tables from specified CORE_ENV (default: prod)
- Create isolated UI tables (LLMModels-sandbox-{user}, ExecutionIndex-sandbox-{user})

This ensures sandbox never conflicts with remote Amplify deployments.

## Common Scenarios

### 1. Test UI Against Production Core
Default behavior - see deployed prod infrastructure:
```bash
npx ampx sandbox
# Core tables: AgentRegistry-prod, ToolRegistry-prod, MCPServerRegistry-prod
# UI tables: LLMModels-sandbox-guy, ExecutionIndex-sandbox-guy
```

### 2. Test UI Against Development Core
Test with dev infrastructure without affecting prod:
```bash
CORE_ENV=dev npx ampx sandbox
# Core tables: AgentRegistry-dev, ToolRegistry-dev, MCPServerRegistry-dev
# UI tables: LLMModels-sandbox-guy, ExecutionIndex-sandbox-guy
```

### 3. Remote Production Deployment
Via Amplify Console (CI/CD):
```bash
git push origin main
# Amplify Console environment variable: CORE_ENV=prod
# Core tables: AgentRegistry-prod, ToolRegistry-prod (imported)
# UI tables: LLMModels-prod, ExecutionIndex-prod (imported)
```

### 4. Remote Development Deployment
Via Amplify Console (CI/CD):
```bash
git push origin dev
# Amplify Console environment variable: CORE_ENV=dev
# Core tables: AgentRegistry-dev, ToolRegistry-dev (imported)
# UI tables: LLMModels-dev, ExecutionIndex-dev (imported)
```

## Environment Reference

| Deployment | CORE_ENV | Core Tables | UI Tables | Use Case |
|------------|----------|-------------|-----------|----------|
| `npx ampx sandbox` | `prod` (default) | AgentRegistry-prod | LLMModels-sandbox-guy | Local dev vs prod |
| `CORE_ENV=dev npx ampx sandbox` | `dev` | AgentRegistry-dev | LLMModels-sandbox-guy | Local dev vs dev |
| Remote prod (Amplify) | `prod` | AgentRegistry-prod | LLMModels-prod | Production |
| Remote dev (Amplify) | `dev` | AgentRegistry-dev | LLMModels-dev | Development |

## Troubleshooting

### Error: "Resource of type 'AWS::DynamoDB::Table' with identifier 'X' already exists"

**Cause**: Trying to create a UI table that already exists (e.g., sandbox creating LLMModels-prod)

**Solution**: Verify CORE_ENV is set correctly and backend.ts uses `uiTableEnvSuffix` for UI tables

### Error: "Table not found" (AgentRegistry-prod)

**Cause**: Core tables don't exist in specified environment

**Solution**: Deploy core stacks first
```bash
cd /Users/guy/projects/step-functions-agent
ENVIRONMENT=prod make deploy-all
```

### Sandbox sees wrong data

**Cause**: Connected to wrong core environment

**Solution**: Set CORE_ENV explicitly
```bash
CORE_ENV=dev npx ampx sandbox
```

### Can't see deployed agents/tools/servers

**Cause**: Core tables empty or connected to wrong environment

**Solution**: Verify core deployment and CORE_ENV
```bash
# Check what's in core-prod
aws dynamodb scan --table-name AgentRegistry-prod --max-items 5
```

## Best Practices

1. **Use CORE_ENV explicitly** - Don't rely on defaults in shared development
2. **Sandbox = isolated UI tables** - Never affects remote Amplify deployments
3. **Deploy core first** - Ensure core-{env} exists before UI deployment
4. **Set Amplify env vars** - Configure CORE_ENV in Amplify Console for remote builds
5. **Parallel development** - Multiple developers can run sandboxes simultaneously

## Summary

The key insight: **Core tables** (registries) are shared/imported, **UI tables** are environment-specific (created for sandbox, imported for remote builds). This allows sandbox to see deployed infrastructure without conflicting with production UI deployments.