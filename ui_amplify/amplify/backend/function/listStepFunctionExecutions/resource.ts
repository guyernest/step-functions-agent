import { defineFunction } from '@aws-amplify/backend';

export const listStepFunctionExecutions = defineFunction({
  name: 'listStepFunctionExecutions',
  entry: './handler.ts',
  timeoutSeconds: 30,
  memoryMB: 512
});