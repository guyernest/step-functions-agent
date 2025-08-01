import { defineFunction } from '@aws-amplify/backend';

export const getStepFunctionExecution = defineFunction({
  name: 'getStepFunctionExecution',
  entry: './handler.ts'
});