/**
 * Amplify Backend Configuration
 *
 * Architecture:
 * - This Amplify app provides the management UI for the Step Functions Agent Framework
 * - Core infrastructure (agents, tools, registries) is managed by the main CDK application
 * - This app references those resources using predictable naming conventions
 *
 * Resource Discovery Strategy:
 * 1. Production/Dev: References existing tables from Core CDK by name
 * 2. Sandbox: Can create local tables for isolated development
 *
 * Environment Configuration:
 * - Set environment via .amplify-env file (created by Makefile)
 * - Control table strategy via USE_EXISTING_TABLES env var
 * - Default: prod/dev use existing tables, sandbox creates local
 */
import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { startAgentExecution } from './backend/function/startAgentExecution/resource';
import { listStepFunctionExecutions } from './backend/function/listStepFunctionExecutions/resource';
import { getStepFunctionExecution } from './backend/function/getStepFunctionExecution/resource';
import { getExecutionStatistics } from './backend/function/getExecutionStatistics/resource';
import { getCloudWatchMetrics } from './backend/function/getCloudWatchMetrics/resource';
import { testToolExecution } from './backend/function/testToolExecution/resource';
import { updateProviderAPIKey } from './backend/function/updateProviderAPIKey/resource';
import { getToolSecretValues } from './backend/function/getToolSecretValues/resource';
import { updateToolSecrets } from './backend/function/updateToolSecrets/resource';
import { getStateMachineInfo } from './backend/function/getStateMachineInfo/resource';
import { registerMCPServer } from './backend/function/registerMCPServer/resource';
import { executeHealthTest } from './backend/function/executeHealthTest/resource';
import { indexStepFunctionExecution } from './backend/function/indexStepFunctionExecution/resource';
import { listExecutionsFromIndex } from './backend/function/listExecutionsFromIndex/resource';
// API Key management functions - to be implemented if needed
// import { generateAPIKey } from './backend/function/generateAPIKey/resource';
// import { revokeAPIKey } from './backend/function/revokeAPIKey/resource';
// import { rotateAPIKey } from './backend/function/rotateAPIKey/resource';
// import { listAPIKeys } from './backend/function/listAPIKeys/resource';
import { createMcpServerResources } from './mcp-server/resource';
import { PolicyStatement, Effect, Policy } from 'aws-cdk-lib/aws-iam';
import { aws_dynamodb, RemovalPolicy, Fn } from 'aws-cdk-lib';
import { Rule } from 'aws-cdk-lib/aws-events';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import * as fs from 'fs';
import * as path from 'path';

/**
 * @see https://docs.amplify.aws/react/build-a-backend/ to add storage, functions, and more
 */
const backend = defineBackend({
  auth,
  data,
  startAgentExecution,
  listStepFunctionExecutions,
  getStepFunctionExecution,
  getExecutionStatistics,
  getCloudWatchMetrics,
  testToolExecution,
  updateProviderAPIKey,
  getToolSecretValues,
  updateToolSecrets,
  getStateMachineInfo,
  registerMCPServer,
  executeHealthTest,
  indexStepFunctionExecution,
  listExecutionsFromIndex,
  // API key management functions - to be implemented
  // generateAPIKey,
  // revokeAPIKey,
  // rotateAPIKey,
  // listAPIKeys,
});

// Set the Cognito User Pool name
const userPool = backend.auth.resources.userPool;
const cfnUserPool = userPool.node.defaultChild as any;
cfnUserPool.userPoolName = 'StepFunctionsAgentAuth';

// Grant Step Functions permissions to authenticated users
const stepFunctionsPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'states:GetActivityTask',
    'states:SendTaskSuccess',
    'states:SendTaskFailure',
    'states:ListActivities',
    'states:DescribeActivity',
    'states:StartExecution',
    'states:ListStateMachines',
    'states:DescribeExecution',
    'states:ListTagsForResource'
  ],
  resources: ['*']
});

// Add the policies to the authenticated role
const stepFunctionsActivityPolicy = new Policy(backend.auth.resources.authenticatedUserIamRole.stack, 'StepFunctionsActivityPolicy', {
  statements: [stepFunctionsPolicy]
});

backend.auth.resources.authenticatedUserIamRole.attachInlinePolicy(stepFunctionsActivityPolicy);

