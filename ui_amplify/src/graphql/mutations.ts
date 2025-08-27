/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "./API";
type GeneratedMutation<InputType, OutputType> = string & {
  __generatedMutationInput: InputType;
  __generatedMutationOutput: OutputType;
};

export const addLLMModel = /* GraphQL */ `mutation AddLLMModel(
  $display_name: String!
  $input_price_per_1k: Float!
  $is_default: Boolean
  $max_tokens: Int
  $model_id: String!
  $output_price_per_1k: Float!
  $provider: String!
  $supports_tools: Boolean
  $supports_vision: Boolean
) {
  addLLMModel(
    display_name: $display_name
    input_price_per_1k: $input_price_per_1k
    is_default: $is_default
    max_tokens: $max_tokens
    model_id: $model_id
    output_price_per_1k: $output_price_per_1k
    provider: $provider
    supports_tools: $supports_tools
    supports_vision: $supports_vision
  )
}
` as GeneratedMutation<
  APITypes.AddLLMModelMutationVariables,
  APITypes.AddLLMModelMutation
>;
export const createApiKey = /* GraphQL */ `mutation CreateApiKey(
  $condition: ModelApiKeyConditionInput
  $input: CreateApiKeyInput!
) {
  createApiKey(condition: $condition, input: $input) {
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
` as GeneratedMutation<
  APITypes.CreateApiKeyMutationVariables,
  APITypes.CreateApiKeyMutation
>;
export const createModelCost = /* GraphQL */ `mutation CreateModelCost(
  $condition: ModelModelCostConditionInput
  $input: CreateModelCostInput!
) {
  createModelCost(condition: $condition, input: $input) {
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
` as GeneratedMutation<
  APITypes.CreateModelCostMutationVariables,
  APITypes.CreateModelCostMutation
>;
export const deleteApiKey = /* GraphQL */ `mutation DeleteApiKey(
  $condition: ModelApiKeyConditionInput
  $input: DeleteApiKeyInput!
) {
  deleteApiKey(condition: $condition, input: $input) {
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
` as GeneratedMutation<
  APITypes.DeleteApiKeyMutationVariables,
  APITypes.DeleteApiKeyMutation
>;
export const deleteLLMModel = /* GraphQL */ `mutation DeleteLLMModel($pk: String!) {
  deleteLLMModel(pk: $pk)
}
` as GeneratedMutation<
  APITypes.DeleteLLMModelMutationVariables,
  APITypes.DeleteLLMModelMutation
>;
export const deleteModelCost = /* GraphQL */ `mutation DeleteModelCost(
  $condition: ModelModelCostConditionInput
  $input: DeleteModelCostInput!
) {
  deleteModelCost(condition: $condition, input: $input) {
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
` as GeneratedMutation<
  APITypes.DeleteModelCostMutationVariables,
  APITypes.DeleteModelCostMutation
>;
export const generateAPIKey = /* GraphQL */ `mutation GenerateAPIKey(
  $clientId: String!
  $clientName: String!
  $expiresInDays: Int
  $permissions: [String]
) {
  generateAPIKey(
    clientId: $clientId
    clientName: $clientName
    expiresInDays: $expiresInDays
    permissions: $permissions
  )
}
` as GeneratedMutation<
  APITypes.GenerateAPIKeyMutationVariables,
  APITypes.GenerateAPIKeyMutation
>;
export const revokeAPIKey = /* GraphQL */ `mutation RevokeAPIKey($keyId: String!) {
  revokeAPIKey(keyId: $keyId)
}
` as GeneratedMutation<
  APITypes.RevokeAPIKeyMutationVariables,
  APITypes.RevokeAPIKeyMutation
>;
export const rotateAPIKey = /* GraphQL */ `mutation RotateAPIKey($expiresInDays: Int, $keyId: String!) {
  rotateAPIKey(expiresInDays: $expiresInDays, keyId: $keyId)
}
` as GeneratedMutation<
  APITypes.RotateAPIKeyMutationVariables,
  APITypes.RotateAPIKeyMutation
>;
export const startAgentExecution = /* GraphQL */ `mutation StartAgentExecution(
  $agentName: String!
  $executionName: String
  $input: String
) {
  startAgentExecution(
    agentName: $agentName
    executionName: $executionName
    input: $input
  )
}
` as GeneratedMutation<
  APITypes.StartAgentExecutionMutationVariables,
  APITypes.StartAgentExecutionMutation
