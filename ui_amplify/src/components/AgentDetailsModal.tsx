import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  Button,
  TextAreaField,
  Flex,
  Badge,
  Divider,
  View,
  Alert,
  Tabs
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

interface AgentDetailsModalProps {
  agent: any
  isOpen: boolean
  onClose: () => void
  onUpdate?: () => void
}

const AgentDetailsModal: React.FC<AgentDetailsModalProps> = ({ 
  agent, 
  isOpen, 
  onClose,
  onUpdate 
}) => {
  const [systemPrompt, setSystemPrompt] = useState('')
  const [originalSystemPrompt, setOriginalSystemPrompt] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    if (agent?.systemPrompt) {
      setSystemPrompt(agent.systemPrompt)
      setOriginalSystemPrompt(agent.systemPrompt)
    }
  }, [agent])

  const handleSave = async () => {
    if (!agent) return
    
    setIsSaving(true)
    setSaveError(null)
    setSaveSuccess(false)
    
    try {
      const result = await client.mutations.updateAgentSystemPrompt({
        agentName: agent.name,
        version: agent.version || 'v1.0',
        systemPrompt: systemPrompt
      })
      
      const responseData = result.data as any
      if (responseData?.success) {
        setSaveSuccess(true)
        setOriginalSystemPrompt(systemPrompt)
        
        // Call onUpdate to refresh the parent data
        if (onUpdate) {
          onUpdate()
        }
        
        // Hide success message after 3 seconds
        setTimeout(() => setSaveSuccess(false), 3000)
      } else {
        setSaveError(responseData?.error || 'Failed to update system prompt')
      }
    } catch (error) {
      console.error('Error updating system prompt:', error)
      setSaveError('Failed to update system prompt')
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    setSystemPrompt(originalSystemPrompt)
    setSaveError(null)
    setSaveSuccess(false)
  }

  const parseJSON = (jsonString: string) => {
    try {
      return JSON.parse(jsonString)
    } catch {
      return {}
    }
  }

  if (!isOpen || !agent) return null

  const parameters = parseJSON(agent.parameters || '{}')
  const metadata = parseJSON(agent.metadata || '{}')
  const observability = parseJSON(agent.observability || '{}')

  return (
    <View
      position="fixed"
      top="0"
      left="0"
      right="0"
      bottom="0"
      backgroundColor="rgba(0, 0, 0, 0.5)"
      style={{ zIndex: 1000 }}
      onClick={onClose}
    >
      <View
        position="absolute"
        top="50%"
        left="50%"
        style={{
          transform: 'translate(-50%, -50%)',
          maxWidth: '800px',
          width: '90%',
          maxHeight: '90vh',
          overflow: 'auto'
        }}
        onClick={(e: React.MouseEvent) => e.stopPropagation()}
      >
        <Card variation="elevated" backgroundColor="white">
          <Flex direction="column" gap="20px">
            <Flex justifyContent="space-between" alignItems="center">
              <Heading level={3}>{agent.name}</Heading>
              <Badge variation={agent.status === 'active' ? 'success' : 'warning'}>
                {agent.status || 'active'}
              </Badge>
            </Flex>

            {agent.description && (
              <Text>{agent.description}</Text>
            )}

            <Flex gap="10px" wrap="wrap">
              <Badge>Version: {agent.version || '1.0.0'}</Badge>
              {agent.llmProvider && <Badge>LLM: {agent.llmProvider}</Badge>}
              {agent.llmModel && <Badge>Model: {agent.llmModel}</Badge>}
            </Flex>

            <Tabs
              defaultValue="system-prompt"
              items={[
                {
                  label: 'System Prompt',
                  value: 'system-prompt',
                  content: (
                    <View marginTop="20px">
                      {saveSuccess && (
                        <Alert variation="success" marginBottom="10px">
                          System prompt updated successfully!
                        </Alert>
                      )}
                      
                      {saveError && (
                        <Alert variation="error" marginBottom="10px">
                          {saveError}
                        </Alert>
                      )}

                      <TextAreaField
                        label="System Prompt"
                        value={systemPrompt}
                        onChange={(e) => setSystemPrompt(e.target.value)}
                        rows={15}
                        descriptiveText="The system prompt defines the agent's behavior and capabilities"
                      />

                      <Flex gap="10px" marginTop="15px">
                        <Button
                          variation="primary"
                          onClick={handleSave}
                          isLoading={isSaving}
                          isDisabled={systemPrompt === originalSystemPrompt}
                        >
                          Save Changes
                        </Button>
                        <Button
                          onClick={handleReset}
                          isDisabled={systemPrompt === originalSystemPrompt}
                        >
                          Reset
                        </Button>
                      </Flex>
                    </View>
                  )
                },
                {
                  label: 'Configuration',
                  value: 'configuration',
                  content: (
                    <View marginTop="20px">
                      <Heading level={5}>Parameters</Heading>
                      <View backgroundColor="gray.10" padding="10px" borderRadius="5px" marginTop="10px">
                        <Text fontSize="small" fontFamily="monospace">
                          {Object.entries(parameters).map(([key, value]) => (
                            <div key={key}>
                              <strong>{key}:</strong> {JSON.stringify(value)}
                            </div>
                          ))}
                        </Text>
                      </View>

                      <Heading level={5} marginTop="20px">Observability</Heading>
                      <View backgroundColor="gray.10" padding="10px" borderRadius="5px" marginTop="10px">
                        <Text fontSize="small" fontFamily="monospace">
                          {Object.entries(observability).map(([key, value]) => (
                            <div key={key}>
                              <strong>{key}:</strong> {JSON.stringify(value)}
                            </div>
                          ))}
                        </Text>
                      </View>

                      <Heading level={5} marginTop="20px">Metadata</Heading>
                      <View backgroundColor="gray.10" padding="10px" borderRadius="5px" marginTop="10px">
                        <Text fontSize="small" fontFamily="monospace">
                          {Object.entries(metadata).map(([key, value]) => (
                            <div key={key}>
                              <strong>{key}:</strong> {JSON.stringify(value)}
                            </div>
                          ))}
                        </Text>
                      </View>
                    </View>
                  )
                },
                {
                  label: 'Tools',
                  value: 'tools',
                  content: (
                    <View marginTop="20px">
                      {agent.tools && agent.tools.length > 0 ? (
                        <Flex direction="column" gap="10px">
                          {agent.tools.map((tool: string, index: number) => (
                            <Badge key={index} size="large">
                              {tool}
                            </Badge>
                          ))}
                        </Flex>
                      ) : (
                        <Text>No tools configured</Text>
                      )}
                    </View>
                  )
                }
              ]}
            />

            <Divider />

            <Flex justifyContent="flex-end">
              <Button onClick={onClose}>Close</Button>
            </Flex>
          </Flex>
        </Card>
      </View>
    </View>
  )
}

export default AgentDetailsModal