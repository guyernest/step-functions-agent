import React from 'react';
import { Button, Card, View, Text, Alert } from '@aws-amplify/ui-react';
import { generateClient } from 'aws-amplify/data';
import type { Schema } from '../../amplify/data/resource';

const client = generateClient<Schema>();

const TestQueries: React.FC = () => {
  const [result, setResult] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const testAgentQuery = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      console.log('Testing listAgentsFromRegistry query...');
      const response = await client.queries.listAgentsFromRegistry();
      console.log('Response:', response);
      setResult(response);
    } catch (err) {
      console.error('Error:', err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const testToolQuery = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      console.log('Testing listToolsFromRegistry query...');
      const response = await client.queries.listToolsFromRegistry();
      console.log('Response:', response);
      setResult(response);
    } catch (err) {
      console.error('Error:', err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <View>
        <Text fontSize="large" fontWeight="bold">GraphQL Query Test</Text>
        
        <View marginTop="1rem">
          <Button onClick={testAgentQuery} isLoading={loading} marginRight="1rem">
            Test Agent Query
          </Button>
          <Button onClick={testToolQuery} isLoading={loading}>
            Test Tool Query
          </Button>
        </View>

        {error && (
          <Alert variation="error" marginTop="1rem">
            Error: {error}
          </Alert>
        )}

        {result && (
          <Card marginTop="1rem" variation="outlined">
            <Text fontWeight="bold">Result:</Text>
            <pre style={{ marginTop: '0.5rem', fontSize: '12px', overflow: 'auto' }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </Card>
        )}
      </View>
    </Card>
  );
};

export default TestQueries;