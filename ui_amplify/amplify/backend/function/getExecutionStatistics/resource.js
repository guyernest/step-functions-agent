import { defineFunction } from '@aws-amplify/backend';
export const getExecutionStatistics = defineFunction({
    name: 'getExecutionStatistics',
    entry: './handler.ts',
    timeoutSeconds: 30,
    memoryMB: 512
});
