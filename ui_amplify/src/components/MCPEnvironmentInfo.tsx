import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  View,
  Flex,
  Badge,
  Button,
  Alert,
  Table,
  TableCell,
  TableBody,
  TableHead,
  TableRow,
  Loader
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

// Import amplify outputs to get current environment MCP server details
import amplifyOutputs from '../../amplify_outputs.json'

interface MCPServerEnvironmentInfo {
  endpoint: string
  region: string
  functionName: string
  logGroup: string
  environment: string
}

interface MCPToolInfo {
  name: string
  description: string
}

const MCPEnvironmentInfo: React.FC = () => {
  const [registryServers, setRegistryServers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [registering, setRegistering] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)

  // Extract MCP server info from amplify_outputs.json
  const currentMCPInfo: MCPServerEnvironmentInfo = {
    endpoint: amplifyOutputs.custom?.mcpServerEndpoint || 'Not configured',
    region: amplifyOutputs.data?.aws_region || 'Unknown',
    functionName: amplifyOutputs.custom?.lambdaFunctions?.mcpServer || 'Unknown',
    logGroup: amplifyOutputs.custom?.logGroups?.mcpServer || 'Unknown',
    environment: process.env.NODE_ENV || 'development'
  }

  // Define the tools available in the current MCP server implementation
  const availableTools: MCPToolInfo[] = [
    {
      name: 'start_agent',
      description: 'Start execution of a Step Functions agent'
    },
    {
      name: 'get_execution_status', 
      description: 'Get status of an agent execution'
    },
    {
      name: 'list_available_agents',
      description: 'List all available agents from the registry'
    }
  ]

  useEffect(() => {
    fetchRegistryServers()
  }, [])

  const fetchRegistryServers = async () => {
    try {
      const response = await client.queries.listMCPServersFromRegistry({})
      if (response.data) {
        setRegistryServers(response.data.filter(server => server !== null))
      }
    } catch (error) {
      console.error('Error fetching registry servers:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateServerId = () => {
    const env = currentMCPInfo.environment
    return `step-functions-agents-mcp-${env}`
  }

  const isServerRegistered = () => {
    const serverId = generateServerId()
    return registryServers.some(server => 
      server.server_id === serverId && 
      server.endpoint_url === currentMCPInfo.endpoint
    )
  }

  const registerCurrentServer = async () => {
    setRegistering(true)
    setMessage(null)

    try {
      // Check if MCP endpoint is configured
      if (!currentMCPInfo.endpoint || currentMCPInfo.endpoint === 'Not configured') {
        setMessage({
          type: 'error',
          text: 'MCP server endpoint is not configured. Deploy the MCP server first.'
        })
        return
      }

      // Call the GraphQL mutation to register the MCP server
      const response = await client.mutations.registerMCPServer({
        endpoint: currentMCPInfo.endpoint,
        environment: currentMCPInfo.environment
      })
      
      if (response.data) {
        const result = typeof response.data === 'string' ? JSON.parse(response.data) : response.data
        
        if (result.success) {
          setMessage({
            type: 'success',
            text: `Successfully registered MCP server: ${result.serverId} v${result.version}`
          })
          
          // Refresh the list to show the newly registered server
          await fetchRegistryServers()
        } else {
          setMessage({
            type: 'error',
            text: result.message || 'Failed to register MCP server'
          })
        }
      }
      
    } catch (error) {
      console.error('Error registering MCP server:', error)
      setMessage({
        type: 'error', 
        text: `Failed to register MCP server: ${error}`
      })
    } finally {
      setRegistering(false)
    }
  }

  return (
    <View padding="1rem">
      <Flex direction="column" gap="1.5rem">
        <View>
          <Heading level={3}>MCP Server Environment Info</Heading>
          <Text variation="secondary">
            Current environment MCP server details from amplify_outputs.json
          </Text>
        </View>

        {message && (
          <Alert
            variation={message.type}
            isDismissible
            onDismiss={() => setMessage(null)}
          >
            {message.text}
          </Alert>
        )}

        <Card variation="outlined">
          <Flex direction="column" gap="1rem">
            <Flex justifyContent="space-between" alignItems="center">
              <Heading level={4}>Current Environment</Heading>
              <Badge variation="info">{currentMCPInfo.environment}</Badge>
            </Flex>
            
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell><strong>MCP Endpoint</strong></TableCell>
                  <TableCell>{currentMCPInfo.endpoint}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>AWS Region</strong></TableCell>
                  <TableCell>{currentMCPInfo.region}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Lambda Function</strong></TableCell>
                  <TableCell>{currentMCPInfo.functionName}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Log Group</strong></TableCell>
                  <TableCell>{currentMCPInfo.logGroup}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Flex>
        </Card>

        <Card variation="outlined">
          <Flex direction="column" gap="1rem">
            <Heading level={4}>Available Tools ({availableTools.length})</Heading>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell as="th">Tool Name</TableCell>
                  <TableCell as="th">Description</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {availableTools.map((tool, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Text fontWeight="semibold">{tool.name}</Text>
                    </TableCell>
                    <TableCell>
                      <Text>{tool.description}</Text>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Flex>
        </Card>

        <Card variation="outlined">
          <Flex direction="column" gap="1rem">
            <Heading level={4}>Registry Status</Heading>
            
            {loading ? (
              <Flex justifyContent="center">
                <Loader size="small" />
              </Flex>
            ) : (
              <Flex direction="column" gap="1rem">
                <Flex justifyContent="space-between" alignItems="center">
                  <Text>
                    Registry contains <strong>{registryServers.length}</strong> MCP server{registryServers.length !== 1 ? 's' : ''}
                  </Text>
                  {isServerRegistered() ? (
                    <Badge variation="success">✓ Registered</Badge>
                  ) : (
                    <Badge variation="warning">Not Registered</Badge>
                  )}
                </Flex>

                {!isServerRegistered() && currentMCPInfo.endpoint !== 'Not configured' && (
                  <Flex direction="column" gap="0.5rem">
                    <Text variation="secondary">
                      The current environment's MCP server is not registered in the registry.
                    </Text>
                    <Button
                      variation="primary"
                      size="small"
                      onClick={registerCurrentServer}
                      isLoading={registering}
                      loadingText="Registering..."
                    >
                      Register Current MCP Server
                    </Button>
                  </Flex>
                )}

                {currentMCPInfo.endpoint === 'Not configured' && (
                  <Alert variation="warning">
                    MCP server endpoint is not configured in this environment.
                  </Alert>
                )}
              </Flex>
            )}
          </Flex>
        </Card>

        <Card variation="outlined">
          <Flex direction="column" gap="1rem">
            <Heading level={4}>Deployment Integration Ideas</Heading>
            <Text variation="secondary">
              Future enhancements for automatic MCP server registration:
            </Text>
            <View as="ul" paddingLeft="1rem">
              <li>
                <Text fontSize="0.875rem">
                  <strong>Post-deployment hook:</strong> Automatically register MCP server after Amplify deployment
                </Text>
              </li>
              <li>
                <Text fontSize="0.875rem">
                  <strong>Environment detection:</strong> Auto-detect environment and register with appropriate settings
                </Text>
              </li>
              <li>
                <Text fontSize="0.875rem">
                  <strong>Health check validation:</strong> Verify MCP server is responding before registration
                </Text>
              </li>
              <li>
                <Text fontSize="0.875rem">
                  <strong>Cleanup on destroy:</strong> Remove registry entries when environment is torn down
                </Text>
              </li>
            </View>
          </Flex>
        </Card>
      </Flex>
    </View>
  )
}

export default MCPEnvironmentInfo