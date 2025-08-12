import { defineFunction } from '@aws-amplify/backend';

export const getToolSecretValues = defineFunction({
  name: 'getToolSecretValues',
  entry: './handler.ts',
  timeoutSeconds: 30,
  environment: {
    ENVIRONMENT: 'prod'
  }
});