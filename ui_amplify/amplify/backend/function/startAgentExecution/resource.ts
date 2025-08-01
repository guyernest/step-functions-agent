import { defineFunction } from '@aws-amplify/backend';

export const startAgentExecution = defineFunction({
  name: 'startAgentExecution',
  entry: './handler.ts',
  timeoutSeconds: 30,
  memoryMB: 512
});