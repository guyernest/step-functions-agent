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
  Flex,
  Divider
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'
import { MessageRenderer } from '../components/MessageRenderer'

const client = generateClient<Schema>()

interface Message {
  role: string
  content: any // Can be string, object, or array
  timestamp?: string
  type?: string
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

const calculateDuration = (startDate: string, endDate?: string) => {
  const start = new Date(startDate).getTime()
  const end = endDate ? new Date(endDate).getTime() : Date.now()
  const durationMs = end - start
  
  const seconds = Math.floor(durationMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

const ExecutionDetail: React.FC = () => {
  const { executionArn } = useParams<{ executionArn: string }>()
  const navigate = useNavigate()
  const [execution, setExecution] = useState<ExecutionDetail | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  useEffect(() => {
    if (executionArn) {
      fetchExecutionDetails(decodeURIComponent(executionArn))
    }
  }, [executionArn])

  // Auto-refresh for running executions
  useEffect(() => {
    if (!execution || !autoRefresh) return

    // Only refresh if execution is still running
    if (execution.status === 'RUNNING') {
      const interval = setInterval(() => {
        fetchExecutionDetails(decodeURIComponent(executionArn!), true)
      }, 3000) // Refresh every 3 seconds

      return () => clearInterval(interval)
    } else {
      // Stop auto-refresh when execution completes
      setAutoRefresh(false)
    }
  }, [execution, executionArn, autoRefresh])

  const fetchExecutionDetails = async (arn: string, isRefresh = false) => {
    // Only show loading on initial load, not on refresh
    if (!isRefresh) {
      setLoading(true)
    }
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
          setLastUpdated(new Date())
        } else if (data.error) {
          setError(data.error + (data.details ? ': ' + data.details : ''))
        }
      }
    } catch (err) {
      console.error('Error fetching execution details:', err)
      setError('Failed to fetch execution details')
    } finally {
      // Only set loading false if we were showing loading
      if (!isRefresh) {
        setLoading(false)
      }
    }
  }

  const renderMessage = (message: Message, index: number) => {
    // Check if this is actually a tool result disguised as a user message
    const isToolResult = message.role === 'user' && 
                        Array.isArray(message.content) && 
                        message.content.length > 0 &&
                        message.content[0].type === 'tool_result'
    
    const displayRole = isToolResult ? 'tool' : message.role
    
    const roleColor = displayRole === 'user' ? '#1976D2' : 
                     displayRole === 'assistant' ? '#388E3C' : 
                     displayRole === 'tool' ? '#9C27B0' : '#666'
    
    const roleIcon = displayRole === 'user' ? '👤' : 
                    displayRole === 'assistant' ? '🤖' : 
                    displayRole === 'tool' ? '🔧' : '📋'
    
    const roleLabel = isToolResult ? 'Tool Result' : 
                     displayRole.charAt(0).toUpperCase() + displayRole.slice(1)
    
    return (
      <Card key={index} variation="elevated" marginBottom="10px">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="10px">
          <Flex alignItems="center" gap="10px">
            <Text fontSize="large">{roleIcon}</Text>
            <Text fontWeight="bold" color={roleColor}>
              {roleLabel}
            </Text>
          </Flex>
          {message.timestamp && (
            <Text fontSize="small" color="gray">
              {formatDate(message.timestamp)}
            </Text>
          )}
        </Flex>
        <Divider marginBottom="10px" />
        <MessageRenderer content={message.content} role={displayRole} messageType={message.type} />
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
            <Flex justifyContent="space-between" alignItems="center">
              <Heading level={4}>Execution Information</Heading>
              {lastUpdated && execution.status === 'RUNNING' && (
                <Text fontSize="small" color="gray">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </Text>
              )}
            </Flex>
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
                  <Flex alignItems="center" gap="10px">
                    <Badge variation={getStatusBadgeVariation(execution.status)}>
                      {execution.status}
                    </Badge>
                    {execution.status === 'RUNNING' && (
                      <Loader size="small" />
                    )}
                  </Flex>
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
                <View>
                  <Text fontWeight="bold">Duration:</Text>
                  <Text>{calculateDuration(execution.startDate, execution.stopDate)}</Text>
                </View>
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