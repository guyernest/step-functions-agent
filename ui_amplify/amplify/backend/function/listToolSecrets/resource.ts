import { defineFunction } from '@aws-amplify/backend';

export const listToolSecrets = defineFunction({
  name: 'listToolSecrets',
  entry: './handler.ts',
  timeoutSeconds: 30,
  environment: {
    ENVIRONMENT: 'prod'
  }
});