import { type ClientSchema, a, defineData } from '@aws-amplify/backend';
import { startAgentExecution } from '../backend/function/startAgentExecution/resource';
import { listStepFunctionExecutions } from '../backend/function/listStepFunctionExecutions/resource';
import { getStepFunctionExecution } from '../backend/function/getStepFunctionExecution/resource';
import { getExecutionStatistics } from '../backend/function/getExecutionStatistics/resource';
import { getCloudWatchMetrics } from '../backend/function/getCloudWatchMetrics/resource';

const schema = a.schema({
  // Model for storing custom model costs
  ModelCost: a
    .model({
      modelName: a.string().required(),
      inputPrice: a.float().required(),
      outputPrice: a.float().required(),
      lastUpdated: a.datetime(),
      updatedBy: a.string(),
      isActive: a.boolean().default(true),
    })
    .authorization((allow) => [allow.authenticated()]),
  
  // Custom types for external DynamoDB tables
  Agent: a.customType({
    id: a.string().required(),
    name: a.string().required(),
    description: a.string(),
    version: a.string(),
    type: a.string(),
    createdAt: a.string(),
    tools: a.string().array(),
    systemPrompt: a.string(),
    llmProvider: a.string(),
    llmModel: a.string(),
    status: a.string(),
    parameters: a.string(),
    metadata: a.string(),
    observability: a.string(),
  }),
  
  Tool: a.customType({
    id: a.string().required(),
    name: a.string().required(),
    description: a.string(),
    version: a.string(),
    type: a.string(),
    createdAt: a.string(),
  }),
  
  listAgentsFromRegistry: a
    .query()
    .arguments({})
    .returns(a.ref('Agent').array())
    .handler(
      a.handler.custom({
        dataSource: 'AgentRegistryDataSource',
        entry: './listAgentsFromRegistry.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  listToolsFromRegistry: a
    .query()
    .arguments({})
    .returns(a.ref('Tool').array())
    .handler(
      a.handler.custom({
        dataSource: 'ToolRegistryDataSource',
        entry: './listToolsFromRegistry.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  startAgentExecution: a
    .mutation()
    .arguments({
      agentName: a.string().required(),
      input: a.string(),
      executionName: a.string()
    })
    .returns(a.json())
    .handler(a.handler.function(startAgentExecution))
    .authorization((allow) => [allow.authenticated()]),
  
  listStepFunctionExecutions: a
    .query()
    .arguments({
      stateMachineArn: a.string(),
      status: a.string(),
      maxResults: a.integer()
    })
    .returns(a.json())
    .handler(a.handler.function(listStepFunctionExecutions))
    .authorization((allow) => [allow.authenticated()]),
  
  getStepFunctionExecution: a
    .query()
    .arguments({
      executionArn: a.string().required()
    })
    .returns(a.json())
    .handler(a.handler.function(getStepFunctionExecution))
    .authorization((allow) => [allow.authenticated()]),
  
  getExecutionStatistics: a
    .query()
    .arguments({})
    .returns(a.json())
    .handler(a.handler.function(getExecutionStatistics))
    .authorization((allow) => [allow.authenticated()]),
  
  updateAgentSystemPrompt: a
    .mutation()
    .arguments({
      agentName: a.string().required(),
      version: a.string().required(),
      systemPrompt: a.string().required()
    })
    .returns(a.json())
    .handler(
      a.handler.custom({
        dataSource: 'AgentRegistryDataSource',
        entry: './updateAgentSystemPrompt.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  getCloudWatchMetrics: a
    .query()
    .arguments({
      metricType: a.string().required(),
      startTime: a.string(),
      endTime: a.string(),
      period: a.integer(),
      agentName: a.string()
    })
    .returns(a.json())
    .handler(a.handler.function(getCloudWatchMetrics))
    .authorization((allow) => [allow.authenticated()]),
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  name: 'StepFunctionsAgentFramework',
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
// const { data: agents } = await client.queries.listAgentsFromRegistry()

// return <ul>{agents.map(agent => <li key={agent.id}>{agent.name}</li>)}</ul>
