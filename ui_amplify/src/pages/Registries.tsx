import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
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
  Icon,
  Divider,
  Button
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
  tools?: string[] // Tool names associated with this agent
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
  const navigate = useNavigate()
  const [agents, setAgents] = useState<Agent[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [loadingAgents, setLoadingAgents] = useState(true)
  const [loadingTools, setLoadingTools] = useState(true)
  const [agentError, setAgentError] = useState<string | null>(null)
  const [toolError, setToolError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set())

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
          setAgentError(data.error)
        }
      }
    } catch (err) {
      console.error('Error fetching agents:', err)
      setAgentError('Failed to fetch agents')
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
          setToolError(data.error)
        }
      }
    } catch (err) {
      console.error('Error fetching tools:', err)
      setToolError('Failed to fetch tools')
    } finally {
      setLoadingTools(false)
    }
  }

  const toggleAgentExpansion = (agentId: string) => {
    const newExpanded = new Set(expandedAgents)
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId)
    } else {
      newExpanded.add(agentId)
    }
    setExpandedAgents(newExpanded)
  }

  // Filter logic that searches both agents and tools
  const getFilteredData = () => {
    const query = searchQuery.toLowerCase()
    
    if (!query) {
      return { filteredAgents: agents, relevantTools: new Set<string>() }
    }

    const relevantTools = new Set<string>()
    
    // Find all tools that match the search
    tools.forEach(tool => {
      if (tool.name.toLowerCase().includes(query) || 
          tool.description.toLowerCase().includes(query)) {
        relevantTools.add(tool.name)
      }
    })

    // Filter agents based on:
    // 1. Agent name/description matches
    // 2. Agent has a tool that matches
    const filteredAgents = agents.filter(agent => {
      const agentMatches = agent.name.toLowerCase().includes(query) || 
                          agent.description.toLowerCase().includes(query)
      
      const hasMatchingTool = agent.tools?.some(toolName => 
        relevantTools.has(toolName) ||
        toolName.toLowerCase().includes(query)
      )
      
      return agentMatches || hasMatchingTool
    })

    return { filteredAgents, relevantTools }
  }

  const { filteredAgents, relevantTools } = getFilteredData()

  const renderTool = (toolName: string, tool?: Tool) => {
    const isHighlighted = searchQuery && (
      relevantTools.has(toolName) ||
      toolName.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
      <Card 
        key={toolName}
        variation="outlined" 
        marginBottom="5px"
        backgroundColor={isHighlighted ? 'yellow.10' : undefined}
      >
        <Flex justifyContent="space-between" alignItems="center">
          <View>
            <Flex alignItems="center" gap="10px">
              <Icon
                ariaLabel="Tool"
                viewBox={{ width: 16, height: 16 }}
                paths={[
                  {
                    d: "M22.7 19L13.6 9.9C14.5 7.6 14 4.9 12.1 3C10.1 1 7.1 0.6 4.7 1.7L9 6L6 9L1.6 4.7C0.4 7.1 0.9 10.1 2.9 12.1C4.8 14 7.5 14.5 9.8 13.6L18.9 22.7C19.3 23.1 19.9 23.1 20.3 22.7L22.6 20.4C23.1 20 23.1 19.4 22.7 19Z",
                    fill: "currentColor"
                  }
                ]}
              />
              <Text fontWeight="bold">{toolName}</Text>
            </Flex>
            {tool && (
              <Text fontSize="small" color="gray" marginTop="5px">
                {tool.description}
              </Text>
            )}
          </View>
          {tool && (
            <Badge size="small">{tool.version}</Badge>
          )}
        </Flex>
      </Card>
    )
  }

  const renderAgent = (agent: Agent) => {
    const isExpanded = expandedAgents.has(agent.id)
    const agentTools = agent.tools || []
    const toolObjects = agentTools.map(toolName => 
      tools.find(t => t.name === toolName)
    )

    return (
      <Card key={agent.id} variation="elevated" marginBottom="15px">
        <View
          onClick={() => toggleAgentExpansion(agent.id)}
          style={{ cursor: 'pointer' }}
        >
          <Flex justifyContent="space-between" alignItems="center">
            <Flex alignItems="center" gap="15px">
              <Icon
                ariaLabel={isExpanded ? "Collapse" : "Expand"}
                viewBox={{ width: 20, height: 20 }}
                paths={[
                  {
                    d: isExpanded 
                      ? "M7 14l5-5 5 5z" 
                      : "M7 10l5 5 5-5z",
                    fill: "currentColor"
                  }
                ]}
              />
              <View>
                <Flex alignItems="center" gap="10px">
                  <Icon
                    ariaLabel="Agent"
                    viewBox={{ width: 20, height: 20 }}
                    paths={[
                      {
                        d: "M12 2C13.1 2 14 2.9 14 4S13.1 6 12 6 10 5.1 10 4 10.9 2 12 2M12 7C14.2 7 16 8.8 16 11S14.2 15 12 15 8 13.2 8 11 9.8 7 12 7M12 16.5C14.5 16.5 19 17.8 19 20.5V22H5V20.5C5 17.8 9.5 16.5 12 16.5Z",
                        fill: "currentColor"
                      }
                    ]}
                  />
                  <Heading level={5}>{agent.name}</Heading>
                </Flex>
                <Text fontSize="small" color="gray">{agent.description}</Text>
              </View>
            </Flex>
            <Flex gap="10px" alignItems="center">
              <Badge>{agentTools.length} tools</Badge>
              <Badge variation="info">{agent.version}</Badge>
            </Flex>
          </Flex>
        </View>

        {isExpanded && (
          <View marginTop="15px" marginLeft="35px">
            <Divider marginBottom="10px" />
            <Flex justifyContent="space-between" alignItems="flex-start">
              <View flex="1">
                <Text fontSize="small" fontWeight="bold" marginBottom="10px">
                  Associated Tools:
                </Text>
                {agentTools.length > 0 ? (
                  agentTools.map((toolName, index) => 
                    renderTool(toolName, toolObjects[index])
                  )
                ) : (
                  <Text fontSize="small" color="gray">No tools configured</Text>
                )}
              </View>
              <Flex gap="10px" direction="column" minWidth="140px">
                <Button
                  variation="primary"
                  size="small"
                  isFullWidth
                  onClick={(e) => {
                    e.stopPropagation()
                    navigate(`/execute?agent=${encodeURIComponent(agent.name)}`)
                  }}
                >
                  Execute Agent
                </Button>
                <Button
                  size="small"
                  isFullWidth
                  onClick={(e) => {
                    e.stopPropagation()
                    navigate(`/history?agent=${encodeURIComponent(agent.name)}`)
                  }}
                >
                  View History
                </Button>
              </Flex>
            </Flex>
          </View>
        )}
      </Card>
    )
  }

  const loading = loadingAgents || loadingTools

  return (
    <View>
      <Heading level={2}>Agent & Tool Registry</Heading>
      
      {(agentError || toolError) && (
        <Alert variation="error" marginTop="10px">
          {agentError || toolError}
        </Alert>
      )}

      <Card variation="elevated" marginTop="20px">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
          <View>
            <Heading level={4}>Registered Agents</Heading>
            <Text fontSize="small" color="gray" marginTop="5px">
              Click on an agent to view its associated tools
            </Text>
          </View>
          <SearchField
            label="Search"
            placeholder="Search agents or tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
            width="300px"
          />
        </Flex>
        
        {loading ? (
          <Loader size="large" />
        ) : filteredAgents.length > 0 ? (
          <View>
            {searchQuery && (
              <Alert variation="info" marginBottom="15px">
                Showing {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''} 
                {relevantTools.size > 0 && ` with ${relevantTools.size} matching tool${relevantTools.size !== 1 ? 's' : ''}`}
              </Alert>
            )}
            {filteredAgents.map(agent => renderAgent(agent))}
          </View>
        ) : (
          <Text marginTop="10px">
            {agents.length === 0 
              ? 'No agents registered yet.' 
              : 'No agents or tools match your search criteria'}
          </Text>
        )}
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>About the Registry</Heading>
        <Text marginTop="10px">
          This registry shows all registered AI agents and their associated tools. 
          Click on any agent to expand and view the tools it can use. 
          Use the search bar to filter by agent name, tool name, or description.
        </Text>
      </Card>
    </View>
  )
}

export default Registries