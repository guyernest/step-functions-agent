import { defineFunction } from '@aws-amplify/backend';

export const listExecutionsFromIndex = defineFunction({
  name: 'listExecutionsFromIndex',
  entry: './handler.ts',
  timeoutSeconds: 30,
  runtime: 20,
  resourceGroupName: 'data',
});