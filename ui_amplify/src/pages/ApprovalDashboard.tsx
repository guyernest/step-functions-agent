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
  const [modifiedQuery, setModifiedQuery] = useState('')
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
            
            // Handle the nested structure for SQL query
            const sqlQuery = activityTask.input?.tool_input?.query || 
                           activityTask.input?.tool_input?.sql_query || 
                           activityTask.input?.input?.sql_query || 
                           ''
            setModifiedQuery(sqlQuery)
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
          name: task.input.tool_name || 'execute_sql_query',
          id: task.input.tool_use_id || task.input.id || '',
          input: {
            sql_query: modifiedQuery
          }
        }
        
        await sendTaskSuccess(task.taskToken, output)
        setMessage('Task approved successfully')
      } else {
        await sendTaskFailure(
          task.taskToken,
          'NotApproved',
          'Human rejected the SQL query'
        )
        setMessage('Task rejected successfully')
      }

      setTask(null)
      setModifiedQuery('')
      
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
              <Heading level={5}>SQL Query Approval Required</Heading>
              
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
              
              <TextAreaField
                label="SQL Query"
                value={modifiedQuery}
                onChange={(e) => setModifiedQuery(e.target.value)}
                rows={6}
                marginTop="10px"
                descriptiveText="You can modify the query before approving"
              />

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