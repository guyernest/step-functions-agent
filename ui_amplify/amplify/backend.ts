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
import { PolicyStatement, Effect, Policy } from 'aws-cdk-lib/aws-iam';
import { aws_dynamodb, RemovalPolicy } from 'aws-cdk-lib';

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

// Define table names - always use prod for now
const agentRegistryTableName = 'AgentRegistry-prod';
const toolRegistryTableName = 'ToolRegistry-prod';

// Reference the existing external DynamoDB tables
const agentRegistryTable = aws_dynamodb.Table.fromTableName(
  externalDataSourcesStack,
  'AgentRegistryTable',
  agentRegistryTableName
);

const toolRegistryTable = aws_dynamodb.Table.fromTableName(
  externalDataSourcesStack,
  'ToolRegistryTable',
  toolRegistryTableName
);

// Reference the ToolSecrets table
const toolSecretsTable = aws_dynamodb.Table.fromTableName(
  externalDataSourcesStack,
  'ToolSecretsTable',
  'ToolSecrets-prod'
);

// Create the LLMModels table as part of this stack
const llmModelsTable = new aws_dynamodb.Table(externalDataSourcesStack, 'LLMModelsTable', {
  tableName: 'LLMModels-prod',
  partitionKey: { name: 'pk', type: aws_dynamodb.AttributeType.STRING },
  billingMode: aws_dynamodb.BillingMode.PAY_PER_REQUEST,
  pointInTimeRecovery: true,
  removalPolicy: RemovalPolicy.RETAIN
});

// Add Global Secondary Index for provider queries
llmModelsTable.addGlobalSecondaryIndex({
  indexName: 'provider-index',
  partitionKey: { name: 'provider', type: aws_dynamodb.AttributeType.STRING },
  sortKey: { name: 'is_active', type: aws_dynamodb.AttributeType.STRING },
  projectionType: aws_dynamodb.ProjectionType.ALL
});

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
  'LLMModelsDataSource',
  llmModelsTable
);

backend.data.addDynamoDbDataSource(
  'ToolSecretsDataSource',
  toolSecretsTable
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
  // The secret is at /ai-agent/llm-secrets/prod (not a prefix)
  // AWS adds a random suffix to the ARN, so we use wildcard
  resources: ['arn:aws:secretsmanager:*:*:secret:/ai-agent/llm-secrets/prod*']
});

backend.updateProviderAPIKey.resources.lambda.addToRolePolicy(secretsManagerPolicy);

// Grant permissions to the getToolSecretValues Lambda
const getToolSecretValuesPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'secretsmanager:GetSecretValue'
  ],
  resources: ['arn:aws:secretsmanager:*:*:secret:/ai-agent/tool-secrets/prod*']
});

backend.getToolSecretValues.resources.lambda.addToRolePolicy(getToolSecretValuesPolicy);

// Grant permissions to the updateToolSecrets Lambda
const updateToolSecretsPolicy = new PolicyStatement({
  effect: Effect.ALLOW,
  actions: [
    'secretsmanager:GetSecretValue',
    'secretsmanager:UpdateSecret'
  ],
  resources: ['arn:aws:secretsmanager:*:*:secret:/ai-agent/tool-secrets/prod*']
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
