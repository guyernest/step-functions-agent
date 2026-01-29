/* tslint:disable */
/* eslint-disable */
//  This file was automatically generated and should not be edited.

export type ApiKey = {
  __typename: "ApiKey",
  clientId: string,
  clientName: string,
  createdAt?: string | null,
  createdBy: string,
  expiresAt?: string | null,
  id: string,
  isActive?: boolean | null,
  keyId: string,
  lastUsed?: string | null,
  metadata?: string | null,
  permissions?: Array< string | null > | null,
  updatedAt: string,
  usageCount?: number | null,
};

export type ModelCost = {
  __typename: "ModelCost",
  createdAt: string,
  id: string,
  inputPrice: number,
  isActive?: boolean | null,
  lastUpdated?: string | null,
  modelName: string,
  outputPrice: number,
  updatedAt: string,
  updatedBy?: string | null,
};

export type Agent = {
  __typename: "Agent",
  createdAt?: string | null,
  description?: string | null,
  id: string,
  llmModel?: string | null,
  llmProvider?: string | null,
  metadata?: string | null,
  name: string,
  observability?: string | null,
  parameters?: string | null,
  status?: string | null,
  systemPrompt?: string | null,
  tools?: Array< string | null > | null,
  type?: string | null,
  version?: string | null,
};

export type ModelApiKeyFilterInput = {
  and?: Array< ModelApiKeyFilterInput | null > | null,
  clientId?: ModelStringInput | null,
  clientName?: ModelStringInput | null,
  createdAt?: ModelStringInput | null,
  createdBy?: ModelStringInput | null,
  expiresAt?: ModelStringInput | null,
  id?: ModelIDInput | null,
  isActive?: ModelBooleanInput | null,
  keyId?: ModelStringInput | null,
  lastUsed?: ModelStringInput | null,
  metadata?: ModelStringInput | null,
  not?: ModelApiKeyFilterInput | null,
  or?: Array< ModelApiKeyFilterInput | null > | null,
  permissions?: ModelStringInput | null,
  updatedAt?: ModelStringInput | null,
  usageCount?: ModelIntInput | null,
};

export type ModelStringInput = {
  attributeExists?: boolean | null,
  attributeType?: ModelAttributeTypes | null,
  beginsWith?: string | null,
  between?: Array< string | null > | null,
  contains?: string | null,
  eq?: string | null,
  ge?: string | null,
  gt?: string | null,
  le?: string | null,
  lt?: string | null,
  ne?: string | null,
  notContains?: string | null,
  size?: ModelSizeInput | null,
};

export enum ModelAttributeTypes {
  _null = "_null",
  binary = "binary",
  binarySet = "binarySet",
  bool = "bool",
  list = "list",
  map = "map",
  number = "number",
  numberSet = "numberSet",
  string = "string",
  stringSet = "stringSet",
}


export type ModelSizeInput = {
  between?: Array< number | null > | null,
  eq?: number | null,
  ge?: number | null,
  gt?: number | null,
  le?: number | null,
  lt?: number | null,
  ne?: number | null,
};

export type ModelIDInput = {
  attributeExists?: boolean | null,
  attributeType?: ModelAttributeTypes | null,
  beginsWith?: string | null,
  between?: Array< string | null > | null,
  contains?: string | null,
  eq?: string | null,
  ge?: string | null,
  gt?: string | null,
  le?: string | null,
  lt?: string | null,
  ne?: string | null,
  notContains?: string | null,
  size?: ModelSizeInput | null,
};

export type ModelBooleanInput = {
  attributeExists?: boolean | null,
  attributeType?: ModelAttributeTypes | null,
  eq?: boolean | null,
  ne?: boolean | null,
};

export type ModelIntInput = {
  attributeExists?: boolean | null,
  attributeType?: ModelAttributeTypes | null,
  between?: Array< number | null > | null,
  eq?: number | null,
  ge?: number | null,
  gt?: number | null,
  le?: number | null,
  lt?: number | null,
  ne?: number | null,
};

