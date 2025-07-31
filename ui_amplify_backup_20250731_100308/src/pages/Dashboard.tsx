import React from 'react';
import { Heading, Grid, Card, Text, View, Flex } from '@aws-amplify/ui-react';

const Dashboard: React.FC = () => {
  // Mock data for now - will be replaced with real data from GraphQL
  const stats = {
    totalAgents: 12,
    activeExecutions: 3,
    totalTools: 25,
    recentExecutions: 145
  };

  return (
    <View>
      <Heading level={2} marginBottom="2rem">Dashboard</Heading>
      
      <Grid templateColumns="1fr 1fr 1fr 1fr" gap="1rem">
        <Card>
          <Flex direction="column" alignItems="center">
            <Text fontSize="2rem" fontWeight="bold" color="blue.80">
              {stats.totalAgents}
            </Text>
            <Text color="gray.60">Total Agents</Text>
          </Flex>
        </Card>
        
        <Card>
          <Flex direction="column" alignItems="center">
            <Text fontSize="2rem" fontWeight="bold" color="green.80">
              {stats.activeExecutions}
            </Text>
            <Text color="gray.60">Active Executions</Text>
          </Flex>
        </Card>
        
        <Card>
          <Flex direction="column" alignItems="center">
            <Text fontSize="2rem" fontWeight="bold" color="purple.80">
              {stats.totalTools}
            </Text>
            <Text color="gray.60">Total Tools</Text>
          </Flex>
        </Card>
        
        <Card>
          <Flex direction="column" alignItems="center">
            <Text fontSize="2rem" fontWeight="bold" color="orange.80">
              {stats.recentExecutions}
            </Text>
            <Text color="gray.60">Recent Executions</Text>
          </Flex>
        </Card>
      </Grid>
      
      <Grid templateColumns="2fr 1fr" gap="2rem" marginTop="2rem">
        <Card>
          <Heading level={4}>Recent Activity</Heading>
          <Text marginTop="1rem" color="gray.60">
            Activity feed will be displayed here...
          </Text>
        </Card>
        
        <Card>
          <Heading level={4}>System Health</Heading>
          <Text marginTop="1rem" color="gray.60">
            System metrics will be displayed here...
          </Text>
        </Card>
      </Grid>
    </View>
  );
};

export default Dashboard;