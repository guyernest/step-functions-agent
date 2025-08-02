# Amplify Gen 2 Cross-Account Deployment Guide

This guide documents the learnings and best practices for deploying an AWS Amplify Gen 2 application to a different AWS account than the one used for development with the sandbox.

## Overview

When developing with Amplify Gen 2, the sandbox environment typically uses your local AWS credentials. However, when deploying to production or other environments, you often need to deploy to a different AWS account. This guide covers the key considerations and steps for successful cross-account deployment.

## Key Learnings

### 1. AWS SDK Bundling Issues

**Problem**: Lambda functions using AWS SDK fail to bundle correctly in the Amplify pipeline with errors like:
```
Could not resolve "@aws-sdk/client-dynamodb"
Could not resolve "aws-sdk"
```

**Root Cause**: 
- Node.js 20 Lambda runtime includes AWS SDK v3 (not v2)
- Amplify's esbuild bundler tries to bundle the AWS SDK by default
- TypeScript needs type definitions during compilation

**Solution**:
1. Use AWS SDK v3 imports (not v2):
   ```typescript
   // ✅ Correct - AWS SDK v3
   import { DynamoDBClient, ScanCommand } from '@aws-sdk/client-dynamodb';
   
   // ❌ Wrong - AWS SDK v2
   const AWS = require('aws-sdk');
   ```

2. Add AWS SDK packages as devDependencies:
   ```json
   {
     "devDependencies": {
       "@aws-sdk/client-dynamodb": "^3.859.0",
       "@aws-sdk/client-sfn": "^3.859.0",
       "@types/aws-lambda": "^8.10.152"
     }
   }
   ```

### 2. Amplify Pipeline Deployment

**Important**: The `ampx pipeline-deploy` command is designed for CI/CD environments only.

```bash
# ❌ This will fail locally
npx ampx pipeline-deploy --branch main --app-id YOUR_APP_ID

# ✅ Use sandbox for local development
npx ampx sandbox
```

### 3. Cross-Account Deployment Steps

1. **Create Amplify App in Target Account**:
   - Log into the target AWS account
   - Create a new Amplify app in the AWS Console
   - Note the App ID (e.g., `da3qaqtumm8y3`)

2. **Connect to Git Repository**:
   - Connect your GitHub/GitLab/CodeCommit repository
   - Configure branch auto-build settings
   - Amplify will automatically detect the `amplify.yml` or use default build settings

3. **Build Configuration**:
   The default Amplify build configuration works well:
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

4. **Environment Variables**:
   - Amplify automatically provides `$AWS_BRANCH` and `$AWS_APP_ID`
   - Additional environment variables can be set in Amplify Console

### 4. Lambda Function Considerations

1. **TypeScript Declaration for process.env**:
   ```typescript
   declare const process: { env: { AWS_REGION?: string } };
   ```

2. **No Custom Bundling Options**:
   - Amplify Gen 2's `defineFunction` doesn't support custom esbuild options
   - Cannot use `externalModules` property
   - AWS SDK is automatically available in Lambda runtime

3. **Resource Definition**:
   ```typescript
   export const myFunction = defineFunction({
     name: 'myFunction',
     entry: './handler.ts',
     timeoutSeconds: 30,
     memoryMB: 512
   });
   ```

### 5. Troubleshooting Build Failures

1. **Check Build Logs**:
   - Look for TypeScript compilation errors
   - Check for module resolution issues
   - Verify all required dependencies are in package.json

2. **Common Fixes**:
   - Ensure all TypeScript types are installed
   - Use ES module imports for consistency
   - Don't try to bundle AWS SDK - it's provided by runtime

3. **Local Testing**:
   ```bash
   # Test TypeScript compilation
   npm run build
   
   # Test Amplify sandbox
   npx ampx sandbox
   ```

### 6. Best Practices

1. **Development Workflow**:
   - Use `npx ampx sandbox` for local development
   - Test builds locally before pushing
   - Keep AWS SDK types as devDependencies

2. **Git Workflow**:
   - Commit and push to trigger automatic deployments
   - Use meaningful commit messages
   - Tag releases for production deployments

3. **Security**:
   - Never commit AWS credentials
   - Use Amplify's built-in auth for API access
   - Keep sensitive data in environment variables

## Summary

Deploying Amplify Gen 2 to a different account is straightforward once you understand:
- AWS SDK v3 is included in Lambda runtime (no bundling needed)
- TypeScript needs SDK types as devDependencies for compilation
- Pipeline deployment only works in CI/CD environments
- Amplify handles most of the complexity automatically

The key is ensuring your Lambda functions use the correct AWS SDK imports and that all necessary type definitions are available during the build process.