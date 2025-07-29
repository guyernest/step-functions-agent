import { defineFunction } from '@aws-amplify/backend';

export const getExecutionHistory = defineFunction({
  name: 'getExecutionHistory',
  entry: './handler.ts',
  runtime: 20,
  timeoutSeconds: 30,
});