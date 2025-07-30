import { defineFunction } from '@aws-amplify/backend';

export const listAgentsFromRegistry = defineFunction({
  name: 'listAgentsFromRegistry',
  entry: './handler.ts',
  runtime: 20,
  timeoutSeconds: 30,
  environment: {
    AGENT_REGISTRY_TABLE_NAME: 'AgentRegistry-prod'
  }
});