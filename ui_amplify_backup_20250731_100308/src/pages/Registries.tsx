import React, { useState } from 'react';
import { 
  Heading, 
  Card, 
  Tabs,
  Collection,
  Badge,
  SearchField,
  View,
  Text,
  Flex,
  Loader,
  Alert
} from '@aws-amplify/ui-react';
import { useAgentRegistry } from '../hooks/useAgentRegistry';
import { useToolRegistry } from '../hooks/useToolRegistry';
// Remove test components - they were for debugging

const Registries: React.FC = () => {
  const [agentSearch, setAgentSearch] = useState('');
  const [toolSearch, setToolSearch] = useState('');
  
  // Fetch data from DynamoDB via Lambda functions
  const { data: agents, isLoading: agentsLoading, error: agentsError } = useAgentRegistry();
  const { data: tools, isLoading: toolsLoading, error: toolsError } = useToolRegistry();
  
  const filteredAgents = React.useMemo(() => 
    agents?.filter(agent => 
      agent.name.toLowerCase().includes(agentSearch.toLowerCase()) ||
      (agent.description || '').toLowerCase().includes(agentSearch.toLowerCase())
    ) || []
  , [agents, agentSearch]);
  
  const filteredTools = React.useMemo(() => 
    tools?.filter(tool => 
      tool.name.toLowerCase().includes(toolSearch.toLowerCase()) ||
      (tool.description || '').toLowerCase().includes(toolSearch.toLowerCase())
    ) || []
  , [tools, toolSearch]);
  
  // Clean up - remove debug logging since it's working now

  return (
    <View>
      <Heading level={2} marginBottom="2rem">Agent & Tool Registries</Heading>
      
      {/* Bypass tabs temporarily to test content rendering */}
      <View marginBottom="2rem">
        <Heading level={3} marginBottom="1rem">Agents ({filteredAgents.length})</Heading>
          <Card>
            <SearchField
              label="Search agents"
              placeholder="Search by name or description..."
              value={agentSearch}
              onChange={(e) => setAgentSearch(e.target.value)}
              onClear={() => setAgentSearch('')}
            />
            
            {agentsError && (
              <Alert
                variation="error"
                marginTop="1rem"
                heading="Error loading agents"
              >
                {agentsError.message}
              </Alert>
            )}
            
            {agentsLoading ? (
              <Flex justifyContent="center" marginTop="2rem">
                <Loader size="large" />
              </Flex>
            ) : (
              <>
                {filteredAgents.length === 0 && (
                  <Text textAlign="center" padding="2rem" color="gray.60">
                    No agents found matching your search criteria.
                  </Text>
                )}
                
                {/* Direct mapping works better than Collection component */}
                <View>
                  {filteredAgents.map((agent, index) => (
                    <Card key={agent.id} variation="outlined" marginBottom="1rem">
                      <Flex justifyContent="space-between" alignItems="start">
                        <View>
                          <Heading level={5}>{agent.name}</Heading>
                          <Text color="gray.60">{agent.description || 'No description available'}</Text>
                          <Flex gap="0.5rem" marginTop="0.5rem">
                            <Badge variation="success">v{agent.version}</Badge>
                            <Badge>{agent.status || 'ACTIVE'}</Badge>
                          </Flex>
                        </View>
                        <View>
                          <Text fontSize="small" color="gray.60">Tools:</Text>
                          {(agent.tools || [])
                            .filter((tool: string) => tool && tool.trim()) // Filter out empty tools
                            .map((tool: string, index: number) => (
                            <Badge key={`${agent.id}-tool-${index}-${tool}`} size="small" marginLeft="0.25rem">
                              {tool}
                            </Badge>
                          ))}
                        </View>
                      </Flex>
                    </Card>
                  ))}
                </View>
              </>
            )}
          </Card>
      </View>
      
      <View>
        <Heading level={3} marginBottom="1rem">Tools ({filteredTools.length})</Heading>
        <Card>
            <SearchField
              label="Search tools"
              placeholder="Search by name or description..."
              value={toolSearch}
              onChange={(e) => setToolSearch(e.target.value)}
              onClear={() => setToolSearch('')}
            />
            
            {toolsError && (
              <Alert
                variation="error"
                marginTop="1rem"
                heading="Error loading tools"
              >
                {toolsError.message}
              </Alert>
            )}
            
            {toolsLoading ? (
              <Flex justifyContent="center" marginTop="2rem">
                <Loader size="large" />
              </Flex>
            ) : (
              <>
                {filteredTools.length === 0 && (
                  <Text textAlign="center" padding="2rem" color="gray.60">
                    No tools found matching your search criteria.
                  </Text>
                )}
                
                <View>
                  {filteredTools.map((tool) => (
                    <Card key={tool.id} variation="outlined" marginBottom="1rem">
                      <Flex justifyContent="space-between" alignItems="center">
                        <View>
                          <Heading level={5}>{tool.name}</Heading>
                          <Text color="gray.60">{tool.description || 'No description available'}</Text>
                          <Badge marginTop="0.5rem">{tool.status || 'ACTIVE'}</Badge>
                        </View>
                        <Badge variation="info">v{tool.version}</Badge>
                      </Flex>
                    </Card>
                  ))}
                </View>
              </>
            )}
        </Card>
      </View>
    </View>
  );
};

export default Registries;