export type ModelApiKeyConnection = {
  __typename: "ModelApiKeyConnection",
  items:  Array<ApiKey | null >,
  nextToken?: string | null,
};

export type LLMModel = {
  __typename: "LLMModel",
  created_at?: string | null,
  display_name: string,
  input_price_per_1k: number,
  is_active?: string | null,
  is_default?: boolean | null,
  max_tokens?: number | null,
  model_id: string,
  output_price_per_1k: number,
  pk: string,
  provider: string,
  supports_tools?: boolean | null,
  supports_vision?: boolean | null,
  updated_at?: string | null,
};

export type ModelModelCostFilterInput = {
  and?: Array< ModelModelCostFilterInput | null > | null,
  createdAt?: ModelStringInput | null,
  id?: ModelIDInput | null,
  inputPrice?: ModelFloatInput | null,
  isActive?: ModelBooleanInput | null,
  lastUpdated?: ModelStringInput | null,
  modelName?: ModelStringInput | null,
  not?: ModelModelCostFilterInput | null,
  or?: Array< ModelModelCostFilterInput | null > | null,
  outputPrice?: ModelFloatInput | null,
  updatedAt?: ModelStringInput | null,
  updatedBy?: ModelStringInput | null,
};

export type ModelFloatInput = {
  attributeExists?: boolean | null,
  attributeType?: ModelAttributeTypes | null,
  between?: Array< number | null > | null,
  eq?: number | null,
  ge?: number | null,
  gt?: number | null,
  le?: number | null,
  lt?: number | null,
  ne?: number | null,
};

export type ModelModelCostConnection = {
  __typename: "ModelModelCostConnection",
  items:  Array<ModelCost | null >,
  nextToken?: string | null,
};

export type Tool = {
  __typename: "Tool",
  createdAt?: string | null,
  description?: string | null,
  id: string,
  inputSchema?: string | null,
  lambda_arn?: string | null,
  lambda_function_name?: string | null,
  language?: string | null,
  name: string,
  type?: string | null,
  version?: string | null,
};

export type ModelApiKeyConditionInput = {
  and?: Array< ModelApiKeyConditionInput | null > | null,
  clientId?: ModelStringInput | null,
  clientName?: ModelStringInput | null,
  createdAt?: ModelStringInput | null,
  createdBy?: ModelStringInput | null,
  expiresAt?: ModelStringInput | null,
  isActive?: ModelBooleanInput | null,
  keyId?: ModelStringInput | null,
  lastUsed?: ModelStringInput | null,
  metadata?: ModelStringInput | null,
  not?: ModelApiKeyConditionInput | null,
  or?: Array< ModelApiKeyConditionInput | null > | null,
  permissions?: ModelStringInput | null,
  updatedAt?: ModelStringInput | null,
  usageCount?: ModelIntInput | null,
};

export type CreateApiKeyInput = {
  clientId: string,
  clientName: string,
  createdAt?: string | null,
  createdBy: string,
  expiresAt?: string | null,
  id?: string | null,
  isActive?: boolean | null,
  keyId: string,
  lastUsed?: string | null,
  metadata?: string | null,
  permissions?: Array< string | null > | null,
  usageCount?: number | null,
};

export type ModelModelCostConditionInput = {
  and?: Array< ModelModelCostConditionInput | null > | null,
  createdAt?: ModelStringInput | null,
  inputPrice?: ModelFloatInput | null,
  isActive?: ModelBooleanInput | null,
  lastUpdated?: ModelStringInput | null,
  modelName?: ModelStringInput | null,
  not?: ModelModelCostConditionInput | null,
  or?: Array< ModelModelCostConditionInput | null > | null,
  outputPrice?: ModelFloatInput | null,
  updatedAt?: ModelStringInput | null,
  updatedBy?: ModelStringInput | null,
};

export type CreateModelCostInput = {
  id?: string | null,
  inputPrice: number,
  isActive?: boolean | null,
  lastUpdated?: string | null,
  modelName: string,
  outputPrice: number,
  updatedBy?: string | null,
};

export type DeleteApiKeyInput = {
  id: string,
};

