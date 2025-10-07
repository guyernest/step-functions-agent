# AWS Amplify Gen 2 Setup Guide: Best Practices and Common Pitfalls

This guide documents the correct way to set up an AWS Amplify Gen 2 project with Lambda functions, based on lessons learned from troubleshooting module export errors and CDK assembly issues.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Project Setup](#project-setup)
4. [Lambda Function Structure](#lambda-function-structure)
5. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Best Practices](#best-practices)

## Overview

AWS Amplify Gen 2 introduces a new, simplified structure for building full-stack applications. The key differences from Gen 1 include:
- Simplified Lambda function structure (no individual package.json or tsconfig.json)
- ES modules support with proper configuration
- Centralized dependency management
- TypeScript-first approach

## Prerequisites

- Node.js 18.x or 20.x (ensure consistency across your project)
- npm or yarn
- AWS CLI configured with appropriate credentials
- Basic understanding of TypeScript and AWS services

## Project Setup

### 1. Create a New Amplify Gen 2 Project

Always use the official Amplify scaffolding tool:

```bash
npx create-amplify@latest my-amplify-app
cd my-amplify-app
```

This creates the correct project structure with all necessary configurations.

### 2. Install Dependencies

Install AWS SDK and other dependencies at the **project root level**, not in individual Lambda folders:

```bash
npm install @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb @aws-sdk/client-sfn
```

### 3. Project Structure

The correct Amplify Gen 2 structure should look like this:

```
my-amplify-app/
├── amplify/
│   ├── auth/
│   │   └── resource.ts
│   ├── backend/
│   │   └── function/
│   │       └── myFunction/
│   │           ├── handler.ts      # Lambda handler code
│   │           └── resource.ts     # Function configuration
│   ├── data/
│   │   └── resource.ts            # GraphQL schema
│   ├── backend.ts                 # Backend configuration
│   ├── package.json               # Contains only: { "type": "module" }
│   └── tsconfig.json              # Amplify TypeScript config
├── src/                           # Frontend code
├── package.json                   # Project dependencies
└── tsconfig.json                  # Project TypeScript config
```

## Lambda Function Structure

### Correct Lambda Function Setup

#### 1. Function Resource Definition (`resource.ts`)

```typescript
import { defineFunction } from '@aws-amplify/backend';

export const myFunction = defineFunction({
  name: 'myFunction',
  entry: './handler.ts',
  runtime: 20,  // Node.js 20.x
  timeoutSeconds: 30,
  environment: {
    MY_ENV_VAR: 'value'
  }
});
```

#### 2. Function Handler (`handler.ts`)

```typescript
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({});
const ddbDocClient = DynamoDBDocumentClient.from(client);

export const handler = async (event: any) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  try {
    // Your Lambda logic here
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Success' })
    };
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};
```

### Important: What NOT to Include

Lambda functions in Amplify Gen 2 should **NOT** have:
- Individual `package.json` files
- Individual `tsconfig.json` files
- `node_modules` directories
- Bundling configurations in `resource.ts`

## Common Pitfalls to Avoid

### 1. Module Export Errors

**Problem**: "The requested module does not provide an export named 'functionName'"

**Causes**:
- Lambda functions have their own package.json/tsconfig.json
- Mixing CommonJS and ES modules
- Incorrect import/export syntax

**Solution**:
- Remove all package.json and tsconfig.json from Lambda folders
- Ensure root `amplify/package.json` contains `{ "type": "module" }`
- Use ES module syntax consistently

### 2. CDK Assembly Errors

**Problem**: "Unable to deploy due to CDK Assembly Error"

**Causes**:
- Corrupted build cache after terminal crash
- Node version mismatch
- TypeScript version conflicts

**Solution**:
```bash
# Clear all caches
rm -rf node_modules
rm -rf amplify/backend/function/*/node_modules
rm -rf .amplify
npm cache clean --force

# Reinstall
npm install
npx ampx sandbox
```

### 3. AWS SDK Import Errors

**Problem**: "Cannot find module '@aws-sdk/client-dynamodb'"

**Cause**: AWS SDK v3 is not included in Lambda runtime by default

**Solution**: Install AWS SDK dependencies at the project root:
```bash
npm install @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb
```

## Troubleshooting Guide

### Terminal Crash Recovery

If your terminal crashes during development:

1. Start fresh terminal session
2. Set up environment:
   ```bash
   # Restore AWS credentials
   assume your-profile  # or export AWS_PROFILE=your-profile
   
   # Ensure correct Node version
   nvm use 20  # or nvm use 18
   
   # Clean install
   npm install
   ```

3. Clear Amplify cache:
   ```bash
   rm -rf .amplify
   npx ampx sandbox --clean
   ```

### Module Resolution Issues

If you encounter module resolution errors:

1. Check that Lambda functions don't have individual package files
2. Verify root `amplify/package.json` has `"type": "module"`
3. Ensure consistent import syntax (use `.js` extensions if needed)
4. Clear TypeScript build info: `rm -rf tsconfig.tsbuildinfo`

## Best Practices

### 1. Backend Configuration

```typescript
// amplify/backend.ts
import { defineBackend } from '@aws-amplify/backend';
import * as iam from 'aws-cdk-lib/aws-iam';

const backend = defineBackend({
  auth,
  data,
  myFunction,
});

// Add IAM permissions
backend.myFunction.resources.lambda.addToRolePolicy(
  new iam.PolicyStatement({
    actions: ['dynamodb:GetItem', 'dynamodb:PutItem'],
    resources: ['arn:aws:dynamodb:*:*:table/MyTable*'],
  })
);
```

### 2. GraphQL Integration

```typescript
// amplify/data/resource.ts
import { defineData, a } from '@aws-amplify/backend';
import { myFunction } from '../backend/function/myFunction/resource';

const schema = a.schema({
  MyType: a.customType({
    id: a.string().required(),
    name: a.string(),
  }),
  
  myQuery: a
    .query()
    .returns(a.ref('MyType'))
    .handler(a.handler.function(myFunction))
    .authorization((allow) => [allow.authenticated()]),
});

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'userPool',
  },
});
```

### 3. Environment Variables

Always define environment variables in the function resource:

```typescript
export const myFunction = defineFunction({
  name: 'myFunction',
  entry: './handler.ts',
  environment: {
    TABLE_NAME: 'MyTable',
    REGION: process.env.AWS_REGION || 'us-east-1'
  }
});
```

### 4. Error Handling

Implement proper error handling in Lambda functions:

```typescript
export const handler = async (event: any) => {
  try {
    // Your logic
    return successResponse;
  } catch (error) {
    console.error('Error details:', error);
    // Return appropriate error response for GraphQL
    throw new Error(`Operation failed: ${error.message}`);
  }
};
```

## Development Workflow

1. **Start the sandbox**:
   ```bash
   npx ampx sandbox
   ```

2. **In another terminal, run the frontend**:
   ```bash
   cd ui_amplify  # or your frontend directory
   npm start
   ```

3. **Make changes** to Lambda functions - they will hot reload

4. **Test your functions** using the GraphQL API or AWS Console

## Migration from Problematic Setup

If you're migrating from a setup with module export errors:

1. Create a fresh Amplify project using `create-amplify`
2. Copy only the handler logic from your Lambda functions
3. Recreate function resources without bundling configurations
4. Install all dependencies at the root level
5. Test each function individually before adding more

## Conclusion

The key to avoiding issues with Amplify Gen 2 is to:
- Use the official scaffolding
- Keep Lambda functions simple (no individual configs)
- Manage dependencies centrally
- Maintain consistent Node.js versions
- Clear caches when encountering issues

Following this guide will help you avoid the common pitfalls and build robust Amplify Gen 2 applications.