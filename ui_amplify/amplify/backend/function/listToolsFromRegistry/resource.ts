import { defineFunction } from '@aws-amplify/backend';

export const listToolsFromRegistry = defineFunction({
  name: 'listToolsFromRegistry',
  entry: './handler.ts',
  timeoutSeconds: 30,
  memoryMB: 512
});