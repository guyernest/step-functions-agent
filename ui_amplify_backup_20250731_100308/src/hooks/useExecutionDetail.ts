import { useQuery } from '@tanstack/react-query';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';

export interface ExecutionDetail {
  executionArn: string;
  name: string;
  stateMachineArn: string;
  status: string;
  startDate: string;
  stopDate?: string;
  input?: any;
  output?: any;
  error?: string;
  agentName?: string;
}

export const useExecutionDetail = (executionArn: string) => {
  return useQuery<ExecutionDetail>({
    queryKey: ['execution', executionArn],
    queryFn: async () => {
      if (!executionArn) {
        throw new Error('Execution ARN is required');
      }

      try {
        const client = generateClient<Schema>();
        
        const response = await client.queries.getStepFunctionExecution({
          executionArn,
        });

        if (response.errors) {
          throw new Error(response.errors[0].message);
        }

        return response.data as ExecutionDetail;
      } catch (error) {
        console.error('Error fetching execution detail:', error);
        throw error;
      }
    },
    enabled: !!executionArn,
    // Simple refetch every 5 seconds - can be optimized later to only refetch when running
    refetchInterval: 5000,
  });
};