// Add external DynamoDB tables as data sources
const externalDataSourcesStack = backend.createStack('ExternalDataSources');

// Determine environment suffix to match Core CDK naming
// This must match the ENVIRONMENT variable used in Core CDK app.py
const userName = process.env.USER || 'user';

// Determine environment based on (in order of precedence):
// 1. Environment variable (for Amplify branch deployments)
// 2. File-based detection (for local development)
// 3. Default sandbox mode
let envSuffix: string;

// First, check for environment variable from Amplify Console
if (process.env.TABLE_ENV_SUFFIX) {
  envSuffix = process.env.TABLE_ENV_SUFFIX;
  console.log(`=== Using environment from TABLE_ENV_SUFFIX variable: ${envSuffix} ===`);
  console.log(`    (Set via Amplify Console environment variables)`);
} else {
  // Fall back to file-based detection for local development
  try {
    // Check for environment file (written by Makefile commands)
    // Try multiple possible locations for the .amplify-env file
    const possiblePaths = [
      '.amplify-env',                    // Current working directory
      '../.amplify-env',                 // One level up
      '../../.amplify-env',              // Two levels up
      path.join(process.cwd(), '.amplify-env'),  // Absolute from cwd
    ];

    let envFile: string | null = null;
    for (const filePath of possiblePaths) {
      try {
        envFile = fs.readFileSync(filePath, 'utf8').trim();
        console.log(`    Found .amplify-env at: ${filePath}`);
        break;
      } catch {
        // Try next path
      }
    }

    if (envFile) {
      envSuffix = envFile;
      console.log(`=== Using environment from .amplify-env file: ${envSuffix} ===`);
    } else {
      throw new Error('No .amplify-env file found');
    }
  } catch (err) {
    // Check if we're running in Amplify Hosting (has AWS_BRANCH env var)
    if (process.env.AWS_BRANCH) {
      // Default to prod for Amplify Hosting deployments
      envSuffix = 'prod';
      console.log(`=== Using default 'prod' for Amplify Hosting deployment ===`);
      console.log(`    Branch: ${process.env.AWS_BRANCH}`);
      console.log(`    (Set TABLE_ENV_SUFFIX to override)`);
    } else {
      // Fallback to sandbox mode for local development
      envSuffix = `sandbox-${userName}`;
      console.log(`=== Using default sandbox environment: ${envSuffix} ===`);
      console.log(`    (No TABLE_ENV_SUFFIX variable or .amplify-env file found)`);
    }
  }
}

// Resource discovery strategy:
// 1. Use predictable naming conventions that match Core CDK
// 2. Reference tables by name (they must exist in the account)
// 3. For true sandbox isolation, create separate sandbox tables

// Determine if we should import from Core CDK or create local tables
// Remote Amplify builds (prod, dev) import everything
// Local sandbox connects to specified core env but creates isolated UI tables
const importFromCoreCDK = envSuffix === 'prod' || envSuffix === 'dev' || process.env.USE_EXISTING_TABLES === 'true';

// Which core environment to connect to (prod, dev, etc.)
// For remote builds: use the deployment environment (prod connects to core-prod, dev to core-dev)
// For sandbox: connect to specified core env (default: prod)
const coreEnv = importFromCoreCDK ? envSuffix : (process.env.CORE_ENV || 'prod');

// UI table suffix: remote builds use env name, sandbox uses sandbox-{user} for isolation
const uiTableEnvSuffix = importFromCoreCDK ? envSuffix : `sandbox-${userName}`;

// For logging
console.log(`=== Environment Configuration ===`);
console.log(`    Amplify environment: ${envSuffix}`);
console.log(`    Core environment (for registries): ${coreEnv}`);
console.log(`    UI tables suffix: ${uiTableEnvSuffix}`);
console.log(`    Strategy: ${importFromCoreCDK ? 'Remote build - import all tables' : `Sandbox - connect to core-${coreEnv}, create isolated UI tables`}`);

// Import or create DynamoDB tables
let agentRegistryTable: aws_dynamodb.ITable;
let toolRegistryTable: aws_dynamodb.ITable;
let mcpRegistryTable: aws_dynamodb.ITable;
let testEventsTable: aws_dynamodb.ITable;
let testResultsTable: aws_dynamodb.ITable;
let templateRegistryTable: aws_dynamodb.ITable;

