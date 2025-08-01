import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Heading,
  Text,
  View,
  Button,
  Loader,
  Alert,
  Badge,
  Flex
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

interface Message {
  role: string
  content: string
  timestamp?: string
}

interface ExecutionDetail {
  executionArn: string
  stateMachineArn: string
  name: string
  status: string
  startDate: string
  stopDate?: string
  agentName: string
  input?: any
  output?: any
}

const getStatusBadgeVariation = (status: string) => {
  switch (status) {
    case 'SUCCEEDED':
      return 'success'
    case 'FAILED':
      return 'error'
    case 'RUNNING':
      return 'info'
    case 'ABORTED':
      return 'warning'
    default:
      return undefined
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString()
}

const ExecutionDetail: React.FC = () => {
  const { executionArn } = useParams<{ executionArn: string }>()
  const navigate = useNavigate()
  const [execution, setExecution] = useState<ExecutionDetail | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (executionArn) {
      fetchExecutionDetails(decodeURIComponent(executionArn))
    }
  }, [executionArn])

  const fetchExecutionDetails = async (arn: string) => {
    setLoading(true)
    setError(null)

    try {
      const response = await client.queries.getStepFunctionExecution({
        executionArn: arn
      })

      console.log('Execution details response:', response)

      if (response.data) {
        const data = typeof response.data === 'string' 
          ? JSON.parse(response.data) 
          : response.data

        if (data.execution) {
          setExecution(data.execution)
          setMessages(data.messages || [])
        } else if (data.error) {
          setError(data.error + (data.details ? ': ' + data.details : ''))
        }
      }
    } catch (err) {
      console.error('Error fetching execution details:', err)
      setError('Failed to fetch execution details')
    } finally {
      setLoading(false)
    }
  }

  const renderMessage = (message: Message, index: number) => {
    const roleColor = message.role === 'user' ? '#1976D2' : 
                     message.role === 'assistant' ? '#388E3C' : '#666'
    
    return (
      <Card key={index} variation="elevated" marginBottom="10px">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="5px">
          <Text fontWeight="bold" color={roleColor}>
            {message.role.charAt(0).toUpperCase() + message.role.slice(1)}
          </Text>
          {message.timestamp && (
            <Text fontSize="small" color="gray">
              {formatDate(message.timestamp)}
            </Text>
          )}
        </Flex>
        <Text style={{ whiteSpace: 'pre-wrap' }}>{message.content}</Text>
      </Card>
    )
  }

  if (loading) {
    return (
      <View padding="20px">
        <Loader size="large" />
      </View>
    )
  }

  return (
    <View>
      <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
        <Heading level={2}>Execution Details</Heading>
        <Button onClick={() => navigate('/history')}>Back to History</Button>
      </Flex>

      {error && (
        <Alert variation="error" marginBottom="20px">
          {error}
        </Alert>
      )}

      {execution && (
        <>
          <Card variation="elevated" marginBottom="20px">
            <Heading level={4}>Execution Information</Heading>
            <View marginTop="10px">
              <Flex gap="20px" wrap="wrap">
                <View>
                  <Text fontWeight="bold">Agent:</Text>
                  <Text>{execution.agentName}</Text>
                </View>
                <View>
                  <Text fontWeight="bold">Name:</Text>
                  <Text>{execution.name || 'Unnamed'}</Text>
                </View>
                <View>
                  <Text fontWeight="bold">Status:</Text>
                  <Badge variation={getStatusBadgeVariation(execution.status)}>
                    {execution.status}
                  </Badge>
                </View>
                <View>
                  <Text fontWeight="bold">Start Time:</Text>
                  <Text>{formatDate(execution.startDate)}</Text>
                </View>
                {execution.stopDate && (
                  <View>
                    <Text fontWeight="bold">End Time:</Text>
                    <Text>{formatDate(execution.stopDate)}</Text>
                  </View>
                )}
              </Flex>
            </View>
          </Card>

          <Card variation="elevated" marginBottom="20px">
            <Heading level={4}>Conversation Messages</Heading>
            {messages.length > 0 ? (
              <View marginTop="10px">
                {messages.map((message, index) => renderMessage(message, index))}
              </View>
            ) : (
              <Text marginTop="10px" color="gray">
                No messages found in this execution.
              </Text>
            )}
          </Card>

          {(execution.input || execution.output) && (
            <Card variation="elevated">
              <Heading level={4}>Execution Data</Heading>
              
              {execution.input && (
                <View marginTop="10px">
                  <Text fontWeight="bold" marginBottom="5px">Input:</Text>
                  <Card variation="outlined">
                    <Text fontSize="small" fontFamily="monospace" style={{ whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(execution.input, null, 2)}
                    </Text>
                  </Card>
                </View>
              )}
              
              {execution.output && (
                <View marginTop="10px">
                  <Text fontWeight="bold" marginBottom="5px">Output:</Text>
                  <Card variation="outlined">
                    <Text fontSize="small" fontFamily="monospace" style={{ whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(execution.output, null, 2)}
                    </Text>
                  </Card>
                </View>
              )}
            </Card>
          )}
        </>
      )}
    </View>
  )
}

export default ExecutionDetail