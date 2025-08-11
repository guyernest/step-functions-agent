import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  Button,
  TextAreaField,
  SelectField,
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

interface LLMModel {
  pk: string
  provider: string
  model_id: string
  display_name: string
  input_price_per_1k: number
  output_price_per_1k: number
  max_tokens?: number | null
  supports_tools?: boolean | null
  supports_vision?: boolean | null
  is_active?: string | null
  is_default?: boolean | null
}

interface AgentDetailsModalProps {
  agent: any
  isOpen: boolean
  onClose: () => void
  onUpdate?: () => void
}

// Map agent registry provider names to LLMModels provider names
// TODO: Long-term fix - update agent registry to use consistent provider names
// Currently agent registry uses model family names (claude, gemini) while 
// LLMModels table uses company names (anthropic, google)
const PROVIDER_MAPPING: { [key: string]: string } = {
  'claude': 'anthropic',
  'gemini': 'google', 
  'gpt': 'openai',
  'openai': 'openai',
  'amazon': 'amazon',
  'xai': 'xai',
  'deepseek': 'deepseek'
}

const AgentDetailsModal: React.FC<AgentDetailsModalProps> = ({ 
  agent, 
  isOpen, 
  onClose,
  onUpdate 
}) => {
  const [systemPrompt, setSystemPrompt] = useState('')
  const [originalSystemPrompt, setOriginalSystemPrompt] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [originalModel, setOriginalModel] = useState('')
  const [availableModels, setAvailableModels] = useState<LLMModel[]>([])
  const [loadingModels, setLoadingModels] = useState(false)
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
    
    if (agent?.llmModel) {
      setSelectedModel(agent.llmModel)
      setOriginalModel(agent.llmModel)
    }
    
    // Fetch tool details and models when agent changes
    if (agent && isOpen) {
      fetchToolDetails()
      if (agent.llmProvider) {
        // Map the agent's provider name to the LLMModels provider name
        const mappedProvider = PROVIDER_MAPPING[agent.llmProvider] || agent.llmProvider
        fetchAvailableModels(mappedProvider)
      }
    }
  }, [agent, isOpen])

  const fetchAvailableModels = async (provider: string) => {
    setLoadingModels(true)
    try {
      const response = await client.queries.listLLMModelsByProvider({ provider })
      
      if (response.data) {
        const models = response.data as LLMModel[]
        // Sort models client-side: default first, then by name
        const sortedModels = models.sort((a, b) => {
          if (a.is_default !== b.is_default) {
            return b.is_default ? 1 : -1
          }
          return a.display_name.localeCompare(b.display_name)
        })
        setAvailableModels(sortedModels)
      }
    } catch (error) {
      console.error('Error fetching available models:', error)
      setAvailableModels([])
    } finally {
      setLoadingModels(false)
    }
  }

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
      let hasChanges = false
      let allSuccess = true
      
      // Update system prompt if changed
      if (systemPrompt !== originalSystemPrompt) {
        const result = await client.mutations.updateAgentSystemPrompt({
          agentName: agent.name,
          version: agent.version || 'v1.0',
          systemPrompt: systemPrompt
        })
        
        // Parse the JSON string response
        const responseData = typeof result.data === 'string' 
          ? JSON.parse(result.data as string)
          : result.data as any
          
        if (responseData?.success) {
          setOriginalSystemPrompt(systemPrompt)
          hasChanges = true
        } else {
          allSuccess = false
          setSaveError(responseData?.error || 'Failed to update system prompt')
        }
      }
      
      // Update model if changed
      if (selectedModel !== originalModel && selectedModel) {
        const result = await client.mutations.updateAgentModel({
          agentName: agent.name,
          version: agent.version || 'v1.0',
          modelId: selectedModel
        })
        
        // Parse the JSON string response
        const responseData = typeof result.data === 'string' 
          ? JSON.parse(result.data as string)
          : result.data as any
          
        if (responseData?.success) {
          setOriginalModel(selectedModel)
          hasChanges = true
        } else {
          allSuccess = false
          setSaveError(responseData?.error || 'Failed to update model')
        }
      }
      
      if (hasChanges && allSuccess) {
        setSaveSuccess(true)
        
        // Call onUpdate to refresh the parent data
        if (onUpdate) {
          onUpdate()
        }
        
        // Hide success message after 3 seconds
        setTimeout(() => setSaveSuccess(false), 3000)
      }
    } catch (error) {
      console.error('Error updating agent:', error)
      setSaveError('Failed to update agent configuration')
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    setSystemPrompt(originalSystemPrompt)
    setSelectedModel(originalModel)
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
                          isDisabled={systemPrompt === originalSystemPrompt && selectedModel === originalModel}
                        >
                          Save Changes
                        </Button>
                        <Button
                          onClick={handleReset}
                          isDisabled={systemPrompt === originalSystemPrompt && selectedModel === originalModel}
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
                      {saveSuccess && (
                        <Alert variation="success" marginBottom="10px">
                          Configuration updated successfully!
                        </Alert>
                      )}
                      
                      {saveError && (
                        <Alert variation="error" marginBottom="10px">
                          {saveError}
                        </Alert>
                      )}
                      
                      <Heading level={5}>Model Configuration</Heading>
                      <View marginTop="10px" marginBottom="20px">
                        <Flex direction="column" gap="10px">
                          <Text fontSize="small">
                            <strong>Provider:</strong> {agent.llmProvider || 'Not configured'}
                          </Text>
                          {loadingModels ? (
                            <Loader size="small" />
                          ) : availableModels.length > 0 ? (
                            <SelectField
                              label="Model"
                              value={selectedModel}
                              onChange={(e) => setSelectedModel(e.target.value)}
                              descriptiveText="Select the LLM model for this agent"
                            >
                              {availableModels.map((model) => (
                                <option key={model.pk} value={model.model_id}>
                                  {model.display_name} 
                                  {model.is_default && ' (Default)'}
                                  {model.supports_tools && model.supports_vision && ' - Tools & Vision'}
                                  {model.supports_tools && !model.supports_vision && ' - Tools'}
                                  {!model.supports_tools && model.supports_vision && ' - Vision'}
                                </option>
                              ))}
                            </SelectField>
                          ) : (
                            <Text fontSize="small" color="gray">
                              No models available for provider: {agent.llmProvider}
                            </Text>
                          )}
                        </Flex>
                        
                        {(selectedModel !== originalModel) && (
                          <Flex gap="10px" marginTop="15px">
                            <Button
                              variation="primary"
                              onClick={handleSave}
                              isLoading={isSaving}
                              isDisabled={selectedModel === originalModel}
                            >
                              Save Model Change
                            </Button>
                            <Button
                              onClick={handleReset}
                              isDisabled={selectedModel === originalModel}
                            >
                              Reset
                            </Button>
                          </Flex>
                        )}
                      </View>

                      <Divider />

                      <Heading level={5} marginTop="20px">Parameters</Heading>
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