export type DeleteModelCostInput = {
  id: string,
};

export type UpdateApiKeyInput = {
  clientId?: string | null,
  clientName?: string | null,
  createdAt?: string | null,
  createdBy?: string | null,
  expiresAt?: string | null,
  id: string,
  isActive?: boolean | null,
  keyId?: string | null,
  lastUsed?: string | null,
  metadata?: string | null,
  permissions?: Array< string | null > | null,
  usageCount?: number | null,
};

export type UpdateModelCostInput = {
  id: string,
  inputPrice?: number | null,
  isActive?: boolean | null,
  lastUpdated?: string | null,
  modelName?: string | null,
  outputPrice?: number | null,
  updatedBy?: string | null,
};

export type ModelSubscriptionApiKeyFilterInput = {
  and?: Array< ModelSubscriptionApiKeyFilterInput | null > | null,
  clientId?: ModelSubscriptionStringInput | null,
  clientName?: ModelSubscriptionStringInput | null,
  createdAt?: ModelSubscriptionStringInput | null,
  createdBy?: ModelSubscriptionStringInput | null,
  expiresAt?: ModelSubscriptionStringInput | null,
  id?: ModelSubscriptionIDInput | null,
  isActive?: ModelSubscriptionBooleanInput | null,
  keyId?: ModelSubscriptionStringInput | null,
  lastUsed?: ModelSubscriptionStringInput | null,
  metadata?: ModelSubscriptionStringInput | null,
  or?: Array< ModelSubscriptionApiKeyFilterInput | null > | null,
  permissions?: ModelSubscriptionStringInput | null,
  updatedAt?: ModelSubscriptionStringInput | null,
  usageCount?: ModelSubscriptionIntInput | null,
};

export type ModelSubscriptionStringInput = {
  beginsWith?: string | null,
  between?: Array< string | null > | null,
  contains?: string | null,
  eq?: string | null,
  ge?: string | null,
  gt?: string | null,
  in?: Array< string | null > | null,
  le?: string | null,
  lt?: string | null,
  ne?: string | null,
  notContains?: string | null,
  notIn?: Array< string | null > | null,
};

export type ModelSubscriptionIDInput = {
  beginsWith?: string | null,
  between?: Array< string | null > | null,
  contains?: string | null,
  eq?: string | null,
  ge?: string | null,
  gt?: string | null,
  in?: Array< string | null > | null,
  le?: string | null,
  lt?: string | null,
  ne?: string | null,
  notContains?: string | null,
  notIn?: Array< string | null > | null,
};

export type ModelSubscriptionBooleanInput = {
  eq?: boolean | null,
  ne?: boolean | null,
};

export type ModelSubscriptionIntInput = {
  between?: Array< number | null > | null,
  eq?: number | null,
  ge?: number | null,
  gt?: number | null,
  in?: Array< number | null > | null,
  le?: number | null,
  lt?: number | null,
  ne?: number | null,
  notIn?: Array< number | null > | null,
};

export type ModelSubscriptionModelCostFilterInput = {
  and?: Array< ModelSubscriptionModelCostFilterInput | null > | null,
  createdAt?: ModelSubscriptionStringInput | null,
  id?: ModelSubscriptionIDInput | null,
  inputPrice?: ModelSubscriptionFloatInput | null,
  isActive?: ModelSubscriptionBooleanInput | null,
  lastUpdated?: ModelSubscriptionStringInput | null,
  modelName?: ModelSubscriptionStringInput | null,
  or?: Array< ModelSubscriptionModelCostFilterInput | null > | null,
  outputPrice?: ModelSubscriptionFloatInput | null,
  updatedAt?: ModelSubscriptionStringInput | null,
  updatedBy?: ModelSubscriptionStringInput | null,
};

export type ModelSubscriptionFloatInput = {
  between?: Array< number | null > | null,
  eq?: number | null,
  ge?: number | null,
  gt?: number | null,
  in?: Array< number | null > | null,
  le?: number | null,
  lt?: number | null,
  ne?: number | null,
  notIn?: Array< number | null > | null,
};

