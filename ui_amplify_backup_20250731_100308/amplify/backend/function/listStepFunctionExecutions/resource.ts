import { defineFunction } from '@aws-amplify/backend';

export const listStepFunctionExecutions = defineFunction({
  name: 'listStepFunctionExecutions',
  entry: './handler.ts',
  runtime: 20,
  timeoutSeconds: 30
});