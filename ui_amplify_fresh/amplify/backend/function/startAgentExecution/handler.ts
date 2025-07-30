import type { Handler } from 'aws-lambda';
import { SFNClient, StartExecutionCommand, DescribeStateMachineCommand } from '@aws-sdk/client-sfn';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand } from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'crypto';

const sfnClient = new SFNClient({});
const ddbClient = new DynamoDBClient({});
const ddbDocClient = DynamoDBDocumentClient.from(ddbClient);

interface StartAgentExecutionInput {
  agentName: string;
  prompt: string;
  systemPrompt?: string;
  llmConfig?: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
  };
  userId: string;
}

export const handler: Handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  const input = event as StartAgentExecutionInput;
  const { agentName, prompt, systemPrompt, llmConfig, userId } = input;
  
  const agentRegistryTable = process.env.AGENT_REGISTRY_TABLE_NAME;
  
  if (!agentRegistryTable) {
    throw new Error('AGENT_REGISTRY_TABLE_NAME environment variable not set');
  }
  
  try {
    // Get agent details from registry
    const agentCommand = new GetCommand({
      TableName: agentRegistryTable,
      Key: {
        agent_name: agentName,
        version: 'latest'
      }
    });
    
    const agentResponse = await ddbDocClient.send(agentCommand);
    
    if (!agentResponse.Item) {
      throw new Error(`Agent ${agentName} not found in registry`);
    }
    
    const agent = agentResponse.Item;
    const stateMachineArn = agent.state_machine_arn;
    
    if (!stateMachineArn) {
      throw new Error(`Agent ${agentName} does not have a state machine ARN`);
    }
    
    // Get state machine details
    const describeCommand = new DescribeStateMachineCommand({
      stateMachineArn
    });
    
    const stateMachineDetails = await sfnClient.send(describeCommand);
    
    // Prepare execution input
    const executionInput = {
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      prompt,
      systemPrompt: systemPrompt || agent.system_prompt || '',
      llmConfig: {
        model: llmConfig?.model || agent.llm_config?.model || 'claude-3-sonnet-20240229',
        temperature: llmConfig?.temperature || agent.llm_config?.temperature || 0.7,
        max_tokens: llmConfig?.maxTokens || agent.llm_config?.max_tokens || 4000
      },
      tools: agent.tools || [],
      maxIterations: agent.max_iterations || 10,
      userId,
      agentName
    };
    
    // Start execution
    const executionId = randomUUID();
    const executionName = `${agentName}-${executionId}`;
    
    const startCommand = new StartExecutionCommand({
      stateMachineArn,
      name: executionName,
      input: JSON.stringify(executionInput)
    });
    
    const executionResponse = await sfnClient.send(startCommand);
    
    // Return execution information directly from Step Functions
    return {
      executionArn: executionResponse.executionArn,
      name: executionName,
      stateMachineArn,
      status: 'RUNNING',
      startDate: new Date().toISOString(),
      input: executionInput,
      output: null,
      error: null,
    };
    
  } catch (error) {
    console.error('Error starting agent execution:', error);
    throw new Error(`Failed to start agent execution: ${error instanceof Error ? error.message : String(error)}`);
  }
};