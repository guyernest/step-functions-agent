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
  Flex,
  SwitchField
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

interface Agent {
  id: string
  name: string
  description: string
}

interface TestPrompt {
  id: string
  test_name: string
  description?: string | null
  test_input: string  // AWSJSON - comes as a JSON string
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
  const [testPrompts, setTestPrompts] = useState<TestPrompt[]>([])
  const [selectedTestPrompt, setSelectedTestPrompt] = useState('')
  const [testMode, setTestMode] = useState(false)
  const [autoApprove, setAutoApprove] = useState(false)
  const [showSavePromptModal, setShowSavePromptModal] = useState(false)
  const [newPromptName, setNewPromptName] = useState('')
  const [newPromptDescription, setNewPromptDescription] = useState('')

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
  const handleAgentChange = async (agentName: string) => {
    setSelectedAgent(agentName)
    setSelectedTestPrompt('')
    setTestPrompts([])
    if (agentName) {
      setSearchParams({ agent: agentName })
      // Load test prompts for this agent
      await loadTestPrompts(agentName)
    } else {
      setSearchParams({})
    }
  }

  const loadTestPrompts = async (agentName: string) => {
    try {
      const response = await client.queries.listTestEvents({
        resource_type: 'agent',
        resource_id: agentName
      })
      
      if (response.data) {
        const prompts = response.data
          .filter((event): event is NonNullable<typeof event> => event !== null && event !== undefined)
          .map(event => ({
            id: event.id,
            test_name: event.test_name,
            description: event.description,
            test_input: event.test_input  // Renamed from 'input'
          } as TestPrompt))
        setTestPrompts(prompts)
      }
    } catch (err) {
      console.error('Error loading test prompts:', err)
      // Don't show error - test prompts are optional
    }
  }

  const handleTestPromptChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const promptId = e.target.value
    setSelectedTestPrompt(promptId)
    
    if (promptId) {
      const testPrompt = testPrompts.find(p => p.id === promptId)
      if (testPrompt && testPrompt.test_input) {
        // Parse the JSON string and extract the prompt
        try {
          const parsed = JSON.parse(testPrompt.test_input);
          if (parsed.prompt) {
            setInput(parsed.prompt);
          }
        } catch (e) {
          console.error('Error parsing test_input:', e);
        }
      }
    }
  }

  const handleSaveTestPrompt = async () => {
    if (!selectedAgent || !newPromptName || !input) {
      setError('Agent name, test name, and prompt are required')
      return
    }

    try {
      const response = await client.mutations.saveTestEvent({
        resource_type: 'agent',
        resource_id: selectedAgent,
        test_name: newPromptName,
        description: newPromptDescription || undefined,
        test_input: JSON.stringify({ prompt: input }),  // Renamed from 'input' and stringified
        metadata: JSON.stringify({
          saved_from_execution: true,
          test_mode: testMode,
          auto_approve: autoApprove
        })
      })

      if (response.data) {
        // Reload test prompts
        await loadTestPrompts(selectedAgent)
        setShowSavePromptModal(false)
        setNewPromptName('')
        setNewPromptDescription('')
        setSuccess('Test prompt saved successfully!')
      }
    } catch (err) {
      console.error('Error saving test prompt:', err)
      setError('Failed to save test prompt')
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
      const messageData = {
        messages: [
          {
            role: "user",
            content: input.trim()
          }
        ]
      }

      // Add test mode metadata if enabled
      if (testMode) {
        (messageData as any).metadata = {
          test_mode: true,
          auto_approve: autoApprove
        }
      }

      const formattedInput = input.trim() ? JSON.stringify(messageData) : undefined

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

            {selectedAgent && testPrompts.length > 0 && (
              <SelectField
                label="Test Prompts (Optional)"
                value={selectedTestPrompt}
                onChange={handleTestPromptChange}
                marginBottom="15px"
                descriptiveText="Select a predefined test prompt or enter custom input below"
              >
                <option value="">-- Custom input --</option>
                {testPrompts.map((prompt) => (
                  <option key={prompt.id} value={prompt.id}>
                    {prompt.test_name} {prompt.description && `- ${prompt.description}`}
                  </option>
                ))}
              </SelectField>
            )}

            {selectedAgent && (
              <Card variation="outlined" marginBottom="15px">
                <Heading level={5}>Test Mode Options</Heading>
                <Flex direction="column" gap="10px">
                  <SwitchField
                    label="Test Mode"
                    isChecked={testMode}
                    onChange={(e) => setTestMode(e.target.checked)}
                    descriptiveText="Enable test mode for this execution"
                  />
                  {testMode && (
                    <SwitchField
                      label="Auto-Approve"
                      isChecked={autoApprove}
                      onChange={(e) => setAutoApprove(e.target.checked)}
                      descriptiveText="Automatically approve any human approval steps"
                    />
                  )}
                </Flex>
              </Card>
            )}

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
              <Flex gap="10px">
                <Button
                  variation="primary"
                  onClick={handleExecute}
                  isLoading={executing}
                  isDisabled={!selectedAgent || executing}
                >
                  Start Execution
                </Button>
                
                {selectedAgent && input && (
                  <Button
                    onClick={() => setShowSavePromptModal(true)}
                  >
                    Save as Test Prompt
                  </Button>
                )}
              </Flex>
              
              {selectedAgent && (
                <Text fontSize="small" color="gray">
                  Selected: {selectedAgent}
                </Text>
              )}
            </Flex>
          </View>
        )}
      </Card>

      {showSavePromptModal && (
        <Card variation="elevated" marginTop="20px">
          <Heading level={4}>Save Test Prompt</Heading>
          <Flex direction="column" gap="15px">
            <TextField
              label="Test Name"
              value={newPromptName}
              onChange={(e) => setNewPromptName(e.target.value)}
              placeholder="e.g., basic_query_test"
              required
            />
            <TextAreaField
              label="Description"
              value={newPromptDescription}
              onChange={(e) => setNewPromptDescription(e.target.value)}
              placeholder="Describe what this test validates"
              rows={3}
            />
            <Flex gap="10px">
              <Button
                variation="primary"
                onClick={handleSaveTestPrompt}
              >
                Save Test Prompt
              </Button>
              <Button
                onClick={() => {
                  setShowSavePromptModal(false)
                  setNewPromptName('')
                  setNewPromptDescription('')
                }}
              >
                Cancel
              </Button>
            </Flex>
          </Flex>
        </Card>
      )}

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