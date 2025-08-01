import { defineFunction } from '@aws-amplify/backend';

export const getStepFunctionExecution = defineFunction({
  name: 'getStepFunctionExecution',
  entry: './handler.ts',
  environment: {
    // Environment variables can be added here if needed
  },
  runtime: 20,
  timeoutSeconds: 30,
  memoryMB: 512,
  bundling: {
    externalModules: [
      '@aws-sdk/client-sfn',
      '@aws-sdk/*'
    ]
  }
});