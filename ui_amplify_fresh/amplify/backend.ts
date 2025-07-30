import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { listAgentsFromRegistry } from './backend/function/listAgentsFromRegistry/resource';
import { startAgentExecution } from './backend/function/startAgentExecution/resource';
import { Stack } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';

/**
 * @see https://docs.amplify.aws/react/build-a-backend/ to add storage, functions, and more
 */
const backend = defineBackend({
  auth,
  data,
  listAgentsFromRegistry,
  startAgentExecution,
});

// Grant permissions to Lambda functions
backend.addOutput({
  custom: {
    awsRegion: Stack.of(backend.data).region,
  },
});

// Grant DynamoDB permissions to listAgentsFromRegistry
backend.listAgentsFromRegistry.resources.lambda.addToRolePolicy(
  new iam.PolicyStatement({
    actions: ['dynamodb:Scan', 'dynamodb:Query', 'dynamodb:GetItem'],
    resources: ['arn:aws:dynamodb:*:*:table/AgentRegistry-prod*'],
  })
);

// Grant permissions to startAgentExecution
backend.startAgentExecution.resources.lambda.addToRolePolicy(
  new iam.PolicyStatement({
    actions: [
      'dynamodb:GetItem',
      'dynamodb:Query',
      'dynamodb:Scan'
    ],
    resources: [
      'arn:aws:dynamodb:*:*:table/AgentRegistry-prod*'
    ],
  })
);

backend.startAgentExecution.resources.lambda.addToRolePolicy(
  new iam.PolicyStatement({
    actions: [
      'states:StartExecution',
      'states:DescribeStateMachine',
      'states:ListStateMachines'
    ],
    resources: ['arn:aws:states:*:*:stateMachine:*'],
  })
);