export type GetApiKeyQueryVariables = {
  id: string,
};

export type GetApiKeyQuery = {
  getApiKey?:  {
    __typename: "ApiKey",
    clientId: string,
    clientName: string,
    createdAt?: string | null,
    createdBy: string,
    expiresAt?: string | null,
    id: string,
    isActive?: boolean | null,
    keyId: string,
    lastUsed?: string | null,
    metadata?: string | null,
    permissions?: Array< string | null > | null,
    updatedAt: string,
    usageCount?: number | null,
  } | null,
};

export type GetCloudWatchMetricsQueryVariables = {
  agentName?: string | null,
  endTime?: string | null,
  metricType: string,
  period?: number | null,
  startTime?: string | null,
};

export type GetCloudWatchMetricsQuery = {
  getCloudWatchMetrics?: string | null,
};

export type GetExecutionStatisticsQueryVariables = {
};

export type GetExecutionStatisticsQuery = {
  getExecutionStatistics?: string | null,
};

export type GetModelCostQueryVariables = {
  id: string,
};

export type GetModelCostQuery = {
  getModelCost?:  {
    __typename: "ModelCost",
    createdAt: string,
    id: string,
    inputPrice: number,
    isActive?: boolean | null,
    lastUpdated?: string | null,
    modelName: string,
    outputPrice: number,
    updatedAt: string,
    updatedBy?: string | null,
  } | null,
};

export type GetStateMachineInfoQueryVariables = {
  agentName: string,
};

export type GetStateMachineInfoQuery = {
  getStateMachineInfo?: string | null,
};

export type GetStepFunctionExecutionQueryVariables = {
  executionArn: string,
};

export type GetStepFunctionExecutionQuery = {
  getStepFunctionExecution?: string | null,
};

export type GetToolSecretValuesQueryVariables = {
};

export type GetToolSecretValuesQuery = {
  getToolSecretValues?: string | null,
};

export type ListAPIKeysQueryVariables = {
};

export type ListAPIKeysQuery = {
  listAPIKeys?:  Array< {
    __typename: "ApiKey",
    clientId: string,
    clientName: string,
    createdAt?: string | null,
    createdBy: string,
    expiresAt?: string | null,
    id: string,
    isActive?: boolean | null,
    keyId: string,
    lastUsed?: string | null,
    metadata?: string | null,
    permissions?: Array< string | null > | null,
    updatedAt: string,
    usageCount?: number | null,
  } | null > | null,
};

export type ListAgentsFromRegistryQueryVariables = {
};

export type ListAgentsFromRegistryQuery = {
  listAgentsFromRegistry?:  Array< {
    __typename: "Agent",
    createdAt?: string | null,
    description?: string | null,
    id: string,
    llmModel?: string | null,
    llmProvider?: string | null,
    metadata?: string | null,
    name: string,
    observability?: string | null,
    parameters?: string | null,
    status?: string | null,
    systemPrompt?: string | null,
    tools?: Array< string | null > | null,
    type?: string | null,
    version?: string | null,
  } | null > | null,
};

export type ListApiKeysQueryVariables = {
  filter?: ModelApiKeyFilterInput | null,
  limit?: number | null,
  nextToken?: string | null,
};

export type ListApiKeysQuery = {
  listApiKeys?:  {
    __typename: "ModelApiKeyConnection",
    items:  Array< {
      __typename: "ApiKey",
      clientId: string,
      clientName: string,
      createdAt?: string | null,
      createdBy: string,
      expiresAt?: string | null,
      id: string,
      isActive?: boolean | null,
      keyId: string,
      lastUsed?: string | null,
      metadata?: string | null,
      permissions?: Array< string | null > | null,
      updatedAt: string,
      usageCount?: number | null,
    } | null >,
    nextToken?: string | null,
  } | null,
};

export type ListLLMModelsQueryVariables = {
};

