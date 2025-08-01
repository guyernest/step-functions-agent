import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  View,
  Button,
  TextField,
  Alert,
  Flex,
  SelectField
} from '@aws-amplify/ui-react'

const Settings: React.FC = () => {
  const [accountId, setAccountId] = useState('')
  const [region, setRegion] = useState('us-west-2')
  const [agentRegistryTableName, setAgentRegistryTableName] = useState('AgentRegistry-prod')
  const [toolRegistryTableName, setToolRegistryTableName] = useState('tool-registry-prod')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    // Load saved settings
    const savedAccountId = localStorage.getItem('awsAccountId') || ''
    const savedRegion = localStorage.getItem('awsRegion') || 'us-west-2'
    const savedAgentRegistryTableName = localStorage.getItem('agentRegistryTableName') || 'AgentRegistry-prod'
    const savedToolRegistryTableName = localStorage.getItem('toolRegistryTableName') || 'tool-registry-prod'
    setAccountId(savedAccountId)
    setRegion(savedRegion)
    setAgentRegistryTableName(savedAgentRegistryTableName)
    setToolRegistryTableName(savedToolRegistryTableName)
  }, [])

  const handleSave = () => {
    localStorage.setItem('awsAccountId', accountId)
    localStorage.setItem('awsRegion', region)
    localStorage.setItem('agentRegistryTableName', agentRegistryTableName)
    localStorage.setItem('toolRegistryTableName', toolRegistryTableName)
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

        <TextField
          label="Agent Registry Table Name"
          value={agentRegistryTableName}
          onChange={(e) => setAgentRegistryTableName(e.target.value)}
          placeholder="AgentRegistry-prod"
          descriptiveText="The DynamoDB table name for the agent registry"
          marginTop="10px"
        />

        <TextField
          label="Tool Registry Table Name"
          value={toolRegistryTableName}
          onChange={(e) => setToolRegistryTableName(e.target.value)}
          placeholder="tool-registry-prod"
          descriptiveText="The DynamoDB table name for the tool registry"
          marginTop="10px"
        />

        <Button onClick={handleSave} variation="primary" marginTop="20px">
          Save Settings
        </Button>
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Activity ARNs</Heading>
        <Text marginTop="10px">
          Based on your settings, here are the expected activity ARNs:
        </Text>
        
        {accountId && (
          <View marginTop="10px">
            <Text fontSize="small" fontFamily="monospace" backgroundColor="gray.10" padding="10px">
              Human Approval: arn:aws:states:{region}:{accountId}:activity:HumanApprovalActivityForSQLQueryExecution
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