import { defineFunction } from '@aws-amplify/backend'

export const getCloudWatchMetrics = defineFunction({
  name: 'getCloudWatchMetrics',
  entry: './handler.ts',
  timeoutSeconds: 30,
  memoryMB: 256,
})