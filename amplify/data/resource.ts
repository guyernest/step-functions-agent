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

  // Execution response type
  ExecutionResponse: a.customType({
    executionArn: a.string().required(),
    executionName: a.string().required(),
    startDate: a.string().required(),
    status: a.string().required(),
    agentName: a.string().required(),
    agentVersion: a.string().required(),
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
      input: a.json(),
    })
    .returns(a.ref('ExecutionResponse'))
    .handler(a.handler.function(startAgentExecution))
    .authorization((allow) => [allow.authenticated()]),
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'userPool',
  },
});