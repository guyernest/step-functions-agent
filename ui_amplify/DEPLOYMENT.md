# Deployment Guide

## Quick Start

### For Production
```bash
# Ensure Core CDK is deployed
cd /Users/guy/projects/step-functions-agent
ENVIRONMENT=prod make deploy-all

# Deploy UI via GitHub push (Amplify Hosting)
git push origin main
```

### For Local Development
```bash
# Option 1: Isolated Sandbox (creates own tables)
make sandbox

# Option 2: Connected to Dev Environment
make sandbox-dev  # Uses existing dev tables

# Option 3: Connected to Production (BE CAREFUL!)
make sandbox-prod  # Uses existing prod tables
```

## How It Works

### Resource Discovery
The Amplify app uses **predictable naming conventions** to find resources:
- No CloudFormation exports required
- Works with Amplify Hosting deployments
- Tables are referenced by name: `{TableName}-{Environment}`

### Environment Detection
1. Reads `.amplify-env` file (created by Makefile)
2. Determines table strategy based on environment:
   - `prod`/`dev` → Use existing Core CDK tables
   - `sandbox-*` → Create local temporary tables

### Table Strategy
Control with `USE_EXISTING_TABLES` environment variable:
```bash
# Force use of existing tables (Core CDK must be deployed)
USE_EXISTING_TABLES=true make sandbox

# Let sandbox create its own tables (default for sandbox)
make sandbox
```

## Common Scenarios

### 1. Frontend Developer (Isolated)
No need for Core CDK deployment:
```bash
make sandbox
# Works immediately with local tables
```

### 2. Full-Stack Developer (Integrated)
Test with real Core CDK infrastructure:
```bash
# Deploy your sandbox Core CDK
cd ../
ENVIRONMENT=sandbox-$USER make deploy-all

# Run UI connected to your Core CDK
cd ui_amplify
USE_EXISTING_TABLES=true make sandbox
```

### 3. Testing Against Production Data
```bash
make sandbox-prod
# WARNING: This uses production tables!
```

### 4. CI/CD Pipeline
Amplify Hosting automatically:
1. Detects branch (main → prod, develop → dev)
2. Sets environment accordingly
3. Connects to existing Core CDK tables
4. No manual intervention needed

## Environment Reference

| Command | Environment | Tables | Use Case |
|---------|------------|--------|----------|
| `make sandbox` | `sandbox-{USER}` | Creates local | Isolated development |
| `make sandbox-dev` | `dev` | Uses existing | Test with dev data |
| `make sandbox-prod` | `prod` | Uses existing | Debug production |
| `git push main` | `prod` | Uses existing | Production deploy |

## Troubleshooting

### "Table not found" Error
```bash
# Check if Core CDK tables exist
aws dynamodb list-tables | grep -E "AgentRegistry|ToolRegistry"

# If missing, deploy Core CDK first
cd /Users/guy/projects/step-functions-agent
ENVIRONMENT=sandbox-$USER make deploy-all
```

### Wrong Environment
```bash
# Check current environment
cat .amplify-env

# Change if needed
echo "dev" > .amplify-env
make sandbox
```

### Permission Issues
- Sandbox tables: Automatically granted
- Existing tables: Check IAM roles in Core CDK

## Best Practices

1. **Always use Makefile commands** - They manage `.amplify-env` correctly
2. **Don't mix environments** - Keep sandbox/dev/prod separate
3. **Check before sandbox-prod** - You're using production data!
4. **Deploy Core CDK first** - For dev/prod environments
5. **Use isolated sandbox** - For pure frontend development