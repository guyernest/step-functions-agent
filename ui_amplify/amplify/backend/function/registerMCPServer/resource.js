import { defineFunction } from '@aws-amplify/backend';
export const registerMCPServer = defineFunction({
    name: 'registerMCPServer',
    entry: './handler.ts'
});
