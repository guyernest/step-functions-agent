/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "./API";
type GeneratedSubscription<InputType, OutputType> = string & {
  __generatedSubscriptionInput: InputType;
  __generatedSubscriptionOutput: OutputType;
};

export const onCreateApiKey = /* GraphQL */ `subscription OnCreateApiKey($filter: ModelSubscriptionApiKeyFilterInput) {
  onCreateApiKey(filter: $filter) {
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
` as GeneratedSubscription<
  APITypes.OnCreateApiKeySubscriptionVariables,
  APITypes.OnCreateApiKeySubscription
>;
export const onCreateModelCost = /* GraphQL */ `subscription OnCreateModelCost($filter: ModelSubscriptionModelCostFilterInput) {
  onCreateModelCost(filter: $filter) {
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
` as GeneratedSubscription<
  APITypes.OnCreateModelCostSubscriptionVariables,
  APITypes.OnCreateModelCostSubscription
>;
export const onDeleteApiKey = /* GraphQL */ `subscription OnDeleteApiKey($filter: ModelSubscriptionApiKeyFilterInput) {
  onDeleteApiKey(filter: $filter) {
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
` as GeneratedSubscription<
  APITypes.OnDeleteApiKeySubscriptionVariables,
  APITypes.OnDeleteApiKeySubscription
>;
export const onDeleteModelCost = /* GraphQL */ `subscription OnDeleteModelCost($filter: ModelSubscriptionModelCostFilterInput) {
  onDeleteModelCost(filter: $filter) {
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
` as GeneratedSubscription<
  APITypes.OnDeleteModelCostSubscriptionVariables,
  APITypes.OnDeleteModelCostSubscription
>;
export const onUpdateApiKey = /* GraphQL */ `subscription OnUpdateApiKey($filter: ModelSubscriptionApiKeyFilterInput) {
  onUpdateApiKey(filter: $filter) {
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
` as GeneratedSubscription<
  APITypes.OnUpdateApiKeySubscriptionVariables,
  APITypes.OnUpdateApiKeySubscription
>;
export const onUpdateModelCost = /* GraphQL */ `subscription OnUpdateModelCost($filter: ModelSubscriptionModelCostFilterInput) {
  onUpdateModelCost(filter: $filter) {
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
` as GeneratedSubscription<
  APITypes.OnUpdateModelCostSubscriptionVariables,
  APITypes.OnUpdateModelCostSubscription
>;
