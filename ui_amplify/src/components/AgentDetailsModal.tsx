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
  Tabs,
  Icon,
  Loader
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

interface Tool {
  id: string
  name: string
  description: string
  version: string
  type: string
  createdAt: string
  language?: string
  lambda_function_name?: string
  lambda_arn?: string
}

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
  const [tools, setTools] = useState<Tool[]>([])
  const [loadingTools, setLoadingTools] = useState(false)

  useEffect(() => {
    if (agent?.systemPrompt) {
      setSystemPrompt(agent.systemPrompt)
      setOriginalSystemPrompt(agent.systemPrompt)
    }
    
    // Fetch tool details when agent changes
    if (agent && isOpen) {
      fetchToolDetails()
    }
  }, [agent, isOpen])

  const fetchToolDetails = async () => {
    if (!agent?.tools || agent.tools.length === 0) return
    
    setLoadingTools(true)
    try {
      const response = await client.queries.listToolsFromRegistry({})
      
      if (response.data) {
        const allTools = response.data
          .filter(tool => tool !== null && tool !== undefined)
          .map(tool => ({
            id: tool.id,
            name: tool.name,
            description: tool.description || '',
            version: tool.version || '1.0.0',
            type: tool.type || 'tool',
            createdAt: tool.createdAt || new Date().toISOString(),
            language: tool.language || 'python',
            lambda_function_name: tool.lambda_function_name || undefined,
            lambda_arn: tool.lambda_arn || undefined
          }))
        
        // Filter tools that belong to this agent
        const agentTools = allTools.filter(tool => 
          agent.tools.includes(tool.name)
        )
        
        setTools(agentTools)
      }
    } catch (error) {
      console.error('Error fetching tool details:', error)
    } finally {
      setLoadingTools(false)
    }
  }

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

  // Helper function to get language badge color
  const getLanguageColor = (language?: string): string => {
    const lang = language?.toLowerCase() || 'python'
    const colors: { [key: string]: string } = {
      python: '#3776AB',
      typescript: '#007ACC',
      go: '#00ADD8',
      rust: '#CE412B',
      java: '#F89820'
    }
    return colors[lang] || '#666666'
  }

  // Helper function to format language display name
  const formatLanguageName = (language?: string): string => {
    const lang = language?.toLowerCase() || 'python'
    const names: { [key: string]: string } = {
      python: 'Python',
      typescript: 'TypeScript',
      go: 'Go',
      rust: 'Rust',
      java: 'Java'
    }
    return names[lang] || lang.charAt(0).toUpperCase() + lang.slice(1)
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
                        <Flex direction="column" gap="5px">
                          {Object.entries(parameters).map(([key, value]) => (
                            <Text key={key} fontSize="small" fontFamily="monospace">
                              <strong>{key}:</strong> {JSON.stringify(value)}
                            </Text>
                          ))}
                        </Flex>
                      </View>

                      <Heading level={5} marginTop="20px">Observability</Heading>
                      <View backgroundColor="gray.10" padding="10px" borderRadius="5px" marginTop="10px">
                        <Flex direction="column" gap="5px">
                          {Object.entries(observability).map(([key, value]) => (
                            <Text key={key} fontSize="small" fontFamily="monospace">
                              <strong>{key}:</strong> {JSON.stringify(value)}
                            </Text>
                          ))}
                        </Flex>
                      </View>

                      <Heading level={5} marginTop="20px">Metadata</Heading>
                      <View backgroundColor="gray.10" padding="10px" borderRadius="5px" marginTop="10px">
                        <Flex direction="column" gap="5px">
                          {Object.entries(metadata).map(([key, value]) => (
                            <Text key={key} fontSize="small" fontFamily="monospace">
                              <strong>{key}:</strong> {JSON.stringify(value)}
                            </Text>
                          ))}
                        </Flex>
                      </View>
                    </View>
                  )
                },
                {
                  label: 'Tools',
                  value: 'tools',
                  content: (
                    <View marginTop="20px">
                      {loadingTools ? (
                        <Loader size="large" />
                      ) : agent.tools && agent.tools.length > 0 ? (
                        <Flex direction="column" gap="15px">
                          {agent.tools.map((toolName: string, index: number) => {
                            const toolDetail = tools.find(t => t.name === toolName)
                            
                            return (
                              <Card key={index} variation="outlined">
                                <Flex direction="column" gap="10px">
                                  <Flex alignItems="center" gap="10px">
                                    <Icon
                                      ariaLabel="Tool"
                                      viewBox={{ width: 16, height: 16 }}
                                      paths={[
                                        {
                                          d: "M22.7 19L13.6 9.9C14.5 7.6 14 4.9 12.1 3C10.1 1 7.1 0.6 4.7 1.7L9 6L6 9L1.6 4.7C0.4 7.1 0.9 10.1 2.9 12.1C4.8 14 7.5 14.5 9.8 13.6L18.9 22.7C19.3 23.1 19.9 23.1 20.3 22.7L22.6 20.4C23.1 20 23.1 19.4 22.7 19Z",
                                          fill: "currentColor"
                                        }
                                      ]}
                                    />
                                    <Text fontWeight="bold" fontSize="medium">{toolName}</Text>
                                    {toolDetail && (
                                      <Flex gap="5px">
                                        <Badge 
                                          size="small" 
                                          backgroundColor={getLanguageColor(toolDetail.language)}
                                          color="white"
                                        >
                                          {formatLanguageName(toolDetail.language)}
                                        </Badge>
                                        <Badge size="small" variation="info">
                                          {toolDetail.version}
                                        </Badge>
                                      </Flex>
                                    )}
                                  </Flex>
                                  
                                  {toolDetail && (
                                    <>
                                      {toolDetail.description && (
                                        <Text fontSize="small" color="gray">
                                          {toolDetail.description}
                                        </Text>
                                      )}
                                      
                                      {toolDetail.lambda_function_name && (
                                        <View backgroundColor="gray.10" padding="8px" borderRadius="4px">
                                          <Text fontSize="small" fontFamily="monospace">
                                            <strong>Lambda:</strong> {toolDetail.lambda_function_name}
                                          </Text>
                                        </View>
                                      )}
                                    </>
                                  )}
                                </Flex>
                              </Card>
                            )
                          })}
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