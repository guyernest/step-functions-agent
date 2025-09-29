# Remote Amplify Deployment Configuration

## Overview
This guide explains how to deploy the Amplify UI application to different environments (dev, staging, prod) using AWS Amplify Hosting with proper table suffix configuration.

## Environment Detection Strategy

The backend uses the following precedence for determining the environment:
1. **Environment Variable** (`TABLE_ENV_SUFFIX`) - For branch deployments
2. **File-based** (`.amplify-env`) - For local sandbox development
3. **Default** (`sandbox-{username}`) - Fallback for isolated development

## Setting Up Remote Deployments

### Step 1: Configure Environment Variables in Amplify Console

1. Navigate to your Amplify app in the AWS Console
2. Go to **Environment variables** under **Hosting > Build settings**
3. Add the following environment variable:
   ```
   TABLE_ENV_SUFFIX = prod    # For production branch
   TABLE_ENV_SUFFIX = dev     # For development branch
   TABLE_ENV_SUFFIX = staging # For staging branch
   ```

### Step 2: Create/Update amplify.yml

Create an `amplify.yml` file in the repository root if it doesn't exist:

```yaml
version: 1
applications:
  - appRoot: ui_amplify
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            # Export environment variable for the backend to use
            - echo "TABLE_ENV_SUFFIX=$TABLE_ENV_SUFFIX" >> .env
            - npx ampx generate outputs --branch $AWS_BRANCH --app-id $AWS_APP_ID
            - npm run build
      artifacts:
        baseDirectory: dist
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*

    backend:
      phases:
        build:
          commands:
            # The backend will read TABLE_ENV_SUFFIX from the environment
            - npx ampx pipeline-deploy --branch $AWS_BRANCH --app-id $AWS_APP_ID
```

### Step 3: Configure Branch Settings

For each branch you want to deploy:

1. **Production Branch** (main/master):
   - Environment Variable: `TABLE_ENV_SUFFIX=prod`
   - This will import tables: `AgentRegistry-prod`, `ToolRegistry-prod`, etc.

2. **Development Branch** (develop):
   - Environment Variable: `TABLE_ENV_SUFFIX=dev`
   - This will import tables: `AgentRegistry-dev`, `ToolRegistry-dev`, etc.

3. **Feature Branches**:
   - Environment Variable: `TABLE_ENV_SUFFIX=sandbox-feature`
   - Or don't set it to use the default sandbox behavior

## Table Import Behavior

Based on the `TABLE_ENV_SUFFIX` value:

- **prod/dev/staging**: Imports existing tables from Core CDK stack
  - Uses CloudFormation exports: `SharedTableArn{TableName}-{suffix}`
  - Example: `SharedTableArnAgentRegistry-prod`

- **sandbox-***: Creates local tables within the Amplify stack
  - Tables are created with suffix: `{TableName}-{suffix}`
  - Example: `AgentRegistry-sandbox-feature`

## Deployment Commands

### Manual Deployment (from CI/CD)
```bash
# Set the environment for production
export TABLE_ENV_SUFFIX=prod

# Deploy the backend
npx ampx pipeline-deploy --branch main --app-id YOUR_APP_ID

# Generate outputs for the frontend
npx ampx generate outputs --branch main --app-id YOUR_APP_ID
```

### Local Testing of Remote Configuration
```bash
# Test production configuration locally
export TABLE_ENV_SUFFIX=prod
npx ampx sandbox --once

# Test development configuration locally
export TABLE_ENV_SUFFIX=dev
npx ampx sandbox --once
```

## Verification

After deployment, verify the configuration:

1. Check CloudFormation stack outputs for table references
2. Check AppSync data sources to ensure they point to correct tables
3. Test the UI to confirm data is loading from the correct tables

## Troubleshooting

### Issue: Tables not found
**Solution**: Ensure the Core CDK stack has been deployed with the matching environment suffix and CloudFormation exports are available.

### Issue: Permission denied errors
**Solution**: Verify the AppSync service role has permissions for all table operations including GSI queries.

### Issue: Wrong environment detected
**Solution**: Check the build logs in Amplify Console to see which environment was detected. Verify the `TABLE_ENV_SUFFIX` environment variable is set correctly.

## Required Core CDK Exports

The Core CDK stack must export the following for each table:
```python
CfnOutput(
    self,
    f"SharedTableArnAgentRegistry",
    value=agent_registry_table.table_arn,
    export_name=f"SharedTableArnAgentRegistry-{environment}"
)
```

## Security Considerations

- Never store sensitive values in environment variables
- Use AWS Secrets Manager for API keys and credentials
- Environment variables are visible in build logs

## Reference

- [Amplify Environment Variables Documentation](https://docs.amplify.aws/react/deploy-and-host/fullstack-branching/environment-variables/)
- [Amplify Build Specifications](https://docs.aws.amazon.com/amplify/latest/userguide/build-settings.html)