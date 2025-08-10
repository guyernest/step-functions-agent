import { defineFunction } from '@aws-amplify/backend';

export const testToolExecution = defineFunction({
  name: 'testToolExecution',
  entry: './handler.ts',
  runtime: 20,
  timeoutSeconds: 30,
  memoryMB: 512,
  environment: {
    TOOL_REGISTRY_TABLE: 'ToolRegistry-prod'
  }
});