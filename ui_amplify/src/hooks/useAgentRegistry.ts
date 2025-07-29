import { useQuery } from '@tanstack/react-query';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';

export interface Agent {
  id: string;
  name: string;
  version: string;
  description?: string;
  tools?: string[];
  status?: string;
  capabilities?: Record<string, any>;
  maxIterations?: number;
}

export const useAgentRegistry = () => {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      try {
        const client = generateClient<Schema>();
        const response = await client.queries.listAgentsFromRegistry();
        return response.data as Agent[];
      } catch (error) {
        console.error('Error fetching agents:', error);
        throw error;
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};