import { defineFunction } from '@aws-amplify/backend';

export const listAgentsFromRegistry = defineFunction({
  name: 'listAgentsFromRegistry',
  entry: './handler.ts',
  timeoutSeconds: 30,
  memoryMB: 512
});