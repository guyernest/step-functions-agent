import { defineFunction } from '@aws-amplify/backend';
export const revokeAPIKey = defineFunction({
    name: 'revokeAPIKey',
    entry: './handler.ts'
});
