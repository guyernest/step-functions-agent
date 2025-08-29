import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  View,
  Loader,
  Alert,
  Badge,
  SearchField,
  Flex,
  Divider,
  Button,
  Table,
  TableCell,
  TableBody,
  TableHead,
  TableRow,
  Collection,
  Tabs
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'
import MCPEnvironmentInfo from '../components/MCPEnvironmentInfo'

const client = generateClient<Schema>()

interface MCPServer {
  server_id: string
  version: string
  server_name: string
  description: string
  endpoint_url: string
  protocol_type: string
  authentication_type: string
  api_key_header?: string
  available_tools: Array<{
    name: string
    description: string
    inputSchema?: any
  }>
  status: string
  health_check_url?: string
  health_check_interval?: number
  deployment_stack?: string
  deployment_region?: string
  configuration?: string
  metadata?: string
  created_at: string
  updated_at: string
  created_by?: string
}

interface ConnectionResult {
  success: boolean
  message: string
  response_time?: number
}

const MCPServers: React.FC = () => {
  const [servers, setServers] = useState<MCPServer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedServers, setExpandedServers] = useState<Set<string>>(new Set())
  const [testingConnection, setTestingConnection] = useState<string | null>(null)
  const [connectionResults, setConnectionResults] = useState<Record<string, ConnectionResult>>({})

  useEffect(() => {
    fetchServers()
  }, [])

  const fetchServers = async () => {
    try {
      setLoading(true)
      const response = await client.queries.listMCPServersFromRegistry({})
      if (response.data) {
        setServers(response.data as MCPServer[])
      }
    } catch (err) {
      console.error('Error fetching MCP servers:', err)
      setError('Failed to load MCP servers')
    } finally {
      setLoading(false)
    }
  }

  const testConnection = async (serverId: string) => {
    const server = servers.find(s => s.server_id === serverId)
    if (!server) return

    setTestingConnection(serverId)
    try {
      const startTime = Date.now()
      const response = await client.queries.testMCPServerConnection({ server_id: serverId })
      const endTime = Date.now()
      
      if (response.data) {
        const result = typeof response.data === 'string' ? JSON.parse(response.data) : response.data
        setConnectionResults({
          ...connectionResults,
          [serverId]: {
            success: result.success,
            message: result.message,
            response_time: endTime - startTime
          }
        })
      }
    } catch (err) {
      console.error('Error testing connection:', err)
      setConnectionResults({
        ...connectionResults,
        [serverId]: {
          success: false,
          message: `Connection test failed: ${err}`
        }
      })
    } finally {
      setTestingConnection(null)
    }
  }

  const toggleServerExpansion = (serverId: string) => {
    const newExpanded = new Set(expandedServers)
    if (newExpanded.has(serverId)) {
      newExpanded.delete(serverId)
    } else {
      newExpanded.add(serverId)
    }
    setExpandedServers(newExpanded)
  }

  const filteredServers = servers.filter(server =>
    server.server_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    server.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    server.endpoint_url?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    server.server_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    server.available_tools?.some(tool => 
      tool.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description?.toLowerCase().includes(searchQuery.toLowerCase())
    )
  )

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'success'
      case 'inactive': return 'warning'
      case 'error': return 'error'
      default: return 'info'
    }
  }

  const getProtocolColor = (protocol: string) => {
    switch (protocol?.toLowerCase()) {
      case 'jsonrpc': return '#0066cc'
      case 'graphql': return '#e10098'
      case 'rest': return '#61dafb'
      case 'websocket': return '#ffd700'
      default: return '#666666'
    }
  }

  const getAuthTypeDisplay = (authType: string) => {
    switch (authType?.toLowerCase()) {
      case 'api_key': return 'API Key'
      case 'oauth': return 'OAuth'
      case 'iam': return 'IAM'
      case 'none': return 'None'
      default: return authType || 'Unknown'
    }
  }

  if (loading) {
    return (
      <Flex justifyContent="center" alignItems="center" height="400px">
        <Loader variation="linear" />
        <Text marginLeft="1rem">Loading MCP servers...</Text>
      </Flex>
    )
  }

  if (error) {
    return (
      <Alert variation="error" isDismissible onDismiss={() => setError(null)}>
        {error}
      </Alert>
    )
  }

  return (
    <Flex direction="column" gap="2rem">
      <View>
        <Heading level={2}>MCP Servers</Heading>
        <Text variation="secondary">
          Manage and monitor Model Context Protocol (MCP) servers that provide tools and capabilities to AI agents.
        </Text>
      </View>

      <Tabs
        defaultValue="registry"
        items={[
          {
            label: 'Registry',
            value: 'registry',
            content: (
              <Flex direction="column" gap="1.5rem" paddingTop="1rem">
                <Flex gap="1rem" alignItems="center" justifyContent="space-between">
                  <SearchField
                    label="Search MCP servers"
                    placeholder="Search by name, description, endpoint, or tools..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onClear={() => setSearchQuery('')}
                    style={{ flex: 1, maxWidth: '500px' }}
                  />
                  <Flex gap="0.5rem">
                    <Badge variation="info">{servers.length} servers</Badge>
                    <Badge variation="success">
                      {servers.filter(s => s.status === 'active').length} active
                    </Badge>
                  </Flex>
                </Flex>

                {filteredServers.length === 0 ? (
                  <Card>
                    <Flex direction="column" alignItems="center" padding="2rem">
                      <Text>No MCP servers found</Text>
                      <Text variation="secondary">
                        {searchQuery ? 'Try a different search term' : 'No servers have been registered yet'}
                      </Text>
                    </Flex>
                  </Card>
                ) : (
                  <Collection
                    items={filteredServers}
                    type="list"
                    gap="1rem"
                  >
                    {(server) => (
                      <Card key={`${server.server_id}-${server.version}`} variation="outlined">
                        <Flex direction="column" gap="1rem">
                          <Flex justifyContent="space-between" alignItems="flex-start">
                            <Flex direction="column" gap="0.5rem">
                              <Flex gap="1rem" alignItems="center">
                                <Heading level={4}>{server.server_name}</Heading>
                                <Badge variation={getStatusColor(server.status)}>
                                  {server.status}
                                </Badge>
                                <Badge 
                                  backgroundColor={getProtocolColor(server.protocol_type)}
                                  color="white"
                                >
                                  {server.protocol_type.toUpperCase()}
                                </Badge>
                                <Badge variation="info">
                                  {getAuthTypeDisplay(server.authentication_type)}
                                </Badge>
                              </Flex>
                              <Text variation="secondary">{server.description}</Text>
                              <Text fontSize="0.875rem" color="gray">
                                <strong>Endpoint:</strong> {server.endpoint_url}
                              </Text>
                              <Text fontSize="0.875rem" color="gray">
                                <strong>Version:</strong> {server.version} | 
                                <strong> Server ID:</strong> {server.server_id}
                              </Text>
                            </Flex>
                            <Flex gap="0.5rem">
                              <Button
                                size="small"
                                variation={testingConnection === server.server_id ? "primary" : "link"}
                                onClick={() => testConnection(server.server_id)}
                                isLoading={testingConnection === server.server_id}
                              >
                                Test Connection
                              </Button>
                              <Button
                                size="small"
                                onClick={() => toggleServerExpansion(server.server_id)}
                              >
                                {expandedServers.has(server.server_id) ? 'Hide' : 'Show'} Details
                              </Button>
                            </Flex>
                          </Flex>

                          {connectionResults[server.server_id] && (
                            <Alert
                              variation={connectionResults[server.server_id].success ? 'success' : 'error'}
                              isDismissible={true}
                              onDismiss={() => {
                                const newResults = { ...connectionResults }
                                delete newResults[server.server_id]
                                setConnectionResults(newResults)
                              }}
                            >
                              <Flex direction="column" gap="0.25rem">
                                <Text fontWeight="bold">
                                  {connectionResults[server.server_id].success ? 'Connection Successful' : 'Connection Failed'}
                                </Text>
                                <Text>{connectionResults[server.server_id].message}</Text>
                                {connectionResults[server.server_id].response_time && (
                                  <Text fontSize="0.875rem">
                                    Response time: {connectionResults[server.server_id].response_time}ms
                                  </Text>
                                )}
                              </Flex>
                            </Alert>
                          )}

                          {expandedServers.has(server.server_id) && (
                            <>
                              <Divider />
                              <View>
                                <Heading level={5} marginBottom="1rem">Available Tools ({server.available_tools?.length || 0})</Heading>
                                {server.available_tools && server.available_tools.length > 0 ? (
                                  <Table>
                                    <TableHead>
                                      <TableRow>
                                        <TableCell as="th">Tool Name</TableCell>
                                        <TableCell as="th">Description</TableCell>
                                      </TableRow>
                                    </TableHead>
                                    <TableBody>
                                      {server.available_tools.map((tool, index) => (
                                        <TableRow key={index}>
                                          <TableCell>
                                            <Text fontWeight="semibold">{tool.name}</Text>
                                          </TableCell>
                                          <TableCell>
                                            <Text>{tool.description || 'No description'}</Text>
                                          </TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                ) : (
                                  <Text variation="secondary">No tools available</Text>
                                )}
                              </View>

                              <Divider />
                              <Flex gap="2rem">
                                <View flex={1}>
                                  <Heading level={5} marginBottom="0.5rem">Configuration</Heading>
                                  <Flex direction="column" gap="0.25rem">
                                    {server.health_check_url && (
                                      <Text fontSize="0.875rem">
                                        <strong>Health Check URL:</strong> {server.health_check_url}
                                      </Text>
                                    )}
                                    {server.health_check_interval && (
                                      <Text fontSize="0.875rem">
                                        <strong>Health Check Interval:</strong> {server.health_check_interval}s
                                      </Text>
                                    )}
                                    {server.api_key_header && (
                                      <Text fontSize="0.875rem">
                                        <strong>API Key Header:</strong> {server.api_key_header}
                                      </Text>
                                    )}
                                    {server.deployment_stack && (
                                      <Text fontSize="0.875rem">
                                        <strong>Deployment Stack:</strong> {server.deployment_stack}
                                      </Text>
                                    )}
                                    {server.deployment_region && (
                                      <Text fontSize="0.875rem">
                                        <strong>Region:</strong> {server.deployment_region}
                                      </Text>
                                    )}
                                  </Flex>
                                </View>
                                <View flex={1}>
                                  <Heading level={5} marginBottom="0.5rem">Metadata</Heading>
                                  <Flex direction="column" gap="0.25rem">
                                    <Text fontSize="0.875rem">
                                      <strong>Created:</strong> {new Date(server.created_at).toLocaleString()}
                                    </Text>
                                    <Text fontSize="0.875rem">
                                      <strong>Updated:</strong> {new Date(server.updated_at).toLocaleString()}
                                    </Text>
                                    {server.created_by && (
                                      <Text fontSize="0.875rem">
                                        <strong>Created By:</strong> {server.created_by}
                                      </Text>
                                    )}
                                  </Flex>
                                </View>
                              </Flex>
                            </>
                          )}
                        </Flex>
                      </Card>
                    )}
                  </Collection>
                )}
              </Flex>
            )
          },
          {
            label: 'Environment Info',
            value: 'environment',
            content: <MCPEnvironmentInfo />
          }
        ]}
      />
    </Flex>
  )
}

export default MCPServers