if (importFromCoreCDK) {
  // Remote Amplify build: Import all tables from matching core environment
  console.log(`=== Remote Build Mode: Importing all tables from core-${coreEnv} ===`);

  // Import core/registry tables using CloudFormation exports
  agentRegistryTable = aws_dynamodb.Table.fromTableArn(
    externalDataSourcesStack,
    'AgentRegistryTable',
    Fn.importValue(`SharedTableArnAgentRegistry-${coreEnv}`)
  );

  toolRegistryTable = aws_dynamodb.Table.fromTableArn(
    externalDataSourcesStack,
    'ToolRegistryTable',
    Fn.importValue(`SharedTableArnToolRegistry-${coreEnv}`)
  );

  mcpRegistryTable = aws_dynamodb.Table.fromTableArn(
    externalDataSourcesStack,
    'MCPRegistryTable',
    Fn.importValue(`MCPRegistryTableArn-${coreEnv}`)
  );

  templateRegistryTable = aws_dynamodb.Table.fromTableArn(
    externalDataSourcesStack,
    'TemplateRegistryTable',
    Fn.importValue(`TemplateRegistryTableArn-${coreEnv}`)
  );

  // Import UI tables using CloudFormation exports
  testEventsTable = aws_dynamodb.Table.fromTableName(
    externalDataSourcesStack,
    'TestEventsTable',
    Fn.importValue(`SharedTableTestEvents-${uiTableEnvSuffix}`)
  );

  testResultsTable = aws_dynamodb.Table.fromTableName(
    externalDataSourcesStack,
    'TestResultsTable',
    Fn.importValue(`SharedTableTestResults-${uiTableEnvSuffix}`)
  );
} else {
  // Sandbox Mode:
  // - Import core/registry tables from specified core env (default: prod)
  // - Create sandbox-specific UI tables (isolated from remote builds)
  console.log(`=== Sandbox Mode: Connecting to core-${coreEnv}, creating UI tables with ${uiTableEnvSuffix} ===`);

  // Import core/registry tables from specified environment
  agentRegistryTable = aws_dynamodb.Table.fromTableName(
    externalDataSourcesStack,
    'AgentRegistryTable',
    `AgentRegistry-${coreEnv}`
  );

  toolRegistryTable = aws_dynamodb.Table.fromTableName(
    externalDataSourcesStack,
    'ToolRegistryTable',
    `ToolRegistry-${coreEnv}`
  );

  mcpRegistryTable = aws_dynamodb.Table.fromTableName(
    externalDataSourcesStack,
    'MCPRegistryTable',
    `MCPServerRegistry-${coreEnv}`
  );

  templateRegistryTable = aws_dynamodb.Table.fromTableName(
    externalDataSourcesStack,
    'TemplateRegistryTable',
    `TemplateRegistry-${coreEnv}`
  );

  // Create sandbox-specific UI tables (for isolated test data)
  testEventsTable = new aws_dynamodb.Table(externalDataSourcesStack, 'TestEventsTable', {
    tableName: `TestEvents-${uiTableEnvSuffix}`,
    partitionKey: { name: 'id', type: aws_dynamodb.AttributeType.STRING },
    billingMode: aws_dynamodb.BillingMode.PAY_PER_REQUEST,
    removalPolicy: RemovalPolicy.DESTROY
  });

  testResultsTable = new aws_dynamodb.Table(externalDataSourcesStack, 'TestResultsTable', {
    tableName: `TestResults-${uiTableEnvSuffix}`,
    partitionKey: { name: 'id', type: aws_dynamodb.AttributeType.STRING },
    billingMode: aws_dynamodb.BillingMode.PAY_PER_REQUEST,
    removalPolicy: RemovalPolicy.DESTROY
  });
}

// Handle LLMModels table
// This is a UI-specific table for managing model costs and configurations
// Each environment (prod, dev, sandbox-user) gets its own table
let llmModelsTable: aws_dynamodb.ITable;

