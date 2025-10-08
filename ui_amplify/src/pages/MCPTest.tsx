import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Card,
  Heading,
  Text,
  View,
  TextField,
  Button,
  Flex,
} from '@aws-amplify/ui-react';
import WasmMcpClient from '../components/WasmMcpClient';

export default function MCPTest() {
  const [searchParams] = useSearchParams();
  const urlParam = searchParams.get('url');
  const [serverUrl, setServerUrl] = useState(urlParam || 'https://dkheh7ufl9.execute-api.us-west-2.amazonaws.com/');
  const [showClient, setShowClient] = useState(!!urlParam);

  // Auto-connect if URL is provided
  useEffect(() => {
    if (urlParam) {
      setServerUrl(urlParam);
      setShowClient(true);
    }
  }, [urlParam]);

  const handleConnect = () => {
    setShowClient(true);
  };

  return (
    <View padding="2rem">
      <Heading level={3}>MCP WASM Client Test</Heading>
      <Text color="gray" marginBottom="2rem">
        Test the browser-based MCP client using WebAssembly
      </Text>

      {!showClient ? (
        <Card variation="outlined" maxWidth="600px">
          <Heading level={5}>Connect to MCP Server</Heading>
          <Text marginBottom="1rem">
            Enter the MCP server URL to test with the WASM client
          </Text>

          <TextField
            label="Server URL"
            value={serverUrl}
            onChange={(e) => setServerUrl(e.target.value)}
            placeholder="https://your-mcp-server.com/"
            marginBottom="1rem"
          />

          <Flex gap="0.5rem">
            <Button onClick={handleConnect} variation="primary">
              Connect
            </Button>
            <Button
              onClick={() => setServerUrl('https://dkheh7ufl9.execute-api.us-west-2.amazonaws.com/')}
              variation="link"
            >
              Use Reinvent Server
            </Button>
          </Flex>
        </Card>
      ) : (
        <View>
          <Card variation="outlined" marginBottom="1rem">
            <Flex direction="row" justifyContent="space-between" alignItems="center">
              <View>
                <Text fontWeight="bold">Connected to:</Text>
                <Text fontSize="0.875rem" color="gray">{serverUrl}</Text>
              </View>
              <Button onClick={() => setShowClient(false)} variation="link">
                Disconnect
              </Button>
            </Flex>
          </Card>

          <WasmMcpClient serverUrl={serverUrl} />
        </View>
      )}
    </View>
  );
}
