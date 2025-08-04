import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { startAgentExecution } from './backend/function/startAgentExecution/resource';
import { listStepFunctionExecutions } from './backend/function/listStepFunctionExecutions/resource';
import { getStepFunctionExecution } from './backend/function/getStepFunctionExecution/resource';
import { getExecutionStatistics } from './backend/function/getExecutionStatistics/resource';
import { PolicyStatement, Effect, Policy } from 'aws-cdk-lib/aws-iam';
import { aws_dynamodb } from 'aws-cdk-lib';

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

// Reference the existing DynamoDB tables
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

// Add the tables as data sources to the GraphQL API
backend.data.addDynamoDbDataSource(
  'AgentRegistryDataSource',
  agentRegistryTable
);

backend.data.addDynamoDbDataSource(
  'ToolRegistryDataSource',
  toolRegistryTable
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
