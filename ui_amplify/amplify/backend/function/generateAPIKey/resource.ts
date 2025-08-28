import { defineFunction } from '@aws-amplify/backend';

export const generateAPIKey = defineFunction({
  name: 'generateAPIKey',
  entry: './handler.ts'
});