if (importFromCoreCDK) {
  // For prod/dev: import existing table
  const llmModelsTableName = `LLMModels-${envSuffix}`;
  console.log(`    Importing LLMModels table: ${llmModelsTableName}`);

  llmModelsTable = aws_dynamodb.Table.fromTableAttributes(
    externalDataSourcesStack,
    'LLMModelsTable',
    {
      tableName: llmModelsTableName,
      globalIndexes: ['provider-index']
    }
  );
} else {
  // For sandbox: create environment-specific table
  const llmModelsTableName = `LLMModels-${uiTableEnvSuffix}`;
  console.log(`    Creating LLMModels table: ${llmModelsTableName}`);

  llmModelsTable = new aws_dynamodb.Table(externalDataSourcesStack, 'LLMModelsTable', {
    tableName: llmModelsTableName,
    partitionKey: { name: 'pk', type: aws_dynamodb.AttributeType.STRING },
    billingMode: aws_dynamodb.BillingMode.PAY_PER_REQUEST,
    pointInTimeRecovery: true,
    removalPolicy: RemovalPolicy.DESTROY
  });

  // Add Global Secondary Index for provider queries
  (llmModelsTable as aws_dynamodb.Table).addGlobalSecondaryIndex({
    indexName: 'provider-index',
    partitionKey: { name: 'provider', type: aws_dynamodb.AttributeType.STRING },
    sortKey: { name: 'is_active', type: aws_dynamodb.AttributeType.STRING },
    projectionType: aws_dynamodb.ProjectionType.ALL
  });
}

// Create ExecutionIndex table for efficient history queries
// This is a UI-specific table, so use uiTableEnvSuffix to keep sandbox isolated
const executionIndexTableName = `ExecutionIndex-${uiTableEnvSuffix}`;
console.log(`    Creating ExecutionIndex table: ${executionIndexTableName}`);

const executionIndexTable = new aws_dynamodb.Table(externalDataSourcesStack, 'ExecutionIndexTable', {
  tableName: executionIndexTableName,
  partitionKey: { name: 'executionArn', type: aws_dynamodb.AttributeType.STRING },
  billingMode: aws_dynamodb.BillingMode.PAY_PER_REQUEST,
  pointInTimeRecovery: true,
  removalPolicy: RemovalPolicy.DESTROY, // Change to RETAIN for production
  stream: aws_dynamodb.StreamViewType.NEW_AND_OLD_IMAGES, // For future use
});

// Add GSI for agent + date queries
executionIndexTable.addGlobalSecondaryIndex({
  indexName: 'AgentDateIndex',
  partitionKey: { name: 'agentName', type: aws_dynamodb.AttributeType.STRING },
  sortKey: { name: 'startDate', type: aws_dynamodb.AttributeType.STRING },
  projectionType: aws_dynamodb.ProjectionType.ALL,
});

// Add GSI for status + date queries
executionIndexTable.addGlobalSecondaryIndex({
  indexName: 'StatusDateIndex',
  partitionKey: { name: 'status', type: aws_dynamodb.AttributeType.STRING },
  sortKey: { name: 'startDate', type: aws_dynamodb.AttributeType.STRING },
  projectionType: aws_dynamodb.ProjectionType.ALL,
});

// Grant permissions to indexStepFunctionExecution Lambda
executionIndexTable.grantWriteData(backend.indexStepFunctionExecution.resources.lambda);
backend.indexStepFunctionExecution.addEnvironment('EXECUTION_INDEX_TABLE_NAME', executionIndexTable.tableName);

// Grant Step Functions permissions to read tags
const indexSfnPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: ['states:ListTagsForResource'],
  resources: ['*'],
});
backend.indexStepFunctionExecution.resources.lambda.addToRolePolicy(indexSfnPolicy);

// Grant permissions to listExecutionsFromIndex Lambda
executionIndexTable.grantReadData(backend.listExecutionsFromIndex.resources.lambda);
backend.listExecutionsFromIndex.addEnvironment('EXECUTION_INDEX_TABLE_NAME', executionIndexTable.tableName);

// Create EventBridge rule in the data stack to capture ALL Step Functions execution events
// The Lambda will filter by tags to only index agent executions
const dataStack = backend.data.resources.cfnResources.cfnGraphqlApi.stack;
const executionEventRule = new Rule(dataStack, 'ExecutionEventRule', {
  ruleName: `step-functions-execution-index-${uiTableEnvSuffix}`,
  description: 'Capture Step Functions execution events for indexing (filters by tags)',
  eventPattern: {
    source: ['aws.states'],
    detailType: ['Step Functions Execution Status Change'],
    detail: {
      status: ['RUNNING', 'SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED'],
    },
  },
});

