/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "./API";
type GeneratedQuery<InputType, OutputType> = string & {
  __generatedQueryInput: InputType;
  __generatedQueryOutput: OutputType;
};

export const getApiKey = /* GraphQL */ `query GetApiKey($id: ID!) {
  getApiKey(id: $id) {
    clientId
    clientName
    createdAt
    createdBy
    expiresAt
    id
    isActive
    keyId
    lastUsed
    metadata
    permissions
    updatedAt
    usageCount
    __typename
  }
}
` as GeneratedQuery<APITypes.GetApiKeyQueryVariables, APITypes.GetApiKeyQuery>;
export const getCloudWatchMetrics = /* GraphQL */ `query GetCloudWatchMetrics(
  $agentName: String
  $endTime: String
  $metricType: String!
  $period: Int
  $startTime: String
) {
  getCloudWatchMetrics(
    agentName: $agentName
    endTime: $endTime
    metricType: $metricType
    period: $period
    startTime: $startTime
  )
}
` as GeneratedQuery<
  APITypes.GetCloudWatchMetricsQueryVariables,
  APITypes.GetCloudWatchMetricsQuery
>;
export const getExecutionStatistics = /* GraphQL */ `query GetExecutionStatistics {
  getExecutionStatistics
}
` as GeneratedQuery<
  APITypes.GetExecutionStatisticsQueryVariables,
  APITypes.GetExecutionStatisticsQuery
>;
export const getModelCost = /* GraphQL */ `query GetModelCost($id: ID!) {
  getModelCost(id: $id) {
    createdAt
    id
    inputPrice
    isActive
    lastUpdated
    modelName
    outputPrice
    updatedAt
    updatedBy
    __typename
  }
}
` as GeneratedQuery<
  APITypes.GetModelCostQueryVariables,
  APITypes.GetModelCostQuery
>;
export const getStateMachineInfo = /* GraphQL */ `query GetStateMachineInfo($agentName: String!) {
  getStateMachineInfo(agentName: $agentName)
}
` as GeneratedQuery<
  APITypes.GetStateMachineInfoQueryVariables,
  APITypes.GetStateMachineInfoQuery
>;
export const getStepFunctionExecution = /* GraphQL */ `query GetStepFunctionExecution($executionArn: String!) {
  getStepFunctionExecution(executionArn: $executionArn)
}
` as GeneratedQuery<
  APITypes.GetStepFunctionExecutionQueryVariables,
  APITypes.GetStepFunctionExecutionQuery
>;
export const getToolSecretValues = /* GraphQL */ `query GetToolSecretValues {
  getToolSecretValues
}
` as GeneratedQuery<
  APITypes.GetToolSecretValuesQueryVariables,
  APITypes.GetToolSecretValuesQuery
>;
export const listAPIKeys = /* GraphQL */ `query ListAPIKeys {
  listAPIKeys {
    clientId
    clientName
    createdAt
    createdBy
    expiresAt
    id
    isActive
    keyId
    lastUsed
    metadata
    permissions
    updatedAt
    usageCount
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListAPIKeysQueryVariables,
  APITypes.ListAPIKeysQuery
>;
export const listAgentsFromRegistry = /* GraphQL */ `query ListAgentsFromRegistry {
  listAgentsFromRegistry {
    createdAt
    description
    id
    llmModel
    llmProvider
    metadata
    name
    observability
    parameters
    status
    systemPrompt
    tools
    type
    version
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListAgentsFromRegistryQueryVariables,
  APITypes.ListAgentsFromRegistryQuery
>;
export const listApiKeys = /* GraphQL */ `query ListApiKeys(
  $filter: ModelApiKeyFilterInput
  $limit: Int
  $nextToken: String
) {
  listApiKeys(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      clientId
      clientName
      createdAt
      createdBy
      expiresAt
      id
      isActive
      keyId
      lastUsed
      metadata
      permissions
      updatedAt
      usageCount
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListApiKeysQueryVariables,
  APITypes.ListApiKeysQuery
>;
export const listLLMModels = /* GraphQL */ `query ListLLMModels {
  listLLMModels {
    created_at
    display_name
    input_price_per_1k
    is_active
    is_default
    max_tokens
    model_id
    output_price_per_1k
    pk
    provider
    supports_tools
    supports_vision
    updated_at
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListLLMModelsQueryVariables,
  APITypes.ListLLMModelsQuery
>;
export const listLLMModelsByProvider = /* GraphQL */ `query ListLLMModelsByProvider($provider: String!) {
  listLLMModelsByProvider(provider: $provider) {
    created_at
    display_name
    input_price_per_1k
    is_active
    is_default
    max_tokens
    model_id
    output_price_per_1k
    pk
    provider
    supports_tools
    supports_vision
    updated_at
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListLLMModelsByProviderQueryVariables,
  APITypes.ListLLMModelsByProviderQuery
>;
export const listModelCosts = /* GraphQL */ `query ListModelCosts(
  $filter: ModelModelCostFilterInput
  $limit: Int
  $nextToken: String
) {
  listModelCosts(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      createdAt
      id
      inputPrice
      isActive
      lastUpdated
      modelName
      outputPrice
      updatedAt
      updatedBy
      __typename
    }
    nextToken
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListModelCostsQueryVariables,
  APITypes.ListModelCostsQuery
>;
export const listStepFunctionExecutions = /* GraphQL */ `query ListStepFunctionExecutions(
  $maxResults: Int
  $stateMachineArn: String
  $status: String
) {
  listStepFunctionExecutions(
    maxResults: $maxResults
    stateMachineArn: $stateMachineArn
    status: $status
  )
}
` as GeneratedQuery<
  APITypes.ListStepFunctionExecutionsQueryVariables,
  APITypes.ListStepFunctionExecutionsQuery
>;
export const listToolSecrets = /* GraphQL */ `query ListToolSecrets {
  listToolSecrets
}
` as GeneratedQuery<
  APITypes.ListToolSecretsQueryVariables,
  APITypes.ListToolSecretsQuery
>;
export const listToolsFromRegistry = /* GraphQL */ `query ListToolsFromRegistry {
  listToolsFromRegistry {
    createdAt
    description
    id
    inputSchema
    lambda_arn
    lambda_function_name
    language
    name
    type
    version
    __typename
  }
}
` as GeneratedQuery<
  APITypes.ListToolsFromRegistryQueryVariables,
  APITypes.ListToolsFromRegistryQuery
>;
