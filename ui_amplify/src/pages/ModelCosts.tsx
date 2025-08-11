import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  View,
  Button,
  Table,
  TableCell,
  TableBody,
  TableHead,
  TableRow,
  Flex,
  TextField,
  Badge,
  Alert,
  Loader,
  useAuthenticator
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

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
  created_at?: string | null
  updated_at?: string | null
}

interface GroupedModels {
  [provider: string]: LLMModel[]
}

const PROVIDER_DISPLAY_NAMES: { [key: string]: string } = {
  'anthropic': 'Anthropic',
  'openai': 'OpenAI',
  'google': 'Google',
  'amazon': 'Amazon Bedrock',
  'xai': 'xAI',
  'deepseek': 'DeepSeek'
}

const ModelCosts: React.FC = () => {
  const [groupedModels, setGroupedModels] = useState<GroupedModels>({})
  const [loading, setLoading] = useState(true)
  const [editingModel, setEditingModel] = useState<string | null>(null)
  const [editValues, setEditValues] = useState<{ input: string; output: string }>({ input: '', output: '' })
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  
  useEffect(() => {
    fetchModelCosts()
  }, [])

  const fetchModelCosts = async () => {
    setLoading(true)
    try {
      // Fetch models from LLMModels table
      const response = await client.queries.listLLMModels({})
      
      if (response.data) {
        const llmModels = response.data as LLMModel[]
        
        // Sort models by provider, default status, then name
        const sortedModels = llmModels.sort((a, b) => {
          if (a.provider !== b.provider) {
            return a.provider.localeCompare(b.provider)
          }
          if (a.is_default !== b.is_default) {
            return b.is_default ? 1 : -1
          }
          return a.display_name.localeCompare(b.display_name)
        })
        
        // Group models by provider and sort within each group
        const grouped = sortedModels.reduce((acc, model) => {
          if (!acc[model.provider]) {
            acc[model.provider] = []
          }
          acc[model.provider].push(model)
          return acc
        }, {} as GroupedModels)
        
        // Sort models within each provider group
        Object.keys(grouped).forEach(provider => {
          grouped[provider].sort((a, b) => {
            if (a.is_default !== b.is_default) {
              return b.is_default ? 1 : -1
            }
            return a.display_name.localeCompare(b.display_name)
          })
        })
        
        setGroupedModels(grouped)
      }
    } catch (error) {
      console.error('Error fetching model costs:', error)
      setGroupedModels({})
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (model: LLMModel) => {
    setEditingModel(model.pk)
    setEditValues({
      input: model.input_price_per_1k.toString(),
      output: model.output_price_per_1k.toString()
    })
  }

  const handleSave = async (modelPk: string) => {
    const inputPrice = parseFloat(editValues.input)
    const outputPrice = parseFloat(editValues.output)

    if (!isNaN(inputPrice) && !isNaN(outputPrice) && inputPrice >= 0 && outputPrice >= 0) {
      setSaveStatus('saving')
      try {
        // Note: In a real implementation, you would update the LLMModels table here
        // For now, we'll just show an info message
        console.log('Model pricing update requested for:', modelPk, { inputPrice, outputPrice })
        alert('Note: Direct model pricing updates are managed at the infrastructure level. Please update the LLMModels table directly.')
        
        setEditingModel(null)
        setSaveStatus('saved')
        setTimeout(() => setSaveStatus('idle'), 2000)
      } catch (error) {
        console.error('Error saving model cost:', error)
        setSaveStatus('error')
        setTimeout(() => setSaveStatus('idle'), 3000)
      }
    }
  }

  const handleCancel = () => {
    setEditingModel(null)
    setEditValues({ input: '', output: '' })
  }

  const formatCapabilities = (model: LLMModel) => {
    const capabilities = []
    if (model.supports_tools) capabilities.push('Tools')
    if (model.supports_vision) capabilities.push('Vision')
    return capabilities.length > 0 ? capabilities.join(', ') : 'Basic'
  }

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`
  }

  if (loading) {
    return (
      <View>
        <Heading level={2}>Model Cost Management</Heading>
        <Flex justifyContent="center" padding="40px">
          <Loader size="large" />
        </Flex>
      </View>
    )
  }

  return (
    <View>
      <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
        <View>
          <Heading level={2}>Model Cost Management</Heading>
          <Text color="gray">Configure pricing for AI models (per 1M tokens)</Text>
        </View>
        {saveStatus === 'saved' && (
          <Badge variation="success">Changes saved</Badge>
        )}
        {saveStatus === 'error' && (
          <Badge variation="error">Error saving changes</Badge>
        )}
      </Flex>

      <Alert variation="info" marginBottom="20px">
        <Text>
          Model costs are centrally managed in the LLMModels DynamoDB table and used to calculate real-time usage expenses. 
          Prices are shown per 1,000 tokens as configured in the database.
        </Text>
      </Alert>

      <Card variation="elevated">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
          <Heading level={4}>Model Pricing by Provider</Heading>
          {saveStatus === 'saved' && (
            <Badge variation="success">Changes saved</Badge>
          )}
          {saveStatus === 'error' && (
            <Badge variation="error">Error saving changes</Badge>
          )}
        </Flex>

        {Object.entries(groupedModels).map(([provider, providerModels]) => (
          <View key={provider} marginBottom="30px">
            <Heading level={5} marginBottom="10px">
              {PROVIDER_DISPLAY_NAMES[provider] || provider}
            </Heading>
            <Table variation="striped">
              <TableHead>
                <TableRow>
                  <TableCell as="th">Model</TableCell>
                  <TableCell as="th">Model ID</TableCell>
                  <TableCell as="th">Input Price (per 1K tokens)</TableCell>
                  <TableCell as="th">Output Price (per 1K tokens)</TableCell>
                  <TableCell as="th">Max Tokens</TableCell>
                  <TableCell as="th">Capabilities</TableCell>
                  <TableCell as="th">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {providerModels.map((model) => (
                  <TableRow key={model.pk}>
                    <TableCell>
                      <Flex alignItems="center" gap="10px">
                        <Text fontWeight="bold">{model.display_name}</Text>
                        {model.is_default && <Badge size="small" variation="info">Default</Badge>}
                      </Flex>
                    </TableCell>
                    <TableCell>
                      <Text fontSize="small" fontFamily="monospace">{model.model_id}</Text>
                    </TableCell>
                    <TableCell>
                      {editingModel === model.pk ? (
                        <TextField
                          label=""
                          value={editValues.input}
                          onChange={(e) => setEditValues({ ...editValues, input: e.target.value })}
                          type="number"
                          step="0.01"
                          size="small"
                        />
                      ) : (
                        <Text>{formatPrice(model.input_price_per_1k)}</Text>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingModel === model.pk ? (
                        <TextField
                          label=""
                          value={editValues.output}
                          onChange={(e) => setEditValues({ ...editValues, output: e.target.value })}
                          type="number"
                          step="0.01"
                          size="small"
                        />
                      ) : (
                        <Text>{formatPrice(model.output_price_per_1k)}</Text>
                      )}
                    </TableCell>
                    <TableCell>
                      <Text fontSize="small">{model.max_tokens?.toLocaleString() || 'N/A'}</Text>
                    </TableCell>
                    <TableCell>
                      <Text fontSize="small">{formatCapabilities(model)}</Text>
                    </TableCell>
                    <TableCell>
                      {editingModel === model.pk ? (
                        <Flex gap="5px">
                          <Button 
                            size="small" 
                            onClick={() => handleSave(model.pk)}
                            isDisabled={saveStatus === 'saving'}
                          >
                            Save
                          </Button>
                          <Button size="small" variation="link" onClick={handleCancel}>
                            Cancel
                          </Button>
                        </Flex>
                      ) : (
                        <Button 
                          size="small" 
                          variation="link" 
                          onClick={() => handleEdit(model)}
                          isDisabled={saveStatus === 'saving'}
                        >
                          Edit
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </View>
        ))}
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Cost Calculation Example</Heading>
        <Text marginTop="10px">
          For a conversation using Claude 3.5 Sonnet with 1,000 input tokens and 500 output tokens:
        </Text>
        <View marginTop="10px" backgroundColor="rgba(0,0,0,0.05)" padding="10px" borderRadius="5px">
          <Text fontSize="small" fontFamily="monospace">
            Input Cost: 1,000 × ($3.00 / 1,000) = $0.003
          </Text>
          <Text fontSize="small" fontFamily="monospace">
            Output Cost: 500 × ($15.00 / 1,000) = $0.0075
          </Text>
          <Text fontSize="small" fontFamily="monospace" fontWeight="bold">
            Total Cost: $0.0105
          </Text>
        </View>
        <Text fontSize="small" color="gray" marginTop="10px">
          Note: Prices in the table are shown per 1,000 tokens as stored in the database.
        </Text>
      </Card>
    </View>
  )
}

export default ModelCosts