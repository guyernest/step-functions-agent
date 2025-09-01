import { defineFunction } from '@aws-amplify/backend';
export const listAPIKeys = defineFunction({
    name: 'listAPIKeys',
    entry: './handler.ts'
});
