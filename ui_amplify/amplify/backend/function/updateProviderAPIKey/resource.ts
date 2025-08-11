import { defineFunction } from '@aws-amplify/backend';

export const updateProviderAPIKey = defineFunction({
  name: 'updateProviderAPIKey',
  runtime: 20,
  timeoutSeconds: 30,
  memoryMB: 512,
  environment: {
    SECRET_PREFIX: '/ai-agent/llm-secrets/prod'
  }
});