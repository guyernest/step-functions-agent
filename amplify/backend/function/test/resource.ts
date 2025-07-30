import { defineFunction } from '@aws-amplify/backend';

export const test = defineFunction({
  name: 'test',
  entry: './handler.ts',
});