>;
export const testToolExecution = /* GraphQL */ `mutation TestToolExecution(
  $logLevel: String
  $testInput: String!
  $toolName: String!
) {
  testToolExecution(
    logLevel: $logLevel
    testInput: $testInput
    toolName: $toolName
  )
}
` as GeneratedMutation<
  APITypes.TestToolExecutionMutationVariables,
  APITypes.TestToolExecutionMutation
>;
export const updateAgentModel = /* GraphQL */ `mutation UpdateAgentModel(
  $agentName: String!
  $modelId: String!
  $version: String!
) {
  updateAgentModel(agentName: $agentName, modelId: $modelId, version: $version)
}
` as GeneratedMutation<
  APITypes.UpdateAgentModelMutationVariables,
  APITypes.UpdateAgentModelMutation
>;
export const updateAgentProviderAndModel = /* GraphQL */ `mutation UpdateAgentProviderAndModel(
  $agentName: String!
  $modelId: String!
  $provider: String!
  $version: String!
) {
  updateAgentProviderAndModel(
    agentName: $agentName
    modelId: $modelId
    provider: $provider
    version: $version
  )
}
` as GeneratedMutation<
  APITypes.UpdateAgentProviderAndModelMutationVariables,
  APITypes.UpdateAgentProviderAndModelMutation
>;
export const updateAgentSystemPrompt = /* GraphQL */ `mutation UpdateAgentSystemPrompt(
  $agentName: String!
  $systemPrompt: String!
  $version: String!
) {
  updateAgentSystemPrompt(
    agentName: $agentName
    systemPrompt: $systemPrompt
    version: $version
  )
}
` as GeneratedMutation<
  APITypes.UpdateAgentSystemPromptMutationVariables,
  APITypes.UpdateAgentSystemPromptMutation
>;
export const updateApiKey = /* GraphQL */ `mutation UpdateApiKey(
  $condition: ModelApiKeyConditionInput
  $input: UpdateApiKeyInput!
) {
  updateApiKey(condition: $condition, input: $input) {
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
` as GeneratedMutation<
  APITypes.UpdateApiKeyMutationVariables,
  APITypes.UpdateApiKeyMutation
>;
export const updateLLMModel = /* GraphQL */ `mutation UpdateLLMModel(
  $display_name: String
  $input_price_per_1k: Float
  $is_active: String
  $is_default: Boolean
  $max_tokens: Int
  $output_price_per_1k: Float
  $pk: String!
  $supports_tools: Boolean
  $supports_vision: Boolean
) {
  updateLLMModel(
    display_name: $display_name
    input_price_per_1k: $input_price_per_1k
    is_active: $is_active
    is_default: $is_default
    max_tokens: $max_tokens
    output_price_per_1k: $output_price_per_1k
    pk: $pk
    supports_tools: $supports_tools
    supports_vision: $supports_vision
  )
}
` as GeneratedMutation<
  APITypes.UpdateLLMModelMutationVariables,
  APITypes.UpdateLLMModelMutation
>;
export const updateModelCost = /* GraphQL */ `mutation UpdateModelCost(
  $condition: ModelModelCostConditionInput
  $input: UpdateModelCostInput!
) {
  updateModelCost(condition: $condition, input: $input) {
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
` as GeneratedMutation<
  APITypes.UpdateModelCostMutationVariables,
  APITypes.UpdateModelCostMutation
>;
export const updateProviderAPIKey = /* GraphQL */ `mutation UpdateProviderAPIKey($apiKey: String!, $provider: String!) {
  updateProviderAPIKey(apiKey: $apiKey, provider: $provider)
}
` as GeneratedMutation<
  APITypes.UpdateProviderAPIKeyMutationVariables,
  APITypes.UpdateProviderAPIKeyMutation
>;
export const updateToolSecrets = /* GraphQL */ `mutation UpdateToolSecrets($secrets: AWSJSON!, $toolName: String!) {
  updateToolSecrets(secrets: $secrets, toolName: $toolName)
}
` as GeneratedMutation<
  APITypes.UpdateToolSecretsMutationVariables,
  APITypes.UpdateToolSecretsMutation
>;
