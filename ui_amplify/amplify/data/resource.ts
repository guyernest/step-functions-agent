import { type ClientSchema, a, defineData } from '@aws-amplify/backend';
import { listAgentsFromRegistry } from '../backend/function/listAgentsFromRegistry/resource';
import { listToolsFromRegistry } from '../backend/function/listToolsFromRegistry/resource';
import { startAgentExecution } from '../backend/function/startAgentExecution/resource';
import { listStepFunctionExecutions } from '../backend/function/listStepFunctionExecutions/resource';
import { getStepFunctionExecution } from '../backend/function/getStepFunctionExecution/resource';
import { getExecutionStatistics } from '../backend/function/getExecutionStatistics/resource';

const schema = a.schema({
  Todo: a
    .model({
      content: a.string(),
    })
    .authorization((allow) => [allow.guest()]),
  
  listAgentsFromRegistry: a
    .query()
    .arguments({
      tableName: a.string()
    })
    .returns(a.json())
    .handler(a.handler.function(listAgentsFromRegistry))
    .authorization((allow) => [allow.authenticated()]),
  
  listToolsFromRegistry: a
    .query()
    .arguments({
      tableName: a.string()
    })
    .returns(a.json())
    .handler(a.handler.function(listToolsFromRegistry))
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
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
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
