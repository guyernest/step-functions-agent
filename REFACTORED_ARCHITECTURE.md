# Refactored Step Functions AI Agents - Architecture Guide

This document describes the refactored architecture and deployment considerations for the Step Functions AI Agents system.

## Refactored Architecture Overview

### Backend Components (CDK)

```
step-functions-agent/
├── lib/
│   ├── step-functions-agent-stack.ts    # Main stack with Step Functions
│   ├── agent-registry-stack.ts          # DynamoDB table for agents
│   ├── tool-registry-stack.ts           # DynamoDB table for tools
│   └── lambda/                          # Lambda functions for agents
├── bin/
│   └── step-functions-agent.ts          # CDK app entry point
└── cdk.json                             # CDK configuration
```

### Frontend Components (Amplify Gen 2)

```
ui_amplify/
├── amplify/
│   ├── backend.ts                       # Amplify backend configuration
│   ├── auth/resource.ts                 # Cognito auth configuration
│   ├── data/resource.ts                 # GraphQL API configuration
│   └── backend/function/                # Lambda resolvers
│       ├── listAgentsFromRegistry/
│       ├── listToolsFromRegistry/
│       ├── startAgentExecution/
│       ├── getStepFunctionExecution/
│       └── listStepFunctionExecutions/
└── src/
    ├── pages/                           # React components
    └── components/                      # Shared components
```

## Key Refactoring Improvements

### 1. Separation of Concerns

- **Infrastructure**: CDK manages core AWS resources
- **Application**: Amplify manages UI and API layer
- **Integration**: Clean interfaces between layers

### 2. Enhanced UI Features

- **Dashboard**: Real-time metrics and navigation
- **Agent Registry**: Hierarchical view with tool relationships
- **Execution**: Simplified text input (no JSON required)
- **Message Rendering**: Rich content display with tables, images, code
- **Deep Linking**: URL parameters for seamless navigation

### 3. Improved Developer Experience

- **TypeScript**: Full type safety across the stack
- **Modular**: Clear separation of components
- **Testable**: Isolated functions and components
- **Scalable**: Easy to add new agents and tools

## Deployment Architecture

### Multi-Account Strategy

```
Development Account          Production Account
├── CDK Backend             ├── CDK Backend
│   └── Dev Resources       │   └── Prod Resources
└── Amplify Sandbox         └── Amplify App
    └── Local Testing           └── Production UI
```

### Cross-Region Considerations

1. **Data Residency**: DynamoDB tables in primary region
2. **Lambda Edge**: For global UI performance
3. **Step Functions**: Regional deployment
4. **CloudFront**: Global CDN for UI assets

## Integration Points

### 1. UI to Step Functions

```typescript
// Direct SDK calls from browser
const sfnClient = new SFNClient({
  region: config.region,
  credentials: await fetchAuthSession()
});
```

### 2. Lambda to DynamoDB

```typescript
// Lambda resolvers access registry tables
const command = new ScanCommand({
  TableName: event.arguments.tableName
});
```

### 3. Step Functions to Lambda

```yaml
# State machine invokes Lambda functions
Resource: !GetAtt AgentLambda.Arn
```

## Security Model

### Authentication Flow

```
User → Cognito → Amplify UI → API Gateway → Lambda → AWS Resources
```

### Authorization

1. **Cognito User Pools**: User authentication
2. **IAM Roles**: Service permissions
3. **API Keys**: Optional rate limiting
4. **Resource Policies**: Fine-grained access

## Configuration Management

### Environment Variables

**CDK Stack**:
```typescript
new cdk.Stack(app, 'AgentStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  }
});
```

**Amplify Backend**:
```typescript
const backend = defineBackend({
  auth,
  data,
  // Functions automatically get environment context
});
```

### Dynamic Configuration

**Settings Page**: Users can configure:
- Agent Registry Table Name
- Tool Registry Table Name  
- AWS Region
- Execution Parameters

## Monitoring and Observability

### CloudWatch Integration

```
Amplify UI → CloudWatch RUM
Lambda Functions → CloudWatch Logs
Step Functions → CloudWatch Metrics
DynamoDB → CloudWatch Insights
```

### Distributed Tracing

- X-Ray enabled for end-to-end tracing
- Correlation IDs for request tracking
- Performance metrics at each layer

## Scaling Considerations

### Horizontal Scaling

- **Lambda**: Automatic scaling with concurrent executions
- **DynamoDB**: Auto-scaling or on-demand
- **Step Functions**: Express workflows for high volume
- **Amplify**: CDN and edge optimization

### Vertical Scaling

- **Lambda Memory**: Configurable per function
- **Timeout Settings**: Appropriate for workload
- **DynamoDB Capacity**: Provisioned or on-demand

## Migration Path

### From Original to Refactored

1. **Data Migration**: Export/import DynamoDB data
2. **State Machines**: Deploy new versions
3. **UI Cutover**: Switch DNS to Amplify app
4. **Rollback Plan**: Keep original system available

### Version Management

- **API Versioning**: GraphQL schema evolution
- **Infrastructure**: CDK version tracking
- **UI**: Amplify branch deployments

## Best Practices

### Development Workflow

1. **Local Development**: `npx ampx sandbox`
2. **Feature Branches**: Amplify preview deployments
3. **Infrastructure Changes**: CDK diff before deploy
4. **Testing**: Unit, integration, and E2E tests

### Operational Excellence

1. **Runbooks**: Document common procedures
2. **Alerts**: Proactive monitoring
3. **Backups**: Automated and tested
4. **Updates**: Regular dependency updates

## Future Enhancements

### Planned Features

1. **WebSocket Support**: Real-time execution updates
2. **Batch Operations**: Bulk agent execution
3. **Advanced Analytics**: Usage patterns and insights
4. **Plugin System**: Extensible agent capabilities

### Architecture Evolution

1. **Event-Driven**: EventBridge integration
2. **Multi-Region**: Active-active deployment
3. **Edge Computing**: Lambda@Edge for agents
4. **Container Support**: ECS/Fargate agents

## Conclusion

The refactored architecture provides:
- Clean separation between infrastructure and application
- Enhanced user experience with modern UI
- Scalable and maintainable codebase
- Clear deployment and operational model

This architecture supports both current requirements and future growth.