import { type ClientSchema, a, defineData } from '@aws-amplify/backend';
import { listAgentsFromRegistry } from '../backend/function/listAgentsFromRegistry/resource';
import { listToolsFromRegistry } from '../backend/function/listToolsFromRegistry/resource';
import { startAgentExecution } from '../backend/function/startAgentExecution/resource';
// import { listStepFunctionExecutions } from '../backend/function/listStepFunctionExecutions/resource';
// import { getStepFunctionExecution } from '../backend/function/getStepFunctionExecution/resource';
// import { getExecutionHistory } from '../backend/function/getExecutionHistory/resource';

const schema = a.schema({
  // Configuration Management
  Configuration: a
    .model({
      environment: a.string().required(),
      resources: a.json().required(),
      secrets: a.json(),
      features: a.json(),
      lastUpdatedBy: a.string(),
      version: a.integer(),
    })
    .authorization((allow) => [allow.authenticated()]),

  ConfigurationHistory: a
    .model({
      configurationId: a.id(),
      changeType: a.string(),
      previousValue: a.json(),
      newValue: a.json(),
      changedBy: a.string(),
      reason: a.string(),
    })
    .authorization((allow) => [allow.authenticated()]),

  // Step Functions Execution Types (read-only from Step Functions)
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

  ExecutionHistory: a.customType({
    events: a.json().required(),
    nextToken: a.string(),
  }),

  // Metrics
  Metric: a
    .model({
      namespace: a.string().required(),
      metricName: a.string().required(),
      dimensions: a.json(),
      value: a.float().required(),
      unit: a.string(),
      timestamp: a.datetime().required(),
    })
    .authorization((allow) => [allow.authenticated()]),

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

  Tool: a.customType({
    id: a.string().required(),
    name: a.string().required(),
    version: a.string().required(),
    description: a.string(),
    inputSchema: a.json(),
    outputSchema: a.json(),
    status: a.string(),
  }),

  // Custom queries
  listAgentsFromRegistry: a
    .query()
    .returns(a.ref('Agent').array())
    .handler(a.handler.function(listAgentsFromRegistry))
    .authorization((allow) => [allow.authenticated()]),

  listToolsFromRegistry: a
    .query()
    .returns(a.ref('Tool').array())
    .handler(a.handler.function(listToolsFromRegistry))
    .authorization((allow) => [allow.authenticated()]),

  // Step Functions queries - commented out for now
  // listStepFunctionExecutions: a
  //   .query()
  //   .arguments({
  //     stateMachineArn: a.string(),
  //     statusFilter: a.string(),
  //     maxResults: a.integer(),
  //     nextToken: a.string(),
  //   })
  //   .returns(a.ref('StepFunctionExecution').array())
  //   .handler(a.handler.function(listStepFunctionExecutions))
  //   .authorization((allow) => [allow.authenticated()]),

  // getStepFunctionExecution: a
  //   .query()
  //   .arguments({
  //     executionArn: a.string().required(),
  //   })
  //   .returns(a.ref('StepFunctionExecution'))
  //   .handler(a.handler.function(getStepFunctionExecution))
  //   .authorization((allow) => [allow.authenticated()]),

  // getExecutionHistory: a
  //   .query()
  //   .arguments({
  //     executionArn: a.string().required(),
  //     maxResults: a.integer(),
  //     nextToken: a.string(),
  //   })
  //   .returns(a.ref('ExecutionHistory'))
  //   .handler(a.handler.function(getExecutionHistory))
  //   .authorization((allow) => [allow.authenticated()]),

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

/*== STEP 2 ===============================================================
Go to your frontend source code. From your client-side code, generate a
Data client to make CRUDL requests to your table. (THIS SNIPPET WILL ONLY
WORK IN THE FRONTEND CODE FILE.)

Using JavaScript or Next.js React Server Components, Middleware, Server 
Actions or Pages Router? Review how to generate Data clients for those use
cases: https://docs.amplify.aws/gen2/build-a-backend/data/connect-to-API/
=========================================================================*/

/*
"use client"
import { generateClient } from "aws-amplify/data";
import type { Schema } from "@/amplify/data/resource";

const client = generateClient<Schema>() // use this Data client for CRUDL requests
*/

/*== STEP 3 ===============================================================
Fetch records from the database and use them in your frontend component.
(THIS SNIPPET WILL ONLY WORK IN THE FRONTEND CODE FILE.)
=========================================================================*/

/* For example, in a React component, you can use this snippet in your
  function's RETURN statement */
// const { data: todos } = await client.models.Todo.list()

// return <ul>{todos.map(todo => <li key={todo.id}>{todo.content}</li>)}</ul>
