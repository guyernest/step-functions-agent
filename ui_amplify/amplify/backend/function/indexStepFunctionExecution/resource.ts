import { defineFunction } from '@aws-amplify/backend';

export const indexStepFunctionExecution = defineFunction({
  name: 'indexStepFunctionExecution',
  entry: './handler.ts',
  timeoutSeconds: 30,
  runtime: 20,
  resourceGroupName: 'data',
});