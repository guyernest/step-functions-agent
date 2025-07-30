import { type ClientSchema, a, defineData } from '@aws-amplify/backend';
import { listAgentsFromRegistry } from '../backend/function/listAgentsFromRegistry/resource';
import { startAgentExecution } from '../backend/function/startAgentExecution/resource';

const schema = a.schema({
  // Non-model types for registry items
  Agent: a.customType({
    id: a.string().required(),
    name: a.string().required(),
    version: a.string().required(),
    description: a.string(),
    tools: a.string().array(),
    status: a.string(),
    capabilities: a.json(),
    maxIterations: a.integer(),
  }),

  // Step Functions Execution Types
  StepFunctionExecution: a.customType({
    executionArn: a.string().required(),
    name: a.string().required(),
    stateMachineArn: a.string().required(),
    status: a.string().required(),
    startDate: a.string().required(),
    stopDate: a.string(),
    input: a.json(),
    output: a.json(),
    error: a.string(),
  }),

  // Custom queries
  listAgentsFromRegistry: a
    .query()
    .returns(a.ref('Agent').array())
    .handler(a.handler.function(listAgentsFromRegistry))
    .authorization((allow) => [allow.authenticated()]),

  // Custom mutations
  startAgentExecution: a
    .mutation()
    .arguments({
      agentName: a.string().required(),
      prompt: a.string().required(),
      systemPrompt: a.string(),
      llmConfig: a.json(),
    })
    .returns(a.ref('StepFunctionExecution'))
    .handler(a.handler.function(startAgentExecution))
    .authorization((allow) => [allow.authenticated()]),
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  name: 'StepFunctionsAgentAPI',
  authorizationModes: {
    defaultAuthorizationMode: 'userPool',
    apiKeyAuthorizationMode: {
      expiresInDays: 30,
    },
  },
});