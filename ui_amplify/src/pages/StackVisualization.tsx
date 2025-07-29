import React, { useState } from 'react';
import { 
  Heading, 
  Card, 
  View,
  Text,
  Badge,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  SelectField,
  Flex
} from '@aws-amplify/ui-react';

const StackVisualization: React.FC = () => {
  const [selectedTag, setSelectedTag] = useState('Application:AIAgents');
  
  // Mock data - will be replaced with CloudFormation API data
  const mockStacks = [
    {
      stackName: 'SharedInfrastructureStack-prod',
      status: 'CREATE_COMPLETE',
      lastUpdated: '2024-01-15T10:30:00Z',
      exports: ['AgentRegistryTableArn', 'ToolRegistryTableArn'],
      importedBy: ['SQLAgentStack-prod', 'ResearchAgentStack-prod']
    },
    {
      stackName: 'SQLAgentStack-prod',
      status: 'UPDATE_COMPLETE',
      lastUpdated: '2024-01-15T11:45:00Z',
      exports: ['SQLAgentStateMachineArn'],
      importedBy: []
    },
    {
      stackName: 'SharedLLMStack-prod',
      status: 'CREATE_COMPLETE',
      lastUpdated: '2024-01-14T09:00:00Z',
      exports: ['ClaudeLambdaArn', 'OpenAILambdaArn'],
      importedBy: ['SQLAgentStack-prod', 'ResearchAgentStack-prod']
    }
  ];

  const getStatusBadge = (status: string) => {
    if (status.includes('COMPLETE')) {
      return <Badge variation="success">{status}</Badge>;
    } else if (status.includes('FAILED') || status.includes('ROLLBACK')) {
      return <Badge variation="error">{status}</Badge>;
    } else if (status.includes('IN_PROGRESS')) {
      return <Badge variation="info">{status}</Badge>;
    }
    return <Badge>{status}</Badge>;
  };

  return (
    <View>
      <Heading level={2} marginBottom="2rem">CloudFormation Stack Visualization</Heading>
      
      <Card marginBottom="2rem">
        <Flex gap="1rem" alignItems="flex-end">
          <SelectField
            label="Filter by Tag"
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
          >
            <option value="Application:AIAgents">Application: AIAgents</option>
            <option value="Environment:prod">Environment: prod</option>
            <option value="Environment:dev">Environment: dev</option>
          </SelectField>
          
          <Text color="gray.60">
            Showing {mockStacks.length} stacks
          </Text>
        </Flex>
      </Card>
      
      <Card>
        <Heading level={4} marginBottom="1rem">Stack Dependencies</Heading>
        
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Stack Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Updated</TableCell>
              <TableCell>Exports</TableCell>
              <TableCell>Imported By</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mockStacks.map((stack) => (
              <TableRow key={stack.stackName}>
                <TableCell>
                  <Text fontWeight="semibold">{stack.stackName}</Text>
                </TableCell>
                <TableCell>
                  {getStatusBadge(stack.status)}
                </TableCell>
                <TableCell>
                  <Text fontSize="small">
                    {new Date(stack.lastUpdated).toLocaleString()}
                  </Text>
                </TableCell>
                <TableCell>
                  {stack.exports.map(exp => (
                    <Badge key={exp} size="small" marginRight="0.25rem">
                      {exp}
                    </Badge>
                  ))}
                </TableCell>
                <TableCell>
                  {stack.importedBy.length > 0 ? (
                    stack.importedBy.map(imp => (
                      <Text key={imp} fontSize="small">{imp}</Text>
                    ))
                  ) : (
                    <Text fontSize="small" color="gray.60">None</Text>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
      
      <Card marginTop="2rem">
        <Heading level={4}>Dependency Diagram</Heading>
        <Text marginTop="1rem" color="gray.60">
          Interactive dependency diagram will be displayed here...
        </Text>
      </Card>
    </View>
  );
};

export default StackVisualization;