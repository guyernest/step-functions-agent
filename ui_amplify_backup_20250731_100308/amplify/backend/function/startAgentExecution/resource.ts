import { defineFunction } from '@aws-amplify/backend';

export const startAgentExecution = defineFunction({
  name: 'startAgentExecution',
  entry: './handler.ts',
  runtime: 20,
  timeoutSeconds: 30,
  environment: {
    AGENT_REGISTRY_TABLE_NAME: 'AgentRegistry-prod'
  }
});