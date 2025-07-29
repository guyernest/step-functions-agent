import { defineFunction } from '@aws-amplify/backend';

export const listToolsFromRegistry = defineFunction({
  name: 'listToolsFromRegistry',
  entry: './handler.ts',
  runtime: 20,
  timeoutSeconds: 30,
  environment: {
    TOOL_REGISTRY_TABLE_NAME: 'ToolRegistry-prod'
  }
});