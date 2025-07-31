import { useQuery } from '@tanstack/react-query';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';

export interface Tool {
  id: string;
  name: string;
  version: string;
  description?: string;
  inputSchema?: Record<string, any>;
  outputSchema?: Record<string, any>;
  status?: string;
}

export const useToolRegistry = () => {
  return useQuery({
    queryKey: ['tools'],
    queryFn: async () => {
      try {
        const client = generateClient<Schema>();
        const response = await client.queries.listToolsFromRegistry();
        return response.data as Tool[];
      } catch (error) {
        console.error('Error fetching tools:', error);
        throw error;
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};