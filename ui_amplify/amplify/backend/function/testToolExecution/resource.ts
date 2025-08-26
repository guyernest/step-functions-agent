import { defineFunction } from '@aws-amplify/backend';

export const testToolExecution = defineFunction({
  name: 'testToolExecution',
  entry: './handler.ts',
  runtime: 20,
  timeoutSeconds: 300,  // Increased to match longest tool Lambda timeout
  memoryMB: 512,
  environment: {
    TOOL_REGISTRY_TABLE: 'ToolRegistry-prod'
  }
});