import { type ClientSchema, a, defineData } from '@aws-amplify/backend';
import { startAgentExecution } from '../backend/function/startAgentExecution/resource';
import { listStepFunctionExecutions } from '../backend/function/listStepFunctionExecutions/resource';
import { getStepFunctionExecution } from '../backend/function/getStepFunctionExecution/resource';
import { getExecutionStatistics } from '../backend/function/getExecutionStatistics/resource';
import { getCloudWatchMetrics } from '../backend/function/getCloudWatchMetrics/resource';
import { testToolExecution } from '../backend/function/testToolExecution/resource';
import { updateProviderAPIKey } from '../backend/function/updateProviderAPIKey/resource';
import { getToolSecretValues } from '../backend/function/getToolSecretValues/resource';
import { updateToolSecrets } from '../backend/function/updateToolSecrets/resource';
import { getStateMachineInfo } from '../backend/function/getStateMachineInfo/resource';
import { generateAPIKey } from '../backend/function/generateAPIKey/resource';
import { revokeAPIKey } from '../backend/function/revokeAPIKey/resource';
import { rotateAPIKey } from '../backend/function/rotateAPIKey/resource';
import { listAPIKeys } from '../backend/function/listAPIKeys/resource';

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

  // Model for storing API keys for n8n integration
  ApiKey: a
    .model({
      keyId: a.string().required(), // Short identifier (first 8 chars of hash)
      clientName: a.string().required(),
      clientId: a.string().required(),
      createdAt: a.datetime(),
      expiresAt: a.datetime(),
      lastUsed: a.datetime(),
      isActive: a.boolean().default(true),
      permissions: a.string().array(),
      usageCount: a.integer().default(0),
      createdBy: a.string().required(),
      metadata: a.json(),
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
    language: a.string(),
    lambda_function_name: a.string(),
    lambda_arn: a.string(),
    inputSchema: a.string(),
  }),
  
  LLMModel: a.customType({
    pk: a.string().required(),
    provider: a.string().required(),
    model_id: a.string().required(),
    display_name: a.string().required(),
    input_price_per_1k: a.float().required(),
    output_price_per_1k: a.float().required(),
    max_tokens: a.integer(),
    supports_tools: a.boolean(),
    supports_vision: a.boolean(),
    is_active: a.string(),
    is_default: a.boolean(),
    created_at: a.string(),
    updated_at: a.string(),
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
    .authorization((allow) => [
      allow.authenticated(),
      allow.publicApiKey()
    ]),
  
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
    .authorization((allow) => [
      allow.authenticated(),
      allow.publicApiKey()
    ]),
  
  listStepFunctionExecutions: a
    .query()
    .arguments({
      stateMachineArn: a.string(),
      status: a.string(),
      maxResults: a.integer()
    })
    .returns(a.json())
    .handler(a.handler.function(listStepFunctionExecutions))
    .authorization((allow) => [
      allow.authenticated(),
      allow.publicApiKey()
    ]),
  
  getStepFunctionExecution: a
    .query()
    .arguments({
      executionArn: a.string().required()
    })
    .returns(a.json())
    .handler(a.handler.function(getStepFunctionExecution))
    .authorization((allow) => [
      allow.authenticated(),
      allow.publicApiKey()
    ]),
  
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
  
  updateAgentModel: a
    .mutation()
    .arguments({
      agentName: a.string().required(),
      version: a.string().required(),
      modelId: a.string().required()
    })
    .returns(a.json())
    .handler(
      a.handler.custom({
        dataSource: 'AgentRegistryDataSource',
        entry: './updateAgentModel.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  updateAgentProviderAndModel: a
    .mutation()
    .arguments({
      agentName: a.string().required(),
      version: a.string().required(),
      provider: a.string().required(),
      modelId: a.string().required()
    })
    .returns(a.json())
    .handler(
      a.handler.custom({
        dataSource: 'AgentRegistryDataSource',
        entry: './updateAgentProviderAndModel.js',
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
    
  testToolExecution: a
    .mutation()
    .arguments({
      toolName: a.string().required(),
      testInput: a.string().required(),
      logLevel: a.string(),
    })
    .returns(a.json())
    .handler(a.handler.function(testToolExecution))
    .authorization((allow) => [allow.authenticated()]),
    
  listLLMModels: a
    .query()
    .arguments({})
    .returns(a.ref('LLMModel').array())
    .handler(
      a.handler.custom({
        dataSource: 'LLMModelsDataSource',
        entry: './listLLMModels.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
    
  listLLMModelsByProvider: a
    .query()
    .arguments({
      provider: a.string().required(),
    })
    .returns(a.ref('LLMModel').array())
    .handler(
      a.handler.custom({
        dataSource: 'LLMModelsDataSource',
        entry: './listLLMModelsByProvider.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
    
  addLLMModel: a
    .mutation()
    .arguments({
      provider: a.string().required(),
      model_id: a.string().required(),
      display_name: a.string().required(),
      input_price_per_1k: a.float().required(),
      output_price_per_1k: a.float().required(),
      max_tokens: a.integer(),
      supports_tools: a.boolean(),
      supports_vision: a.boolean(),
      is_default: a.boolean()
    })
    .returns(a.json())
    .handler(
      a.handler.custom({
        dataSource: 'LLMModelsDataSource',
        entry: './addLLMModel.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
    
  updateLLMModel: a
    .mutation()
    .arguments({
      pk: a.string().required(),
      display_name: a.string(),
      input_price_per_1k: a.float(),
      output_price_per_1k: a.float(),
      max_tokens: a.integer(),
      supports_tools: a.boolean(),
      supports_vision: a.boolean(),
      is_active: a.string(),
      is_default: a.boolean()
    })
    .returns(a.json())
    .handler(
      a.handler.custom({
        dataSource: 'LLMModelsDataSource',
        entry: './updateLLMModel.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
    
  deleteLLMModel: a
    .mutation()
    .arguments({
      pk: a.string().required()
    })
    .returns(a.json())
    .handler(
      a.handler.custom({
        dataSource: 'LLMModelsDataSource',
        entry: './deleteLLMModel.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
    
  updateProviderAPIKey: a
    .mutation()
    .arguments({
      provider: a.string().required(),
      apiKey: a.string().required()
    })
    .returns(a.json())
    .handler(a.handler.function(updateProviderAPIKey))
    .authorization((allow) => [allow.authenticated()]),
    
  listToolSecrets: a
    .query()
    .arguments({})
    .returns(a.json())
    .handler(
      a.handler.custom({
        dataSource: 'ToolSecretsDataSource',
        entry: './listToolSecrets.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
    
  getToolSecretValues: a
    .query()
    .arguments({})
    .returns(a.json())
    .handler(a.handler.function(getToolSecretValues))
    .authorization((allow) => [allow.authenticated()]),
    
  updateToolSecrets: a
    .mutation()
    .arguments({
      toolName: a.string().required(),
      secrets: a.json().required()
    })
    .returns(a.json())
    .handler(a.handler.function(updateToolSecrets))
    .authorization((allow) => [allow.authenticated()]),
    
  getStateMachineInfo: a
    .query()
    .arguments({
      agentName: a.string().required()
    })
    .returns(a.json())
    .handler(a.handler.function(getStateMachineInfo))
    .authorization((allow) => [allow.authenticated()]),

  // API Key Management Operations (UI only - no API key access)
  generateAPIKey: a
    .mutation()
    .arguments({
      clientName: a.string().required(),
      clientId: a.string().required(),
      expiresInDays: a.integer(),
      permissions: a.string().array()
    })
    .returns(a.json()) // Returns the actual API key - only shown once
    .handler(a.handler.function(generateAPIKey))
    .authorization((allow) => [allow.authenticated()]),

  listAPIKeys: a
    .query()
    .arguments({})
    .returns(a.ref('ApiKey').array())
    .handler(a.handler.function(listAPIKeys))
    .authorization((allow) => [allow.authenticated()]),

  revokeAPIKey: a
    .mutation()
    .arguments({
      keyId: a.string().required()
    })
    .returns(a.json())
    .handler(a.handler.function(revokeAPIKey))
    .authorization((allow) => [allow.authenticated()]),

  rotateAPIKey: a
    .mutation()
    .arguments({
      keyId: a.string().required(),
      expiresInDays: a.integer()
    })
    .returns(a.json()) // Returns new API key
    .handler(a.handler.function(rotateAPIKey))
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