export type ListLLMModelsQuery = {
  listLLMModels?:  Array< {
    __typename: "LLMModel",
    created_at?: string | null,
    display_name: string,
    input_price_per_1k: number,
    is_active?: string | null,
    is_default?: boolean | null,
    max_tokens?: number | null,
    model_id: string,
    output_price_per_1k: number,
    pk: string,
    provider: string,
    supports_tools?: boolean | null,
    supports_vision?: boolean | null,
    updated_at?: string | null,
  } | null > | null,
};

export type ListLLMModelsByProviderQueryVariables = {
  provider: string,
};

export type ListLLMModelsByProviderQuery = {
  listLLMModelsByProvider?:  Array< {
    __typename: "LLMModel",
    created_at?: string | null,
    display_name: string,
    input_price_per_1k: number,
    is_active?: string | null,
    is_default?: boolean | null,
    max_tokens?: number | null,
    model_id: string,
    output_price_per_1k: number,
    pk: string,
    provider: string,
    supports_tools?: boolean | null,
    supports_vision?: boolean | null,
    updated_at?: string | null,
  } | null > | null,
};

export type ListModelCostsQueryVariables = {
  filter?: ModelModelCostFilterInput | null,
  limit?: number | null,
  nextToken?: string | null,
};

export type ListModelCostsQuery = {
  listModelCosts?:  {
    __typename: "ModelModelCostConnection",
    items:  Array< {
      __typename: "ModelCost",
      createdAt: string,
      id: string,
      inputPrice: number,
      isActive?: boolean | null,
      lastUpdated?: string | null,
      modelName: string,
      outputPrice: number,
      updatedAt: string,
      updatedBy?: string | null,
    } | null >,
    nextToken?: string | null,
  } | null,
};

export type ListStepFunctionExecutionsQueryVariables = {
  maxResults?: number | null,
  stateMachineArn?: string | null,
  status?: string | null,
};

export type ListStepFunctionExecutionsQuery = {
  listStepFunctionExecutions?: string | null,
};

export type ListToolsFromRegistryQueryVariables = {
};

export type ListToolsFromRegistryQuery = {
  listToolsFromRegistry?:  Array< {
    __typename: "Tool",
    createdAt?: string | null,
    description?: string | null,
    id: string,
    inputSchema?: string | null,
    lambda_arn?: string | null,
    lambda_function_name?: string | null,
    language?: string | null,
    name: string,
    type?: string | null,
    version?: string | null,
  } | null > | null,
};

export type AddLLMModelMutationVariables = {
  display_name: string,
  input_price_per_1k: number,
  is_default?: boolean | null,
  max_tokens?: number | null,
  model_id: string,
  output_price_per_1k: number,
  provider: string,
  supports_tools?: boolean | null,
  supports_vision?: boolean | null,
};

export type AddLLMModelMutation = {
  addLLMModel?: string | null,
};

export type CreateApiKeyMutationVariables = {
  condition?: ModelApiKeyConditionInput | null,
  input: CreateApiKeyInput,
};

export type CreateApiKeyMutation = {
  createApiKey?:  {
    __typename: "ApiKey",
    clientId: string,
    clientName: string,
    createdAt?: string | null,
    createdBy: string,
    expiresAt?: string | null,
    id: string,
    isActive?: boolean | null,
    keyId: string,
    lastUsed?: string | null,
    metadata?: string | null,
    permissions?: Array< string | null > | null,
    updatedAt: string,
    usageCount?: number | null,
  } | null,
};

export type CreateModelCostMutationVariables = {
  condition?: ModelModelCostConditionInput | null,
  input: CreateModelCostInput,
};

export type CreateModelCostMutation = {
  createModelCost?:  {
    __typename: "ModelCost",
    createdAt: string,
    id: string,
    inputPrice: number,
    isActive?: boolean | null,
    lastUpdated?: string | null,
    modelName: string,
    outputPrice: number,
    updatedAt: string,
    updatedBy?: string | null,
  } | null,
};

export type DeleteApiKeyMutationVariables = {
  condition?: ModelApiKeyConditionInput | null,
  input: DeleteApiKeyInput,
};

