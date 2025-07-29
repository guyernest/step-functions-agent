import React, { useState } from 'react';
import { 
  Heading, 
  Card, 
  SelectField, 
  TextAreaField, 
  Button, 
  Flex, 
  View,
  Alert,
  Text,
  Loader,
  Badge,
  Divider
} from '@aws-amplify/ui-react';
import { useAgentRegistry } from '../hooks/useAgentRegistry';
import { useAgentExecution } from '../hooks/useAgentExecution';

const AgentExecution: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState('');
  const [prompt, setPrompt] = useState('');
  const [executionResult, setExecutionResult] = useState<any>(null);
  
  // Fetch agents from registry
  const { data: agents, isLoading: agentsLoading } = useAgentRegistry();
  const { startExecution } = useAgentExecution();

  const handleExecute = async () => {
    if (!selectedAgent || !prompt) {
      return;
    }
    
    try {
      const result = await startExecution.mutateAsync({
        agentName: selectedAgent,
        prompt: prompt,
      });
      
      setExecutionResult(result);
      // Clear form
      setPrompt('');
    } catch (error) {
      console.error('Failed to start execution:', error);
    }
  };

  return (
    <View>
      <Heading level={2} marginBottom="2rem">Execute Agent</Heading>
      
      <Card>
        <Flex direction="column" gap="1.5rem">
          {agentsLoading ? (
            <Loader />
          ) : (
            <SelectField
              label="Select Agent"
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              placeholder="Choose an agent..."
            >
              <option value="">Select an agent</option>
              {agents?.map(agent => (
                <option key={agent.id} value={agent.name}>
                  {agent.name} (v{agent.version})
                </option>
              ))}
            </SelectField>
          )}
          
          {selectedAgent && agents && (
            <Alert variation="info">
              {agents.find(a => a.name === selectedAgent)?.description || 'No description available'}
            </Alert>
          )}
          
          <TextAreaField
            label="Prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt here..."
            descriptiveText="Provide instructions for the agent"
            rows={4}
          />
          
          <Button
            variation="primary"
            isLoading={startExecution.isPending}
            loadingText="Starting execution..."
            onClick={handleExecute}
            isDisabled={!selectedAgent || !prompt || agentsLoading}
          >
            Execute Agent
          </Button>
        </Flex>
      </Card>
      
      {startExecution.isError && (
        <Alert variation="error" marginTop="1rem">
          Failed to start execution: {startExecution.error?.message}
        </Alert>
      )}
      
      {executionResult && (
        <Card marginTop="2rem">
          <Heading level={4}>Execution Started</Heading>
          <Divider marginTop="1rem" marginBottom="1rem" />
          
          <Flex direction="column" gap="0.5rem">
            <Flex>
              <Text fontWeight="bold">Execution ID:</Text>
              <Text marginLeft="0.5rem">{executionResult.id}</Text>
            </Flex>
            
            <Flex>
              <Text fontWeight="bold">Agent:</Text>
              <Text marginLeft="0.5rem">{executionResult.agentName}</Text>
            </Flex>
            
            <Flex>
              <Text fontWeight="bold">Status:</Text>
              <Badge marginLeft="0.5rem" variation="info">{executionResult.status}</Badge>
            </Flex>
            
            <Flex>
              <Text fontWeight="bold">Started:</Text>
              <Text marginLeft="0.5rem">{new Date(executionResult.startTime).toLocaleString()}</Text>
            </Flex>
          </Flex>
          
          <Alert variation="info" marginTop="1rem">
            Execution has been started. Navigate to the History page to monitor progress and view results.
          </Alert>
        </Card>
      )}
    </View>
  );
};

export default AgentExecution;