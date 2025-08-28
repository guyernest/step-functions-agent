import { defineFunction } from '@aws-amplify/backend';

export const rotateAPIKey = defineFunction({
  name: 'rotateAPIKey',
  entry: './handler.ts'
});