export type DeleteApiKeyMutation = {
  deleteApiKey?:  {
    __typename: "ApiKey",
    clientId: string,
    clientName: string,
    createdAt?: string | null,
    createdBy: string,
    expiresAt?: string | null,
    id: string,
    isActive?: boolean | null,
    keyId: string,
    lastUsed?: string | null,
    metadata?: string | null,
    permissions?: Array< string | null > | null,
    updatedAt: string,
    usageCount?: number | null,
  } | null,
};

export type DeleteLLMModelMutationVariables = {
  pk: string,
};

export type DeleteLLMModelMutation = {
  deleteLLMModel?: string | null,
};

export type DeleteModelCostMutationVariables = {
  condition?: ModelModelCostConditionInput | null,
  input: DeleteModelCostInput,
};

export type DeleteModelCostMutation = {
  deleteModelCost?:  {
    __typename: "ModelCost",
    createdAt: string,
    id: string,
    inputPrice: number,
    isActive?: boolean | null,
    lastUpdated?: string | null,
    modelName: string,
    outputPrice: number,
    updatedAt: string,
    updatedBy?: string | null,
  } | null,
};

export type GenerateAPIKeyMutationVariables = {
  clientId: string,
  clientName: string,
  expiresInDays?: number | null,
  permissions?: Array< string | null > | null,
};

export type GenerateAPIKeyMutation = {
  generateAPIKey?: string | null,
};

export type RevokeAPIKeyMutationVariables = {
  keyId: string,
};

export type RevokeAPIKeyMutation = {
  revokeAPIKey?: string | null,
};

export type RotateAPIKeyMutationVariables = {
  expiresInDays?: number | null,
  keyId: string,
};

export type RotateAPIKeyMutation = {
  rotateAPIKey?: string | null,
};

export type StartAgentExecutionMutationVariables = {
  agentName: string,
  executionName?: string | null,
  input?: string | null,
};

export type StartAgentExecutionMutation = {
  startAgentExecution?: string | null,
};

export type TestToolExecutionMutationVariables = {
  logLevel?: string | null,
  testInput: string,
  toolName: string,
};

export type TestToolExecutionMutation = {
  testToolExecution?: string | null,
};

export type UpdateAgentModelMutationVariables = {
  agentName: string,
  modelId: string,
  version: string,
};

export type UpdateAgentModelMutation = {
  updateAgentModel?: string | null,
};

export type UpdateAgentProviderAndModelMutationVariables = {
  agentName: string,
  modelId: string,
  provider: string,
  version: string,
};

export type UpdateAgentProviderAndModelMutation = {
  updateAgentProviderAndModel?: string | null,
};

export type UpdateAgentSystemPromptMutationVariables = {
  agentName: string,
  systemPrompt: string,
  version: string,
};

export type UpdateAgentSystemPromptMutation = {
  updateAgentSystemPrompt?: string | null,
};

export type UpdateApiKeyMutationVariables = {
  condition?: ModelApiKeyConditionInput | null,
  input: UpdateApiKeyInput,
};

export type UpdateApiKeyMutation = {
  updateApiKey?:  {
    __typename: "ApiKey",
    clientId: string,
    clientName: string,
    createdAt?: string | null,
    createdBy: string,
    expiresAt?: string | null,
    id: string,
    isActive?: boolean | null,
    keyId: string,
    lastUsed?: string | null,
    metadata?: string | null,
    permissions?: Array< string | null > | null,
    updatedAt: string,
    usageCount?: number | null,
  } | null,
};

export type UpdateLLMModelMutationVariables = {
  display_name?: string | null,
  input_price_per_1k?: number | null,
  is_active?: string | null,
  is_default?: boolean | null,
  max_tokens?: number | null,
  output_price_per_1k?: number | null,
  pk: string,
  supports_tools?: boolean | null,
  supports_vision?: boolean | null,
};

export type UpdateLLMModelMutation = {
  updateLLMModel?: string | null,
};

export type UpdateModelCostMutationVariables = {
  condition?: ModelModelCostConditionInput | null,
  input: UpdateModelCostInput,
};

