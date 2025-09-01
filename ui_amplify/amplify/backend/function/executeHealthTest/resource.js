import { defineFunction } from '@aws-amplify/backend';
export const executeHealthTest = defineFunction({
    name: 'executeHealthTest',
    timeoutSeconds: 120,
    environment: {
        TEST_EVENTS_TABLE_NAME: 'TestEvents-prod',
        TEST_RESULTS_TABLE_NAME: 'TestResults-prod',
        TOOL_REGISTRY_TABLE_NAME: 'ToolRegistry-prod',
        AGENT_REGISTRY_TABLE_NAME: 'AgentRegistry-prod',
        ENV_NAME: 'prod'
    }
});
