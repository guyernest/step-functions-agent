# Step Functions AI Agents - Complete Deployment Guide

This guide provides step-by-step instructions for deploying the complete Step Functions AI Agents system to a new AWS account and region, including both the backend infrastructure (CDK) and the frontend UI (Amplify).

## Prerequisites

1. **AWS Account**: Target AWS account with appropriate permissions
2. **AWS CLI**: Installed and configured with credentials for the target account
3. **Node.js**: Version 20.x or higher
4. **CDK CLI**: Install with `npm install -g aws-cdk`
5. **Amplify CLI**: Install with `npm install -g @aws-amplify/cli`
6. **Git**: For cloning the repository

## Architecture Overview

The system consists of:
- **Backend**: Step Functions state machines, Lambda functions, DynamoDB tables (deployed via CDK)
- **Frontend**: React application with Amplify Gen 2 backend (deployed via Amplify)
- **Integration**: The UI connects to Step Functions and DynamoDB tables in the same account

## Step 1: Clone and Prepare the Repository

```bash
# Clone the repository
git clone https://github.com/guyernest/step-functions-agent.git
cd step-functions-agent

# Install dependencies for the CDK backend
npm install

# Install dependencies for the Amplify UI
cd ui_amplify
npm install
cd ..
```

## Step 2: Configure AWS Credentials

```bash
# Option 1: Use AWS SSO (recommended)
aws sso login --profile your-target-profile
export AWS_PROFILE=your-target-profile

# Option 2: Use access keys
aws configure --profile your-target-profile
export AWS_PROFILE=your-target-profile

# Verify the correct account
aws sts get-caller-identity
```

## Step 3: Deploy Backend Infrastructure with CDK

### 3.1 Bootstrap CDK (if not already done for this account/region)

```bash
# Bootstrap CDK for your target account and region
cdk bootstrap aws://ACCOUNT_ID/REGION
```

### 3.2 Review CDK Configuration

Check `cdk.json` and update any account-specific settings:
- Stack naming conventions
- Default tags
- Region-specific configurations

### 3.3 Deploy CDK Stacks

```bash
# List all stacks
cdk list

# Deploy all stacks (or deploy individually)
cdk deploy --all

# Or deploy specific stacks
cdk deploy StepFunctionsAgentStack
cdk deploy AgentRegistryStack
cdk deploy ToolRegistryStack
```

### 3.4 Note Important Outputs

After deployment, note these values from the CDK outputs:
- Agent Registry DynamoDB table name
- Tool Registry DynamoDB table name
- Step Functions state machine ARNs
- Lambda function ARNs

## Step 4: Deploy Frontend with Amplify

### 4.1 Create Amplify App in Target Account

1. Log into AWS Console for the target account
2. Navigate to AWS Amplify
3. Click "Create new app"
4. Choose "Build a web app"
5. Connect your Git repository (GitHub/GitLab/CodeCommit)
6. Select the branch (usually `main`)
7. Note the App ID (e.g., `da3qaqtumm8y3`)

### 4.2 Configure Build Settings

Amplify should auto-detect the build settings, but verify they match:

```yaml
version: 1
applications:
  - backend:
      phases:
        build:
          commands:
            - npm ci --cache .npm --prefer-offline
            - npx ampx pipeline-deploy --branch $AWS_BRANCH --app-id $AWS_APP_ID
    frontend:
      phases:
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: dist
        files:
          - '**/*'
      cache:
        paths:
          - .npm/**/*
    appRoot: ui_amplify
```

### 4.3 Set Environment Variables

In Amplify Console, set these environment variables:
- `VITE_AGENT_REGISTRY_TABLE`: Your agent registry table name from CDK
- `VITE_TOOL_REGISTRY_TABLE`: Your tool registry table name from CDK
- `VITE_AWS_REGION`: Your deployment region

### 4.4 Deploy Amplify

