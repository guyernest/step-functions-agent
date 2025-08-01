import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  View,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Loader,
  Alert,
  Badge,
  SearchField,
  Flex
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

interface Agent {
  id: string
  name: string
  description: string
  version: string
  type: string
  createdAt: string
}

interface Tool {
  id: string
  name: string
  description: string
  version: string
  type: string
  createdAt: string
}

const Registries: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [loadingAgents, setLoadingAgents] = useState(true)
  const [loadingTools, setLoadingTools] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [agentSearch, setAgentSearch] = useState('')
  const [toolSearch, setToolSearch] = useState('')

  useEffect(() => {
    const agentTableName = localStorage.getItem('agentRegistryTableName') || 'AgentRegistry-prod'
    const toolTableName = localStorage.getItem('toolRegistryTableName') || 'tool-registry-prod'
    fetchAgents(agentTableName)
    fetchTools(toolTableName)
  }, [])

  const fetchAgents = async (tableName: string) => {
    try {
      const response = await client.queries.listAgentsFromRegistry({ tableName })
      console.log('Agents response:', response)
      
      if (response.data) {
        const data = typeof response.data === 'string' 
          ? JSON.parse(response.data) 
          : response.data
        
        if (data.agents) {
          setAgents(data.agents)
        } else if (data.error) {
          setError(data.error)
        }
      }
    } catch (err) {
      console.error('Error fetching agents:', err)
      setError('Failed to fetch agents')
    } finally {
      setLoadingAgents(false)
    }
  }

  const fetchTools = async (tableName: string) => {
    try {
      const response = await client.queries.listToolsFromRegistry({ tableName })
      console.log('Tools response:', response)
      
      if (response.data) {
        const data = typeof response.data === 'string' 
          ? JSON.parse(response.data) 
          : response.data
        
        if (data.tools) {
          setTools(data.tools)
        } else if (data.error) {
          setError(data.error)
        }
      }
    } catch (err) {
      console.error('Error fetching tools:', err)
      setError('Failed to fetch tools')
    } finally {
      setLoadingTools(false)
    }
  }

  // Filter agents based on search
  const filteredAgents = agents.filter(agent => 
    agent.name.toLowerCase().includes(agentSearch.toLowerCase()) ||
    agent.description.toLowerCase().includes(agentSearch.toLowerCase())
  )

  // Filter tools based on search
  const filteredTools = tools.filter(tool => 
    tool.name.toLowerCase().includes(toolSearch.toLowerCase()) ||
    tool.description.toLowerCase().includes(toolSearch.toLowerCase())
  )

  return (
    <View>
      <Heading level={2}>Agent & Tool Registries</Heading>
      
      {error && (
        <Alert variation="error" marginTop="10px">
          {error}
        </Alert>
      )}

      <Card variation="elevated" marginTop="20px">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="10px">
          <Heading level={4}>Registered Agents</Heading>
          {agents.length > 0 && (
            <SearchField
              label="Search agents"
              placeholder="Search by name or description"
              value={agentSearch}
              onChange={(e) => setAgentSearch(e.target.value)}
              onClear={() => setAgentSearch('')}
              width="300px"
            />
          )}
        </Flex>
        
        {loadingAgents ? (
          <Loader size="large" />
        ) : filteredAgents.length > 0 ? (
          <View>
            <Table marginTop="10px">
              <TableHead>
                <TableRow>
                  <TableCell as="th">Name</TableCell>
                  <TableCell as="th">Description</TableCell>
                  <TableCell as="th">Version</TableCell>
                  <TableCell as="th">Type</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredAgents.map((agent) => (
                  <TableRow key={agent.id}>
                    <TableCell>{agent.name}</TableCell>
                    <TableCell>{agent.description}</TableCell>
                    <TableCell>
                      <Badge>{agent.version}</Badge>
                    </TableCell>
                    <TableCell>{agent.type}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {agentSearch && filteredAgents.length === 0 && agents.length > 0 && (
              <Text marginTop="10px" color="gray">
                No agents match your search criteria
              </Text>
            )}
          </View>
        ) : (
          <Text marginTop="10px">
            {agents.length === 0 ? 'No agents registered yet.' : 'No agents match your search criteria'}
          </Text>
        )}
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="10px">
          <Heading level={4}>Registered Tools</Heading>
          {tools.length > 0 && (
            <SearchField
              label="Search tools"
              placeholder="Search by name or description"
              value={toolSearch}
              onChange={(e) => setToolSearch(e.target.value)}
              onClear={() => setToolSearch('')}
              width="300px"
            />
          )}
        </Flex>
        
        {loadingTools ? (
          <Loader size="large" />
        ) : filteredTools.length > 0 ? (
          <View>
            <Table marginTop="10px">
              <TableHead>
                <TableRow>
                  <TableCell as="th">Name</TableCell>
                  <TableCell as="th">Description</TableCell>
                  <TableCell as="th">Version</TableCell>
                  <TableCell as="th">Type</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTools.map((tool) => (
                  <TableRow key={tool.id}>
                    <TableCell>{tool.name}</TableCell>
                    <TableCell>{tool.description}</TableCell>
                    <TableCell>
                      <Badge>{tool.version}</Badge>
                    </TableCell>
                    <TableCell>{tool.type}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {toolSearch && filteredTools.length === 0 && tools.length > 0 && (
              <Text marginTop="10px" color="gray">
                No tools match your search criteria
              </Text>
            )}
          </View>
        ) : (
          <Text marginTop="10px">
            {tools.length === 0 ? 'No tools registered yet.' : 'No tools match your search criteria'}
          </Text>
        )}
      </Card>
    </View>
  )
}

export default Registries