export type UpdateModelCostMutation = {
  updateModelCost?:  {
    __typename: "ModelCost",
    createdAt: string,
    id: string,
    inputPrice: number,
    isActive?: boolean | null,
    lastUpdated?: string | null,
    modelName: string,
    outputPrice: number,
    updatedAt: string,
    updatedBy?: string | null,
  } | null,
};

export type UpdateProviderAPIKeyMutationVariables = {
  apiKey: string,
  provider: string,
};

export type UpdateProviderAPIKeyMutation = {
  updateProviderAPIKey?: string | null,
};

export type UpdateToolSecretsMutationVariables = {
  secrets: string,
  toolName: string,
};

export type UpdateToolSecretsMutation = {
  updateToolSecrets?: string | null,
};

export type OnCreateApiKeySubscriptionVariables = {
  filter?: ModelSubscriptionApiKeyFilterInput | null,
};

export type OnCreateApiKeySubscription = {
  onCreateApiKey?:  {
    __typename: "ApiKey",
    clientId: string,
    clientName: string,
    createdAt?: string | null,
    createdBy: string,
    expiresAt?: string | null,
    id: string,
    isActive?: boolean | null,
    keyId: string,
    lastUsed?: string | null,
    metadata?: string | null,
    permissions?: Array< string | null > | null,
    updatedAt: string,
    usageCount?: number | null,
  } | null,
};

export type OnCreateModelCostSubscriptionVariables = {
  filter?: ModelSubscriptionModelCostFilterInput | null,
};

export type OnCreateModelCostSubscription = {
  onCreateModelCost?:  {
    __typename: "ModelCost",
    createdAt: string,
    id: string,
    inputPrice: number,
    isActive?: boolean | null,
    lastUpdated?: string | null,
    modelName: string,
    outputPrice: number,
    updatedAt: string,
    updatedBy?: string | null,
  } | null,
};

export type OnDeleteApiKeySubscriptionVariables = {
  filter?: ModelSubscriptionApiKeyFilterInput | null,
};

export type OnDeleteApiKeySubscription = {
  onDeleteApiKey?:  {
    __typename: "ApiKey",
    clientId: string,
    clientName: string,
    createdAt?: string | null,
    createdBy: string,
    expiresAt?: string | null,
    id: string,
    isActive?: boolean | null,
    keyId: string,
    lastUsed?: string | null,
    metadata?: string | null,
    permissions?: Array< string | null > | null,
    updatedAt: string,
    usageCount?: number | null,
  } | null,
};

export type OnDeleteModelCostSubscriptionVariables = {
  filter?: ModelSubscriptionModelCostFilterInput | null,
};

export type OnDeleteModelCostSubscription = {
  onDeleteModelCost?:  {
    __typename: "ModelCost",
    createdAt: string,
    id: string,
    inputPrice: number,
    isActive?: boolean | null,
    lastUpdated?: string | null,
    modelName: string,
    outputPrice: number,
    updatedAt: string,
    updatedBy?: string | null,
  } | null,
};

export type OnUpdateApiKeySubscriptionVariables = {
  filter?: ModelSubscriptionApiKeyFilterInput | null,
};

export type OnUpdateApiKeySubscription = {
  onUpdateApiKey?:  {
    __typename: "ApiKey",
    clientId: string,
    clientName: string,
    createdAt?: string | null,
    createdBy: string,
    expiresAt?: string | null,
    id: string,
    isActive?: boolean | null,
    keyId: string,
    lastUsed?: string | null,
    metadata?: string | null,
    permissions?: Array< string | null > | null,
    updatedAt: string,
    usageCount?: number | null,
  } | null,
};

export type OnUpdateModelCostSubscriptionVariables = {
  filter?: ModelSubscriptionModelCostFilterInput | null,
};

export type OnUpdateModelCostSubscription = {
  onUpdateModelCost?:  {
    __typename: "ModelCost",
    createdAt: string,
    id: string,
    inputPrice: number,
    isActive?: boolean | null,
    lastUpdated?: string | null,
    modelName: string,
    outputPrice: number,
    updatedAt: string,
    updatedBy?: string | null,
  } | null,
};
