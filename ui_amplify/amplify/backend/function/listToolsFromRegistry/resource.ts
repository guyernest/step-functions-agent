import { defineFunction } from '@aws-amplify/backend';

export const listToolsFromRegistry = defineFunction({
  name: 'listToolsFromRegistry',
  entry: './handler.ts',
  environment: {
    // Environment variables can be added here if needed
  },
  runtime: 20,
  timeoutSeconds: 30,
  memoryMB: 512,
  bundling: {
    externalModules: [
      '@aws-sdk/client-dynamodb',
      '@aws-sdk/*'
    ]
  }
});