1. Save and deploy in Amplify Console
2. Monitor the build progress
3. Once complete, access your app URL

## Step 5: Configure Integration

### 5.1 Update Lambda Permissions

The Amplify-deployed Lambda functions need permissions to access CDK-deployed resources:

```bash
# Update the Amplify Lambda execution role to access DynamoDB tables
# This is typically handled by Amplify, but verify in IAM console
```

### 5.2 Configure CORS (if needed)

If the UI and API are on different domains, configure CORS in your API Gateway or Lambda functions.

### 5.3 Update Settings in UI

1. Access the deployed UI
2. Navigate to Settings page
3. Configure:
   - Agent Registry Table Name
   - Tool Registry Table Name
   - AWS Region

## Step 6: Verify Deployment

### 6.1 Backend Verification

```bash
# List Step Functions state machines
aws stepfunctions list-state-machines --region your-region

# Check DynamoDB tables
aws dynamodb list-tables --region your-region

# Test a Lambda function
aws lambda invoke --function-name your-function-name output.json
```

### 6.2 Frontend Verification

1. Access the Amplify app URL
2. Check the Dashboard loads properly
3. Verify Agent Registry shows agents
4. Test executing an agent
5. Check execution history

## Step 7: Post-Deployment Configuration

### 7.1 Register Agents and Tools

```bash
# Use the provided scripts or API to register agents
python scripts/register_agent.py --name "weather-agent" --description "Gets weather information"

# Register tools
python scripts/register_tool.py --name "get_weather" --description "Fetches weather data"
```

### 7.2 Set Up Monitoring

1. Configure CloudWatch dashboards
2. Set up alarms for critical metrics
3. Enable X-Ray tracing for debugging

### 7.3 Configure Backups

1. Enable point-in-time recovery for DynamoDB tables
2. Set up regular backups for critical data

## Troubleshooting

### Common Issues

1. **Amplify Build Failures**
   - Check AWS SDK imports (use v3, not v2)
   - Ensure all TypeScript types are installed
   - Review build logs in Amplify Console

2. **Permission Errors**
   - Verify IAM roles have necessary permissions
   - Check resource-based policies
   - Ensure cross-service permissions are configured

3. **Connection Issues**
   - Verify AWS region settings
   - Check network connectivity
   - Ensure security groups allow necessary traffic

### Debug Commands

```bash
# Check Amplify app status
aws amplify get-app --app-id YOUR_APP_ID

# View CloudFormation stack events
aws cloudformation describe-stack-events --stack-name YOUR_STACK_NAME

# Check Lambda logs
aws logs tail /aws/lambda/YOUR_FUNCTION_NAME --follow
```

## Security Best Practices

1. **Least Privilege**: Grant minimal required permissions
2. **Encryption**: Enable encryption at rest for DynamoDB
3. **Network**: Use VPC endpoints where appropriate
4. **Secrets**: Store sensitive data in AWS Secrets Manager
5. **Monitoring**: Enable CloudTrail for audit logging

## Cost Optimization

1. **DynamoDB**: Use on-demand pricing for development
2. **Lambda**: Monitor and optimize memory allocation
3. **Step Functions**: Use Express workflows for high-volume
4. **Amplify**: Consider build minutes and bandwidth usage

## Maintenance

### Regular Tasks

1. **Updates**: Keep dependencies updated
2. **Monitoring**: Review CloudWatch metrics weekly
3. **Costs**: Monitor AWS Cost Explorer monthly
4. **Security**: Run security scans quarterly

### Backup and Recovery

1. **Code**: Maintain Git repository backups
2. **Data**: Regular DynamoDB backups
3. **Configuration**: Document all custom settings
4. **Runbooks**: Create operational procedures

## Conclusion

This deployment creates a complete Step Functions AI Agents system with:
- Scalable backend infrastructure via CDK
- Modern React UI via Amplify
- Secure integration between components
- Monitoring and operational capabilities

For updates and issues, refer to the project repository.