// Add Lambda as target
executionEventRule.addTarget(
  new LambdaFunction(backend.indexStepFunctionExecution.resources.lambda, {
    retryAttempts: 2,
  })
);

console.log(`    Created EventBridge rule: ${executionEventRule.ruleName}`);

// Add the tables as data sources to the GraphQL API
backend.data.addDynamoDbDataSource(
  'AgentRegistryDataSource',
  agentRegistryTable
);

backend.data.addDynamoDbDataSource(
  'ToolRegistryDataSource',
  toolRegistryTable
);

backend.data.addDynamoDbDataSource(
  'MCPRegistryDataSource',
  mcpRegistryTable
);

backend.data.addDynamoDbDataSource(
  'LLMModelsDataSource',
  llmModelsTable
);

backend.data.addDynamoDbDataSource(
  'TestEventsDataSource',
  testEventsTable
);

backend.data.addDynamoDbDataSource(
  'TestResultsDataSource',
  testResultsTable
);

backend.data.addDynamoDbDataSource(
  'TemplateRegistryDataSource',
  templateRegistryTable
);


// Grant Step Functions permissions to the startAgentExecution Lambda
const stepFunctionsExecutionPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'states:StartExecution',
    'states:ListStateMachines',
    'states:ListTagsForResource'
  ],
  resources: ['*']
});

backend.startAgentExecution.resources.lambda.addToRolePolicy(stepFunctionsExecutionPolicy);

// Grant Step Functions permissions to the listStepFunctionExecutions Lambda
const stepFunctionsListPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'states:ListExecutions',
    'states:ListStateMachines',
    'states:DescribeExecution',
    'states:ListTagsForResource'
  ],
  resources: ['*']
});

backend.listStepFunctionExecutions.resources.lambda.addToRolePolicy(stepFunctionsListPolicy);

// Grant Step Functions permissions to the getStepFunctionExecution Lambda
const stepFunctionsDetailPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'states:DescribeExecution',
    'states:GetExecutionHistory'
  ],
  resources: ['*']
});

backend.getStepFunctionExecution.resources.lambda.addToRolePolicy(stepFunctionsDetailPolicy);

// Grant Step Functions permissions to the getExecutionStatistics Lambda
const stepFunctionsStatsPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'states:ListExecutions',
    'states:ListStateMachines',
    'states:DescribeExecution',
    'states:ListTagsForResource'
  ],
  resources: ['*']
});

backend.getExecutionStatistics.resources.lambda.addToRolePolicy(stepFunctionsStatsPolicy);

// Grant CloudWatch permissions to the getCloudWatchMetrics Lambda
const cloudWatchMetricsPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'cloudwatch:GetMetricData',
    'cloudwatch:GetMetricStatistics',
    'cloudwatch:ListMetrics'
  ],
  resources: ['*']
});

backend.getCloudWatchMetrics.resources.lambda.addToRolePolicy(cloudWatchMetricsPolicy);

// Grant DynamoDB permissions to the getCloudWatchMetrics Lambda for reading model costs
const dynamoDBMetricsPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'dynamodb:ListTables',
    'dynamodb:Scan',
    'dynamodb:GetItem'
  ],
  resources: ['*']
});

backend.getCloudWatchMetrics.resources.lambda.addToRolePolicy(dynamoDBMetricsPolicy);

// Grant permissions to the testToolExecution Lambda
const testToolExecutionPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'dynamodb:GetItem',
    'lambda:InvokeFunction'
  ],
  resources: ['*']
});

backend.testToolExecution.resources.lambda.addToRolePolicy(testToolExecutionPolicy);

// Grant Secrets Manager permissions to the updateProviderAPIKey Lambda
const secretsManagerPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'secretsmanager:GetSecretValue',
    'secretsmanager:PutSecretValue',
    'secretsmanager:CreateSecret',
    'secretsmanager:UpdateSecret'
  ],
  // The secret path includes environment suffix
  // AWS adds a random suffix to the ARN, so we use wildcard
  resources: [`arn:aws:secretsmanager:*:*:secret:/ai-agent/llm-secrets/${envSuffix}*`]
});

