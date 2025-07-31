import { useQuery } from '@tanstack/react-query';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';

export const useExecutions = (stateMachineArn?: string, statusFilter?: string) => {
  return useQuery({
    queryKey: ['executions', stateMachineArn, statusFilter],
    queryFn: async () => {
      try {
        const client = generateClient<Schema>();
        const response = await client.queries.listStepFunctionExecutions({
          stateMachineArn,
          statusFilter,
          maxResults: 50
        });
        return response.data;
      } catch (error) {
        console.error('Error fetching Step Function executions:', error);
        throw error;
      }
    },
    refetchInterval: 10000, // Refetch every 10 seconds to get status updates
  });
};

export const useExecution = (executionArn: string) => {
  return useQuery({
    queryKey: ['execution', executionArn],
    queryFn: async () => {
      try {
        const client = generateClient<Schema>();
        const response = await client.queries.getStepFunctionExecution({
          executionArn
        });
        return response.data;
      } catch (error) {
        console.error('Error fetching Step Function execution:', error);
        throw error;
      }
    },
    enabled: !!executionArn,
    refetchInterval: 5000, // Refetch every 5 seconds for individual execution
  });
};

export const useExecutionHistory = (executionArn: string) => {
  return useQuery({
    queryKey: ['executionHistory', executionArn],
    queryFn: async () => {
      try {
        const client = generateClient<Schema>();
        const response = await client.queries.getExecutionHistory({
          executionArn,
          maxResults: 100
        });
        return response.data;
      } catch (error) {
        console.error('Error fetching execution history:', error);
        throw error;
      }
    },
    enabled: !!executionArn,
  });
};