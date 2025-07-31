import React, { useEffect } from 'react';
import { Card, Text, View } from '@aws-amplify/ui-react';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';
import { useAgentRegistry } from '../hooks/useAgentRegistry';

const client = generateClient<Schema>();

const Debug: React.FC = () => {
  const { data: agents, isLoading, error } = useAgentRegistry();

  useEffect(() => {
    console.log('Debug: Agent registry data:', { agents, isLoading, error });
    
    // Test direct client call
    const testQuery = async () => {
      try {
        console.log('Testing direct client call...');
        const result = await client.queries.listAgentsFromRegistry();
        console.log('Direct client result:', result);
      } catch (err) {
        console.error('Direct client error:', err);
      }
    };
    
    testQuery();
  }, [agents, isLoading, error]);

  return (
    <Card marginBottom="1rem">
      <View>
        <Text fontWeight="bold">Debug Info:</Text>
        <Text>Loading: {isLoading ? 'true' : 'false'}</Text>
        <Text>Error: {error ? error.message : 'none'}</Text>
        <Text>Data count: {agents ? agents.length : 'none'}</Text>
        <Text>Check browser console for detailed logs</Text>
      </View>
    </Card>
  );
};

export default Debug;