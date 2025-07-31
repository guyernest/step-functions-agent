import { useState, useCallback } from 'react'
import { SFNClient, GetActivityTaskCommand, SendTaskSuccessCommand, SendTaskFailureCommand } from '@aws-sdk/client-sfn'
import { fetchAuthSession } from 'aws-amplify/auth'

export interface ActivityTask {
  taskToken: string
  input: any
}

export const useStepFunctions = () => {
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getClient = async () => {
    const session = await fetchAuthSession()
    const region = localStorage.getItem('awsRegion') || 'us-west-2'
    
    if (!session.credentials) {
      throw new Error('No AWS credentials available')
    }

    return new SFNClient({
      region,
      credentials: session.credentials
    })
  }

  const pollActivityTask = useCallback(async (activityArn: string): Promise<ActivityTask | null> => {
    try {
      const client = await getClient()
      
      const command = new GetActivityTaskCommand({
        activityArn,
        workerName: 'amplify-ui-worker'
      })

      const response = await client.send(command)
      
      if (response.taskToken) {
        let parsedInput = {}
        if (response.input) {
          try {
            parsedInput = JSON.parse(response.input)
          } catch (e) {
            console.error('Error parsing task input:', e)
            parsedInput = { raw: response.input }
          }
        }

        return {
          taskToken: response.taskToken,
          input: parsedInput
        }
      }

      return null
    } catch (err) {
      console.error('Error polling activity:', err)
      setError(err instanceof Error ? err.message : 'Failed to poll activity')
      throw err
    }
  }, [])

  const sendTaskSuccess = useCallback(async (
    taskToken: string,
    output: Record<string, any>
  ): Promise<void> => {
    try {
      const client = await getClient()
      
      const command = new SendTaskSuccessCommand({
        taskToken,
        output: JSON.stringify(output)
      })

      await client.send(command)
    } catch (err) {
      console.error('Error sending task success:', err)
      setError(err instanceof Error ? err.message : 'Failed to send task success')
      throw err
    }
  }, [])

  const sendTaskFailure = useCallback(async (
    taskToken: string,
    error: string,
    cause: string
  ): Promise<void> => {
    try {
      const client = await getClient()
      
      const command = new SendTaskFailureCommand({
        taskToken,
        error,
        cause
      })

      await client.send(command)
    } catch (err) {
      console.error('Error sending task failure:', err)
      setError(err instanceof Error ? err.message : 'Failed to send task failure')
      throw err
    }
  }, [])

  return {
    pollActivityTask,
    sendTaskSuccess,
    sendTaskFailure,
    isPolling,
    setIsPolling,
    error,
    setError
  }
}