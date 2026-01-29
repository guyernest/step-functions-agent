import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  Heading,
  Text,
  View,
  Button,
  TextField,
  Flex,
  Alert,
  TextAreaField,
  Loader
} from '@aws-amplify/ui-react'
import { useStepFunctions, ActivityTask } from '../hooks/useStepFunctions'

const ApprovalDashboard: React.FC = () => {
  const [activityArn, setActivityArn] = useState('')
  const [task, setTask] = useState<ActivityTask | null>(null)
  const [modifiedInput, setModifiedInput] = useState<any>({})
  const [isProcessing, setIsProcessing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const pollingRef = useRef<boolean>(false)
  
  const {
    pollActivityTask,
    sendTaskSuccess,
    sendTaskFailure,
    isPolling,
    setIsPolling,
    error,
    setError
  } = useStepFunctions()

  // Poll for activity tasks
  useEffect(() => {
    if (!isPolling || !activityArn) {
      pollingRef.current = false
      return
    }

    pollingRef.current = true

    const pollForTasks = async () => {
      while (pollingRef.current) {
        try {
          console.log('Polling for activity task...')
          const activityTask = await pollActivityTask(activityArn)
          
          if (activityTask) {
            console.log('Received task:', activityTask)
            setTask(activityTask)
            
            // Extract tool input generically
            const toolInput = activityTask.input?.tool_input || activityTask.input?.input || {}
            setModifiedInput(toolInput)
            setMessage(null)
            setError(null)
            
            // Stop polling when we get a task
            pollingRef.current = false
            setIsPolling(false)
          } else {
            setMessage('No pending approvals')
          }
        } catch (err) {
          console.error('Polling error:', err)
          // Continue polling even on error
          await new Promise(resolve => setTimeout(resolve, 5000))
        }
      }
    }

    pollForTasks()

    return () => {
      pollingRef.current = false
    }
  }, [isPolling, activityArn, pollActivityTask, setIsPolling, setError])

  const handleStartPolling = () => {
    if (!activityArn) {
      setError('Please enter an activity ARN')
      return
    }
    setIsPolling(true)
    setError(null)
    setMessage('Started polling for approval tasks...')
  }

  const handleStopPolling = () => {
    setIsPolling(false)
    pollingRef.current = false
    setTask(null)
    setModifiedInput({})
    setMessage('Stopped polling')
  }

  const handleApproval = async (approved: boolean) => {
    if (!task) return

    setIsProcessing(true)
    setError(null)

    try {
      if (approved) {
        const output = {
          approved: true,
          name: task.input.tool_name || task.input.name || '',
          id: task.input.tool_use_id || task.input.id || '',
          input: modifiedInput
        }
        
        await sendTaskSuccess(task.taskToken, output, activityArn || undefined)
        setMessage('Task approved successfully')
      } else {
        const toolName = task.input.tool_name || task.input.name || 'tool'
        await sendTaskFailure(
          task.taskToken,
          'NotApproved',
          `Human rejected the ${toolName} execution`,
          activityArn || undefined
        )
        setMessage('Task rejected successfully')
      }

      setTask(null)
      setModifiedInput({})
      
      // Resume polling after processing
      if (activityArn) {
        setTimeout(() => {
          setIsPolling(true)
          setMessage(null)
        }, 2000)
      }
    } catch (err) {
      console.error('Error processing approval:', err)
      setError('Failed to process approval')
    } finally {
      setIsProcessing(false)
    }
  }

  // Get default activity ARN from environment
  useEffect(() => {
    const region = localStorage.getItem('awsRegion') || 'us-west-2'
    const accountId = localStorage.getItem('awsAccountId') || ''
    if (accountId) {
      setActivityArn(`arn:aws:states:${region}:${accountId}:activity:sql-agent-approval-activity-prod`)
    }
  }, [])

  // Helper functions for rendering tool inputs
  const getToolDisplayName = (toolName: string): string => {
    const toolDisplayNames: { [key: string]: string } = {
      'execute_sql_query': 'SQL Query',
      'execute_python': 'Python Code',
      'execute_code': 'Code Execution',
      'file_operations': 'File Operations',
      'web_request': 'Web Request',
      'database_operation': 'Database Operation'
    }
    return toolDisplayNames[toolName] || toolName
  }

  const renderToolInput = () => {
    if (!task) return null

    const toolName = task.input.tool_name || task.input.name || ''
    const displayName = getToolDisplayName(toolName)

    // For SQL queries, show a textarea for easy editing
    if (toolName === 'execute_sql_query' && typeof modifiedInput.sql_query === 'string') {
      return (
        <TextAreaField
          label="SQL Query"
          value={modifiedInput.sql_query || ''}
          onChange={(e) => setModifiedInput({ ...modifiedInput, sql_query: e.target.value })}
          rows={6}
          marginTop="10px"
          descriptiveText="You can modify the SQL query before approving"
        />
      )
    }

    // For Python code, show a textarea for easy editing  
    if (toolName === 'execute_python' && typeof modifiedInput.code === 'string') {
      return (
        <TextAreaField
          label="Python Code"
          value={modifiedInput.code || ''}
          onChange={(e) => setModifiedInput({ ...modifiedInput, code: e.target.value })}
          rows={10}
          marginTop="10px"
          descriptiveText="You can modify the Python code before approving"
        />
      )
    }

    // For other tools, show the full input as JSON for editing
    return (
      <TextAreaField
        label={`${displayName} Input`}
        value={JSON.stringify(modifiedInput, null, 2)}
        onChange={(e) => {
          try {
            const parsed = JSON.parse(e.target.value)
            setModifiedInput(parsed)
          } catch (err) {
            // Keep the string value for continued editing
            console.warn('Invalid JSON while editing:', err)
          }
        }}
        rows={8}
        marginTop="10px"
        descriptiveText="Tool input (JSON format). Modify if needed before approving."
      />
    )
  }

  const getToolDescription = (toolName: string): string => {
    const descriptions: { [key: string]: string } = {
      'execute_sql_query': 'Executes a SQL query against the database',
      'execute_python': 'Runs Python code in a sandboxed environment',
      'execute_code': 'Executes code in a secure environment',
      'file_operations': 'Performs file system operations',
      'web_request': 'Makes HTTP requests to external services',
      'database_operation': 'Performs database operations'
    }
    return descriptions[toolName] || 'Tool execution requiring approval'
  }

  return (
    <View>
      <Heading level={2}>Human Approval Dashboard</Heading>
      
      {error && (
        <Alert variation="error" marginTop="10px" marginBottom="10px">
          {error}
        </Alert>
      )}
      
      {message && (
        <Alert variation="info" marginTop="10px" marginBottom="10px">
          {message}
        </Alert>
      )}

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Activity Configuration</Heading>
        
        <TextField
          label="Activity ARN"
          value={activityArn}
          onChange={(e) => setActivityArn(e.target.value)}
          placeholder="arn:aws:states:region:account:activity:name"
          descriptiveText="Enter the Step Functions activity ARN to poll"
          marginTop="10px"
        />

        <Flex marginTop="10px" gap="10px">
          {!isPolling ? (
            <Button onClick={handleStartPolling} variation="primary">
              Start Polling
            </Button>
          ) : (
            <Button onClick={handleStopPolling} variation="warning">
              Stop Polling
            </Button>
          )}
        </Flex>
      </Card>

      {(isPolling || task) && (
        <Card variation="elevated" marginTop="20px">
          <Heading level={4}>Approval Queue</Heading>
          
          {!task && !error && isPolling && (
            <Flex alignItems="center" marginTop="20px">
              <Loader size="small" />
              <Text marginLeft="10px">Polling for approval tasks...</Text>
            </Flex>
          )}

          {task && (
            <View marginTop="20px">
              {(() => {
                const toolName = task.input.tool_name || task.input.name || 'Unknown'
                const displayName = getToolDisplayName(toolName)
                return <Heading level={5}>{displayName} Approval Required</Heading>
              })()}
              
              <Text marginTop="10px" fontSize="small" color="gray">
                {(() => {
                  const toolName = task.input.tool_name || task.input.name || ''
                  return getToolDescription(toolName)
                })()}
              </Text>
              
              <Text marginTop="10px">
                <strong>Tool:</strong> {task.input.tool_name || task.input.name || 'Unknown'}
              </Text>
              
              {task.input.agent_name && (
                <Text marginTop="5px">
                  <strong>Agent:</strong> {task.input.agent_name}
                </Text>
              )}
              
              {task.input.context?.execution_name && (
                <Text marginTop="5px">
                  <strong>Execution:</strong> {task.input.context.execution_name}
                </Text>
              )}
              
              {task.input.timestamp && (
                <Text marginTop="5px" fontSize="small">
                  <strong>Requested:</strong> {new Date(task.input.timestamp).toLocaleString()}
                </Text>
              )}

              {renderToolInput()}

              <Flex marginTop="20px" gap="10px" justifyContent="flex-end">
                <Button
                  onClick={() => handleApproval(false)}
                  variation="destructive"
                  isLoading={isProcessing}
                  isDisabled={isProcessing}
                >
                  Reject
                </Button>
                <Button
                  onClick={() => handleApproval(true)}
                  variation="primary"
                  isLoading={isProcessing}
                  isDisabled={isProcessing}
                >
                  Approve
                </Button>
              </Flex>
            </View>
          )}
        </Card>
      )}
    </View>
  )
}

export default ApprovalDashboard