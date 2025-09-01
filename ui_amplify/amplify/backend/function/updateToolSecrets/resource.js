import { defineFunction } from '@aws-amplify/backend';
export const updateToolSecrets = defineFunction({
    name: 'updateToolSecrets',
    entry: './handler.ts',
    timeoutSeconds: 30,
    environment: {
        ENVIRONMENT: 'prod'
    }
});
