import React, { useState, useEffect } from 'react'
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
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState('')
  const [input, setInput] = useState('')
  const [executionName, setExecutionName] = useState('')
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    setLoading(true)
    try {
      const tableName = localStorage.getItem('agentRegistryTableName') || 'AgentRegistry-prod'
      const response = await client.queries.listAgentsFromRegistry({ tableName })
      
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
      const response = await client.mutations.startAgentExecution({
        agentName: selectedAgent,
        input: input || undefined,
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
          setSuccess(`Execution started successfully! ARN: ${data.executionArn}`)
          // Clear form
          setInput('')
          setExecutionName('')
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
      
      {success && (
        <Alert 
          variation="success" 
          marginTop="10px"
          onDismiss={() => setSuccess(null)}
          isDismissible
        >
          {success}
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
              onChange={(e) => setSelectedAgent(e.target.value)}
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
              label="Input (JSON)"
              placeholder='{"messages": [{"role": "user", "content": "What can you do?"}]}'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={5}
              marginBottom="15px"
            />

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
          Select an agent from the dropdown, provide optional input in JSON format, 
          and click "Start Execution" to begin.
        </Text>
        <Text marginTop="10px">
          The input should be in the format expected by the agent's state machine. 
          If no input is provided, a default message will be sent.
        </Text>
      </Card>
    </View>
  )
}

export default AgentExecution