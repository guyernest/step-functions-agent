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
import { registerMCPServer } from '../backend/function/registerMCPServer/resource';
import { executeHealthTest } from '../backend/function/executeHealthTest/resource';
import { listExecutionsFromIndex } from '../backend/function/listExecutionsFromIndex/resource';
// API Key management functions - to be implemented if needed
// import { generateAPIKey } from '../backend/function/generateAPIKey/resource';
// import { revokeAPIKey } from '../backend/function/revokeAPIKey/resource';
// import { rotateAPIKey } from '../backend/function/rotateAPIKey/resource';
// import { listAPIKeys } from '../backend/function/listAPIKeys/resource';

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
  
  MCPTool: a.customType({
    name: a.string().required(),
    description: a.string(),
    inputSchema: a.json(),
    outputSchema: a.json(),
  }),
  
  MCPServer: a.customType({
    server_id: a.string().required(),
    version: a.string().required(),
    server_name: a.string().required(),
    description: a.string(),
    endpoint_url: a.string().required(),
    protocol_type: a.string().required(),
    authentication_type: a.string().required(),
    api_key_header: a.string(),
    available_tools: a.ref('MCPTool').array(),
    status: a.string().required(),
    health_check_url: a.string(),
    health_check_interval: a.integer(),
    configuration: a.json(),
    metadata: a.json(),
    deployment_stack: a.string(),
    deployment_region: a.string(),
    created_at: a.string().required(),
    updated_at: a.string().required(),
    created_by: a.string(),
  }),
  
  ConnectionTestResult: a.customType({
    success: a.boolean().required(),
    message: a.string().required(),
    response_time: a.integer(),
    server_id: a.string().required(),
    endpoint_url: a.string(),
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
  
  TestEvent: a.customType({
    id: a.string().required(),
    resource_type: a.string().required(),
    resource_id: a.string().required(),
    test_name: a.string().required(),
    description: a.string(),
    test_input: a.json().required(),  // Renamed from 'input' to avoid GraphQL conflicts
    expected_output: a.json(),
    validation_type: a.string(),  // 'exact', 'contains', 'regex', 'schema', 'semantic', 'range', 'ignore'
    validation_config: a.json(),  // Additional configuration for validation (e.g., threshold for semantic, schema definition)
    metadata: a.json(),
    created_at: a.string(),
    updated_at: a.string(),
  }),
  
  TestResult: a.customType({
    test_event_id: a.string().required(),
    executed_at: a.string().required(),
    resource_id: a.string().required(),
    execution_time: a.integer().required(),
    success: a.boolean().required(),
    output: a.json(),
    error: a.string(),
    metadata: a.json(),
  }),
  
  TestExecutionResponse: a.customType({
    success: a.boolean().required(),
    result: a.json(),
    executionTime: a.integer(),
    error: a.string(),
    testEventId: a.string(),
    executionArn: a.string(),
    message: a.string(),
  }),

  Template: a.customType({
    template_id: a.string().required(),
    version: a.string().required(),
    extraction_name: a.string(),
    status: a.string().required(),
    template: a.json().required(),
    variables: a.json(),
    metadata: a.json(),
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
  
  listMCPServersFromRegistry: a
    .query()
    .arguments({})
    .returns(a.ref('MCPServer').array())
    .handler(
      a.handler.custom({
        dataSource: 'MCPRegistryDataSource',
        entry: './listMCPServersFromRegistry.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  getMCPServer: a
    .query()
    .arguments({
      server_id: a.string().required(),
      version: a.string(),
    })
    .returns(a.ref('MCPServer'))
    .handler(
      a.handler.custom({
        dataSource: 'MCPRegistryDataSource',
        entry: './getMCPServer.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  testMCPServerConnection: a
    .query()
    .arguments({
      server_id: a.string().required(),
    })
    .returns(a.ref('ConnectionTestResult'))
    .handler(
      a.handler.custom({
        dataSource: 'MCPRegistryDataSource',
        entry: './testMCPServerConnection.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  registerMCPServer: a
    .mutation()
    .arguments({
      endpoint: a.string().required(),
      environment: a.string(),
    })
    .returns(a.json())
    .handler(a.handler.function(registerMCPServer))
    .authorization((allow) => [allow.authenticated(), allow.publicApiKey()]),
  
  // Test Event Queries
  listTestEvents: a
    .query()
    .arguments({
      resource_type: a.string().required(),
      resource_id: a.string().required(),
    })
    .returns(a.ref('TestEvent').array())
    .handler(
      a.handler.custom({
        dataSource: 'TestEventsDataSource',
        entry: './resolvers/listTestEvents.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  listTestResults: a
    .query()
    .arguments({
      resource_id: a.string().required(),
      limit: a.integer(),
    })
    .returns(a.ref('TestResult').array())
    .handler(
      a.handler.custom({
        dataSource: 'TestResultsDataSource',
        entry: './resolvers/listTestResults.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  // Test Event Mutations
  saveTestEvent: a
    .mutation()
    .arguments({
      resource_type: a.string().required(),
      resource_id: a.string().required(),
      test_name: a.string().required(),
      description: a.string(),
      test_input: a.json().required(),  // Renamed from 'input' to avoid GraphQL conflicts
      expected_output: a.json(),
      validation_type: a.string(),  // 'exact', 'contains', 'regex', 'schema', 'semantic', 'range', 'ignore'
      validation_config: a.json(),  // Additional configuration for validation
      metadata: a.json(),
    })
    .returns(a.ref('TestEvent'))
    .handler(
      a.handler.custom({
        dataSource: 'TestEventsDataSource',
        entry: './resolvers/saveTestEvent.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  deleteTestEvent: a
    .mutation()
    .arguments({
      resource_type: a.string().required(),
      id: a.string().required(),
    })
    .returns(a.boolean())
    .handler(
      a.handler.custom({
        dataSource: 'TestEventsDataSource',
        entry: './resolvers/deleteTestEvent.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),
  
  executeToolTest: a
    .mutation()
    .arguments({
      tool_name: a.string().required(),
      test_event_id: a.string(),
      custom_input: a.json(),
    })
    .returns(a.ref('TestExecutionResponse'))
    .handler(a.handler.function(executeHealthTest))
    .authorization((allow) => [allow.authenticated()]),
  
  executeAgentTest: a
    .mutation()
    .arguments({
      agent_name: a.string().required(),
      prompt: a.string().required(),
      auto_approve: a.boolean(),
      provider_override: a.string(),
      model_override: a.string(),
    })
    .returns(a.ref('TestExecutionResponse'))
    .handler(a.handler.function(executeHealthTest))
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
      maxResults: a.integer(),
      nextToken: a.string(),
      agentName: a.string(),
      startDateFrom: a.string(),
      startDateTo: a.string()
    })
    .returns(a.json())
    .handler(a.handler.function(listStepFunctionExecutions))
    .authorization((allow) => [
      allow.authenticated(),
      allow.publicApiKey()
    ]),

  listExecutionsFromIndex: a
    .query()
    .arguments({
      agentName: a.string(),
      status: a.string(),
      startDateFrom: a.string(),
      startDateTo: a.string(),
      maxResults: a.integer(),
      nextToken: a.string()
    })
    .returns(a.json())
    .handler(a.handler.function(listExecutionsFromIndex))
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

  getAgentTemplate: a
    .query()
    .arguments({
      template_id: a.string().required(),
      version: a.string(),
    })
    .returns(a.ref('Template'))
    .handler(
      a.handler.custom({
        dataSource: 'TemplateRegistryDataSource',
        entry: './getAgentTemplate.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),

  listTemplatesByAgent: a
    .query()
    .arguments({
      agent_name: a.string().required(),
    })
    .returns(a.ref('Template').array())
    .handler(
      a.handler.custom({
        dataSource: 'TemplateRegistryDataSource',
        entry: './listTemplatesByAgent.js',
      })
    )
    .authorization((allow) => [allow.authenticated()]),

  // API Key Management Operations - commented out until functions are implemented
  // generateAPIKey: a
  //   .mutation()
  //   .arguments({
  //     clientName: a.string().required(),
  //     clientId: a.string().required(),
  //     expiresInDays: a.integer(),
  //     permissions: a.string().array()
  //   })
  //   .returns(a.json()) // Returns the actual API key - only shown once
  //   .handler(a.handler.function(generateAPIKey))
  //   .authorization((allow) => [allow.authenticated()]),

  // listAPIKeys: a
  //   .query()
  //   .arguments({})
  //   .returns(a.ref('ApiKey').array())
  //   .handler(a.handler.function(listAPIKeys))
  //   .authorization((allow) => [allow.authenticated()]),

  // revokeAPIKey: a
  //   .mutation()
  //   .arguments({
  //     keyId: a.string().required()
  //   })
  //   .returns(a.json())
  //   .handler(a.handler.function(revokeAPIKey))
  //   .authorization((allow) => [allow.authenticated()]),

  // rotateAPIKey: a
  //   .mutation()
  //   .arguments({
  //     keyId: a.string().required(),
  //     expiresInDays: a.integer()
  //   })
  //   .returns(a.json()) // Returns new API key
  //   .handler(a.handler.function(rotateAPIKey))
  //   .authorization((allow) => [allow.authenticated()]),
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
