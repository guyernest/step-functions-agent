import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  View,
  Button,
  TextField,
  Alert
} from '@aws-amplify/ui-react'

const Settings: React.FC = () => {
  const [accountId, setAccountId] = useState('')
  const [region, setRegion] = useState('us-west-2')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    // Load saved settings
    const savedAccountId = localStorage.getItem('awsAccountId') || ''
    const savedRegion = localStorage.getItem('awsRegion') || 'us-west-2'
    setAccountId(savedAccountId)
    setRegion(savedRegion)
  }, [])

  const handleSave = () => {
    localStorage.setItem('awsAccountId', accountId)
    localStorage.setItem('awsRegion', region)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <View>
      <Heading level={2}>Settings</Heading>
      
      {saved && (
        <Alert variation="success" marginTop="10px" marginBottom="10px">
          Settings saved successfully!
        </Alert>
      )}

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>AWS Configuration</Heading>
        
        <TextField
          label="AWS Account ID"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          placeholder="123456789012"
          descriptiveText="Your AWS account ID (12 digits)"
          marginTop="10px"
        />

        <TextField
          label="AWS Region"
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          placeholder="us-west-2"
          descriptiveText="The AWS region where your Step Functions are deployed"
          marginTop="10px"
        />

        <Button onClick={handleSave} variation="primary" marginTop="20px">
          Save Settings
        </Button>
      </Card>
      
      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Registry Tables</Heading>
        <Text marginTop="10px">
          The Agent and Tool registry tables are now automatically configured based on the deployment environment:
        </Text>
        <View marginTop="10px">
          <Text fontSize="small" fontFamily="monospace" backgroundColor="gray.10" padding="10px">
            Agent Registry: AgentRegistry-prod
          </Text>
          <Text fontSize="small" fontFamily="monospace" backgroundColor="gray.10" padding="10px" marginTop="5px">
            Tool Registry: ToolRegistry-prod
          </Text>
        </View>
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Activity ARNs</Heading>
        <Text marginTop="10px">
          Based on your settings, here are the expected activity ARNs:
        </Text>
        
        {accountId && (
          <View marginTop="10px">
            <Text fontSize="small" fontFamily="monospace" backgroundColor="gray.10" padding="10px">
              SQL Agent Approval: arn:aws:states:{region}:{accountId}:activity:sql-agent-approval-activity-prod
            </Text>
            <Text fontSize="small" fontFamily="monospace" backgroundColor="gray.10" padding="10px" marginTop="5px">
              Remote Execution: arn:aws:states:{region}:{accountId}:activity:local-automation-remote-activity-prod
            </Text>
          </View>
        )}
      </Card>
    </View>
  )
}

export default Settings