backend.updateProviderAPIKey.resources.lambda.addToRolePolicy(secretsManagerPolicy);

// Grant permissions to the getToolSecretValues Lambda
const getToolSecretValuesPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'secretsmanager:GetSecretValue'
  ],
  resources: [`arn:aws:secretsmanager:*:*:secret:/ai-agent/tool-secrets/${envSuffix}*`]
});

backend.getToolSecretValues.resources.lambda.addToRolePolicy(getToolSecretValuesPolicy);

// Grant permissions to the updateToolSecrets Lambda
const updateToolSecretsPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'secretsmanager:GetSecretValue',
    'secretsmanager:UpdateSecret'
  ],
  resources: [`arn:aws:secretsmanager:*:*:secret:/ai-agent/tool-secrets/${envSuffix}*`]
});

backend.updateToolSecrets.resources.lambda.addToRolePolicy(updateToolSecretsPolicy);

// Grant Step Functions permissions to the getStateMachineInfo Lambda
const getStateMachineInfoPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'states:DescribeStateMachine',
    'states:ListStateMachines',
    'states:ListTagsForResource'
  ],
  resources: ['*']
});

backend.getStateMachineInfo.resources.lambda.addToRolePolicy(getStateMachineInfoPolicy);

// Configure registerMCPServer Lambda function
// Grant write permissions to MCP Registry table
mcpRegistryTable.grantWriteData(backend.registerMCPServer.resources.lambda);
mcpRegistryTable.grantReadData(backend.registerMCPServer.resources.lambda);

// Add environment variables using the backend method
backend.registerMCPServer.addEnvironment('MCP_REGISTRY_TABLE_NAME', mcpRegistryTable.tableName);
backend.registerMCPServer.addEnvironment('ENV_NAME', envSuffix);

// Configure executeHealthTest Lambda function
// Grant permissions to test-related tables
testEventsTable.grantReadWriteData(backend.executeHealthTest.resources.lambda);
testResultsTable.grantReadWriteData(backend.executeHealthTest.resources.lambda);
toolRegistryTable.grantReadData(backend.executeHealthTest.resources.lambda);
agentRegistryTable.grantReadData(backend.executeHealthTest.resources.lambda);

// Grant permissions to invoke Lambda functions and Step Functions
const executeHealthTestPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'lambda:InvokeFunction',
    'states:StartExecution',
    'states:DescribeExecution'
  ],
  resources: ['*']
});

backend.executeHealthTest.resources.lambda.addToRolePolicy(executeHealthTestPolicy);

// Grant DynamoDB permissions to API key management Lambda functions
const apiKeyTablePolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'dynamodb:PutItem',
    'dynamodb:GetItem',
    'dynamodb:UpdateItem',
    'dynamodb:Query',
    'dynamodb:Scan'
  ],
  resources: ['*'] // Will be restricted to specific API key table
});

// API key function permissions - commented out until functions are implemented
// backend.generateAPIKey.resources.lambda.addToRolePolicy(apiKeyTablePolicy);
// backend.revokeAPIKey.resources.lambda.addToRolePolicy(apiKeyTablePolicy);
// backend.rotateAPIKey.resources.lambda.addToRolePolicy(apiKeyTablePolicy);
// backend.listAPIKeys.resources.lambda.addToRolePolicy(apiKeyTablePolicy);

// Create MCP server resources for n8n integration
// In sandbox mode, use a unique suffix to avoid conflicts with production MCP resources
const mcpEnvSuffix = process.env.AWS_BRANCH === 'main' ? envSuffix : `sandbox-${userName}`;
const mcpResources = createMcpServerResources(backend, mcpEnvSuffix);

// Add environment variables for API key management functions to access the table
// const apiKeyTableName = `step-functions-agents-prod-api-keys`; // Use prod to match other stacks
// backend.generateAPIKey.addEnvironment('API_KEY_TABLE_NAME', apiKeyTableName);
// backend.revokeAPIKey.addEnvironment('API_KEY_TABLE_NAME', apiKeyTableName);
// backend.rotateAPIKey.addEnvironment('API_KEY_TABLE_NAME', apiKeyTableName);
// backend.listAPIKeys.addEnvironment('API_KEY_TABLE_NAME', apiKeyTableName);

// Export MCP resources for external access if needed
export { mcpResources };
