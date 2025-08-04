import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Heading,
  Text,
  View,
  SelectField,
  TextAreaField,
  TextField,
  Button,
  Alert,
  Loader,
  Flex
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

interface Agent {
  id: string
  name: string
  description: string
}

const AgentExecution: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState('')
  const [input, setInput] = useState('')
  const [executionName, setExecutionName] = useState('')
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [executionArn, setExecutionArn] = useState<string | null>(null)

  useEffect(() => {
    fetchAgents()
  }, [])

  // Handle URL parameter for agent selection
  useEffect(() => {
    const agentParam = searchParams.get('agent')
    if (agentParam && agents.length > 0) {
      // Check if the agent exists in the list
      const agentExists = agents.some(agent => agent.name === agentParam)
      if (agentExists) {
        setSelectedAgent(agentParam)
      }
    }
  }, [searchParams, agents])

  // Update URL when agent selection changes
  const handleAgentChange = (agentName: string) => {
    setSelectedAgent(agentName)
    if (agentName) {
      setSearchParams({ agent: agentName })
    } else {
      setSearchParams({})
    }
  }

  const fetchAgents = async () => {
    setLoading(true)
    try {
      const response = await client.queries.listAgentsFromRegistry({})
      
      if (response.data) {
        const validAgents = response.data
          .filter(agent => agent !== null && agent !== undefined)
          .map(agent => ({
            id: agent.id,
            name: agent.name,
            description: agent.description || '',
            version: agent.version || '1.0.0',
            type: agent.type || 'agent',
            createdAt: agent.createdAt || new Date().toISOString(),
            tools: (agent.tools || []).filter((tool): tool is string => tool !== null && tool !== undefined)
          }))
        setAgents(validAgents)
      }
    } catch (err) {
      console.error('Error fetching agents:', err)
      setError('Failed to fetch agents')
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    if (!selectedAgent) {
      setError('Please select an agent')
      return
    }

    setExecuting(true)
    setError(null)
    setSuccess(null)

    try {
      // Format the plain text input into the expected JSON structure
      const formattedInput = input.trim() ? JSON.stringify({
        messages: [
          {
            role: "user",
            content: input.trim()
          }
        ]
      }) : undefined

      const response = await client.mutations.startAgentExecution({
        agentName: selectedAgent,
        input: formattedInput,
        executionName: executionName || undefined
      })

      console.log('Execution response:', response)

      if (response.data) {
        const data = typeof response.data === 'string' 
          ? JSON.parse(response.data) 
          : response.data

        if (data.error) {
          setError(data.error + (data.details ? ': ' + data.details : ''))
        } else {
          setSuccess(`Execution started successfully!`)
          setExecutionArn(data.executionArn)
          // Clear form
          setInput('')
          setExecutionName('')
          
          // Optionally auto-navigate after a short delay
          setTimeout(() => {
            navigate(`/execution/${encodeURIComponent(data.executionArn)}`)
          }, 2000)
        }
      }
    } catch (err) {
      console.error('Error starting execution:', err)
      setError('Failed to start execution')
    } finally {
      setExecuting(false)
    }
  }

  return (
    <View>
      <Heading level={2}>Execute Agent</Heading>
      
      {error && (
        <Alert 
          variation="error" 
          marginTop="10px"
          onDismiss={() => setError(null)}
          isDismissible
        >
          {error}
        </Alert>
      )}
      
      {success && executionArn && (
        <Alert 
          variation="success" 
          marginTop="10px"
          onDismiss={() => {
            setSuccess(null)
            setExecutionArn(null)
          }}
          isDismissible
        >
          <Flex direction="column" gap="10px">
            <Text>{success}</Text>
            <Text fontSize="small" fontFamily="monospace" color="gray">
              {executionArn}
            </Text>
            <Flex gap="10px">
              <Button
                size="small"
                variation="primary"
                onClick={() => navigate(`/execution/${encodeURIComponent(executionArn)}`)}
              >
                View Execution Details
              </Button>
              <Button
                size="small"
                onClick={() => navigate('/history')}
              >
                Go to History
              </Button>
            </Flex>
            <Text fontSize="small" color="gray">
              Redirecting to execution details in 2 seconds...
            </Text>
          </Flex>
        </Alert>
      )}

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Start Agent Execution</Heading>
        
        {loading ? (
          <Loader size="large" />
        ) : (
          <View>
            <SelectField
              label="Select Agent"
              value={selectedAgent}
              onChange={(e) => handleAgentChange(e.target.value)}
              marginBottom="15px"
            >
              <option value="">-- Select an agent --</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.name}>
                  {agent.name} - {agent.description}
                </option>
              ))}
            </SelectField>

            <TextAreaField
              label="Message"
              placeholder="What can you do?"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={3}
              marginBottom="5px"
              descriptiveText="Enter your message or question for the agent"
            />
            
            {!input && selectedAgent && (
              <View marginBottom="15px">
                <Text fontSize="small" color="gray">Example prompts:</Text>
                <Flex gap="5px" wrap="wrap" marginTop="5px">
                  {selectedAgent.includes('sql') && (
                    <>
                      <Button size="small" variation="link" onClick={() => setInput('Show me all tables in the database')}>
                        Show tables
                      </Button>
                      <Button size="small" variation="link" onClick={() => setInput('Get the top 10 customers by revenue')}>
                        Top customers
                      </Button>
                    </>
                  )}
                  {selectedAgent.includes('weather') && (
                    <>
                      <Button size="small" variation="link" onClick={() => setInput('What is the weather in New York?')}>
                        Weather in NY
                      </Button>
                      <Button size="small" variation="link" onClick={() => setInput('Will it rain tomorrow in London?')}>
                        Rain forecast
                      </Button>
                    </>
                  )}
                  {selectedAgent.includes('research') && (
                    <>
                      <Button size="small" variation="link" onClick={() => setInput('Research Apple Inc stock performance')}>
                        Research Apple
                      </Button>
                      <Button size="small" variation="link" onClick={() => setInput('What are the latest tech industry trends?')}>
                        Tech trends
                      </Button>
                    </>
                  )}
                  {!selectedAgent.includes('sql') && !selectedAgent.includes('weather') && !selectedAgent.includes('research') && (
                    <Button size="small" variation="link" onClick={() => setInput('What can you help me with?')}>
                      What can you do?
                    </Button>
                  )}
                </Flex>
              </View>
            )}

            <TextField
              label="Execution Name (optional)"
              placeholder="my-execution-1"
              value={executionName}
              onChange={(e) => setExecutionName(e.target.value)}
              marginBottom="20px"
              descriptiveText="If not provided, a unique name will be generated"
            />

            <Flex justifyContent="space-between" alignItems="center">
              <Button
                variation="primary"
                onClick={handleExecute}
                isLoading={executing}
                isDisabled={!selectedAgent || executing}
              >
                Start Execution
              </Button>
              
              {selectedAgent && (
                <Text fontSize="small" color="gray">
                  Selected: {selectedAgent}
                </Text>
              )}
            </Flex>
          </View>
        )}
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>About Agent Execution</Heading>
        <Text marginTop="10px">
          This page allows you to start executions of registered Step Functions agents. 
          Select an agent from the dropdown, type your message or question, 
          and click "Start Execution" to begin.
        </Text>
        <Text marginTop="10px">
          Simply enter your request in plain text - the system will automatically 
          format it for the agent. Leave empty to send a default greeting.
        </Text>
      </Card>
    </View>
  )
}

export default AgentExecution