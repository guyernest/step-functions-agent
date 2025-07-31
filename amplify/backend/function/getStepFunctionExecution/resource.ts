import { defineFunction } from '@aws-amplify/backend';

export const getStepFunctionExecution = defineFunction({
  name: 'getStepFunctionExecution',
  entry: './handler.ts',
  runtime: 20,
  timeoutSeconds: 30,
});