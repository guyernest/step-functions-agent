import { useMutation, useQueryClient } from '@tanstack/react-query';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';

export interface StartAgentExecutionInput {
  agentName: string;
  prompt: string;
  systemPrompt?: string;
  llmConfig?: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
  };
}

export interface ExecutionResponse {
  id: string;
  executionArn: string;
  agentName: string;
  status: string;
  startTime: string;
}

export const useAgentExecution = () => {
  const queryClient = useQueryClient();

  const startExecution = useMutation({
    mutationFn: async (input: StartAgentExecutionInput) => {
      try {
        const client = generateClient<Schema>();
        const response = await client.mutations.startAgentExecution({
          agentName: input.agentName,
          prompt: input.prompt,
          systemPrompt: input.systemPrompt,
          llmConfig: input.llmConfig ? JSON.stringify(input.llmConfig) : undefined,
        });
        
        if (response.errors) {
          throw new Error(response.errors[0].message);
        }
        
        return response.data as ExecutionResponse;
      } catch (error) {
        console.error('Error starting agent execution:', error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate executions query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['executions'] });
    },
  });

  return {
    startExecution,
  };
};