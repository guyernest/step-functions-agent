import { defineFunction } from '@aws-amplify/backend';
export const getStateMachineInfo = defineFunction({
    name: 'getStateMachineInfo',
    entry: './handler.ts',
    timeoutSeconds: 30,
});
