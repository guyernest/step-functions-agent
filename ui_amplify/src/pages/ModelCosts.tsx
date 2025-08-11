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
  SelectField,
  CheckboxField,
  Grid,
  PasswordField
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

interface NewModelForm {
  provider: string
  model_id: string
  display_name: string
  input_price_per_1k: string
  output_price_per_1k: string
  max_tokens: string
  supports_tools: boolean
  supports_vision: boolean
  is_default: boolean
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
  const [editValues, setEditValues] = useState<Partial<LLMModel>>({})
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [showAddModel, setShowAddModel] = useState(false)
  const [showApiKeyUpdate, setShowApiKeyUpdate] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [apiKey, setApiKey] = useState<string>('')
  const [newModel, setNewModel] = useState<NewModelForm>({
    provider: '',
    model_id: '',
    display_name: '',
    input_price_per_1k: '',
    output_price_per_1k: '',
    max_tokens: '',
    supports_tools: false,
    supports_vision: false,
    is_default: false
  })
  
  useEffect(() => {
    fetchModelCosts()
  }, [])

  const fetchModelCosts = async () => {
    setLoading(true)
    try {
      const response = await client.queries.listLLMModels({})
      
      if (response.data) {
        const llmModels = response.data as LLMModel[]
        
        const sortedModels = llmModels.sort((a, b) => {
          if (a.provider !== b.provider) {
            return a.provider.localeCompare(b.provider)
          }
          if (a.is_default !== b.is_default) {
            return b.is_default ? 1 : -1
          }
          return a.display_name.localeCompare(b.display_name)
        })
        
        const grouped = sortedModels.reduce((acc, model) => {
          if (!acc[model.provider]) {
            acc[model.provider] = []
          }
          acc[model.provider].push(model)
          return acc
        }, {} as GroupedModels)
        
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
      display_name: model.display_name,
      input_price_per_1k: model.input_price_per_1k,
      output_price_per_1k: model.output_price_per_1k,
      max_tokens: model.max_tokens,
      supports_tools: model.supports_tools,
      supports_vision: model.supports_vision,
      is_active: model.is_active,
      is_default: model.is_default
    })
  }

  const handleSave = async (modelPk: string) => {
    setSaveStatus('saving')
    try {
      const updateData: any = { pk: modelPk }
      
      if (editValues.display_name !== undefined) updateData.display_name = editValues.display_name
      if (editValues.input_price_per_1k !== undefined) updateData.input_price_per_1k = Number(editValues.input_price_per_1k)
      if (editValues.output_price_per_1k !== undefined) updateData.output_price_per_1k = Number(editValues.output_price_per_1k)
      if (editValues.max_tokens !== undefined) updateData.max_tokens = editValues.max_tokens ? Number(editValues.max_tokens) : null
      if (editValues.supports_tools !== undefined) updateData.supports_tools = editValues.supports_tools
      if (editValues.supports_vision !== undefined) updateData.supports_vision = editValues.supports_vision
      if (editValues.is_active !== undefined) updateData.is_active = editValues.is_active
      if (editValues.is_default !== undefined) updateData.is_default = editValues.is_default
      
      const response = await client.mutations.updateLLMModel(updateData)
      
      if (response.data && (response.data as any).success) {
        setEditingModel(null)
        setSaveStatus('saved')
        await fetchModelCosts()
        setTimeout(() => setSaveStatus('idle'), 2000)
      } else {
        throw new Error('Update failed')
      }
    } catch (error) {
      console.error('Error saving model:', error)
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3000)
    }
  }

  const handleDelete = async (modelPk: string) => {
    if (!confirm('Are you sure you want to delete this model?')) return
    
    try {
      const response = await client.mutations.deleteLLMModel({ pk: modelPk })
      
      if (response.data && (response.data as any).success) {
        await fetchModelCosts()
      }
    } catch (error) {
      console.error('Error deleting model:', error)
      alert('Failed to delete model')
    }
  }

  const handleAddModel = async () => {
    if (!newModel.provider || !newModel.model_id || !newModel.display_name || 
        !newModel.input_price_per_1k || !newModel.output_price_per_1k) {
      alert('Please fill in all required fields')
      return
    }
    
    try {
      const response = await client.mutations.addLLMModel({
        provider: newModel.provider,
        model_id: newModel.model_id,
        display_name: newModel.display_name,
        input_price_per_1k: Number(newModel.input_price_per_1k),
        output_price_per_1k: Number(newModel.output_price_per_1k),
        max_tokens: newModel.max_tokens ? Number(newModel.max_tokens) : null,
        supports_tools: newModel.supports_tools,
        supports_vision: newModel.supports_vision,
        is_default: newModel.is_default
      })
      
      if (response.data && (response.data as any).success) {
        setShowAddModel(false)
        setNewModel({
          provider: '',
          model_id: '',
          display_name: '',
          input_price_per_1k: '',
          output_price_per_1k: '',
          max_tokens: '',
          supports_tools: false,
          supports_vision: false,
          is_default: false
        })
        await fetchModelCosts()
      }
    } catch (error) {
      console.error('Error adding model:', error)
      alert('Failed to add model')
    }
  }

  const handleUpdateApiKey = async () => {
    if (!selectedProvider || !apiKey) {
      alert('Please select a provider and enter an API key')
      return
    }
    
    try {
      const response = await client.mutations.updateProviderAPIKey({
        provider: selectedProvider,
        apiKey: apiKey
      })
      
      if (response.data && (response.data as any).success) {
        alert(`API key for ${PROVIDER_DISPLAY_NAMES[selectedProvider] || selectedProvider} updated successfully`)
        setShowApiKeyUpdate(false)
        setSelectedProvider('')
        setApiKey('')
      }
    } catch (error) {
      console.error('Error updating API key:', error)
      alert('Failed to update API key')
    }
  }

  const handleCancel = () => {
    setEditingModel(null)
    setEditValues({})
  }

  const formatCapabilities = (model: LLMModel) => {
    const capabilities = []
    if (model.supports_tools) capabilities.push('Tools')
    if (model.supports_vision) capabilities.push('Vision')
    return capabilities.length > 0 ? capabilities.join(', ') : 'Basic'
  }

  const formatPrice = (price: number) => {
    return `$${price.toFixed(3)}`
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
          <Text color="gray">Configure pricing and capabilities for AI models</Text>
        </View>
        <Flex gap="10px">
          <Button onClick={() => setShowAddModel(true)} variation="primary">
            Add Model
          </Button>
          <Button onClick={() => setShowApiKeyUpdate(true)}>
            Update API Keys
          </Button>
        </Flex>
      </Flex>

      {saveStatus === 'saved' && (
        <Alert variation="success" marginBottom="20px">
          Changes saved successfully
        </Alert>
      )}
      {saveStatus === 'error' && (
        <Alert variation="error" marginBottom="20px">
          Error saving changes
        </Alert>
      )}

      {showAddModel && (
        <Card variation="elevated" marginBottom="20px">
          <Heading level={4} marginBottom="20px">Add New Model</Heading>
          <Grid templateColumns="1fr 1fr" gap="20px">
            <SelectField
              label="Provider"
              value={newModel.provider}
              onChange={(e) => setNewModel({ ...newModel, provider: e.target.value })}
            >
              <option value="">Select provider</option>
              {Object.entries(PROVIDER_DISPLAY_NAMES).map(([key, name]) => (
                <option key={key} value={key}>{name}</option>
              ))}
            </SelectField>
            <TextField
              label="Model ID"
              value={newModel.model_id}
              onChange={(e) => setNewModel({ ...newModel, model_id: e.target.value })}
              placeholder="e.g., gpt-4o-mini"
            />
            <TextField
              label="Display Name"
              value={newModel.display_name}
              onChange={(e) => setNewModel({ ...newModel, display_name: e.target.value })}
              placeholder="e.g., GPT-4o Mini"
            />
            <TextField
              label="Max Tokens"
              type="number"
              value={newModel.max_tokens}
              onChange={(e) => setNewModel({ ...newModel, max_tokens: e.target.value })}
              placeholder="e.g., 128000"
            />
            <TextField
              label="Input Price (per 1K tokens)"
              type="number"
              step="0.001"
              value={newModel.input_price_per_1k}
              onChange={(e) => setNewModel({ ...newModel, input_price_per_1k: e.target.value })}
              placeholder="e.g., 0.15"
            />
            <TextField
              label="Output Price (per 1K tokens)"
              type="number"
              step="0.001"
              value={newModel.output_price_per_1k}
              onChange={(e) => setNewModel({ ...newModel, output_price_per_1k: e.target.value })}
              placeholder="e.g., 0.60"
            />
          </Grid>
          <Flex gap="20px" marginTop="20px">
            <CheckboxField
              label="Supports Tools"
              name="supports_tools"
              checked={newModel.supports_tools}
              onChange={(e) => setNewModel({ ...newModel, supports_tools: e.target.checked })}
            />
            <CheckboxField
              label="Supports Vision"
              name="supports_vision"
              checked={newModel.supports_vision}
              onChange={(e) => setNewModel({ ...newModel, supports_vision: e.target.checked })}
            />
            <CheckboxField
              label="Set as Default"
              name="is_default"
              checked={newModel.is_default}
              onChange={(e) => setNewModel({ ...newModel, is_default: e.target.checked })}
            />
          </Flex>
          <Flex gap="10px" marginTop="20px">
            <Button onClick={handleAddModel} variation="primary">Add Model</Button>
            <Button onClick={() => setShowAddModel(false)} variation="link">Cancel</Button>
          </Flex>
        </Card>
      )}

      {showApiKeyUpdate && (
        <Card variation="elevated" marginBottom="20px">
          <Heading level={4} marginBottom="20px">Update Provider API Key</Heading>
          <Grid templateColumns="1fr 2fr" gap="20px">
            <SelectField
              label="Provider"
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
            >
              <option value="">Select provider</option>
              {Object.entries(PROVIDER_DISPLAY_NAMES).map(([key, name]) => (
                <option key={key} value={key}>{name}</option>
              ))}
            </SelectField>
            <PasswordField
              label="API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter new API key"
            />
          </Grid>
          <Alert variation="info" marginTop="10px">
            API keys are securely stored in AWS Secrets Manager at /ai-agent/llm-secrets/prod/{'{provider}'}
          </Alert>
          <Flex gap="10px" marginTop="20px">
            <Button onClick={handleUpdateApiKey} variation="primary">Update API Key</Button>
            <Button onClick={() => { setShowApiKeyUpdate(false); setSelectedProvider(''); setApiKey('') }} variation="link">
              Cancel
            </Button>
          </Flex>
        </Card>
      )}

      <Card variation="elevated">
        <Heading level={4} marginBottom="20px">Model Pricing by Provider</Heading>

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
                  <TableCell as="th">Input Price</TableCell>
                  <TableCell as="th">Output Price</TableCell>
                  <TableCell as="th">Max Tokens</TableCell>
                  <TableCell as="th">Capabilities</TableCell>
                  <TableCell as="th">Status</TableCell>
                  <TableCell as="th">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {providerModels.map((model) => (
                  <TableRow key={model.pk}>
                    <TableCell>
                      {editingModel === model.pk ? (
                        <TextField
                          label=""
                          value={editValues.display_name || ''}
                          onChange={(e) => setEditValues({ ...editValues, display_name: e.target.value })}
                          size="small"
                        />
                      ) : (
                        <Flex alignItems="center" gap="10px">
                          <Text fontWeight="bold">{model.display_name}</Text>
                          {model.is_default && <Badge size="small" variation="info">Default</Badge>}
                        </Flex>
                      )}
                    </TableCell>
                    <TableCell>
                      <Text fontSize="small" fontFamily="monospace">{model.model_id}</Text>
                    </TableCell>
                    <TableCell>
                      {editingModel === model.pk ? (
                        <TextField
                          label=""
                          value={editValues.input_price_per_1k?.toString() || ''}
                          onChange={(e) => setEditValues({ ...editValues, input_price_per_1k: Number(e.target.value) })}
                          type="number"
                          step="0.001"
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
                          value={editValues.output_price_per_1k?.toString() || ''}
                          onChange={(e) => setEditValues({ ...editValues, output_price_per_1k: Number(e.target.value) })}
                          type="number"
                          step="0.001"
                          size="small"
                        />
                      ) : (
                        <Text>{formatPrice(model.output_price_per_1k)}</Text>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingModel === model.pk ? (
                        <TextField
                          label=""
                          value={editValues.max_tokens?.toString() || ''}
                          onChange={(e) => setEditValues({ ...editValues, max_tokens: e.target.value ? Number(e.target.value) : null })}
                          type="number"
                          size="small"
                        />
                      ) : (
                        <Text fontSize="small">{model.max_tokens?.toLocaleString() || 'N/A'}</Text>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingModel === model.pk ? (
                        <Flex direction="column" gap="5px">
                          <CheckboxField
                            label="Tools"
                            name={`tools_${model.pk}`}
                            checked={editValues.supports_tools || false}
                            onChange={(e) => setEditValues({ ...editValues, supports_tools: e.target.checked })}
                            size="small"
                          />
                          <CheckboxField
                            label="Vision"
                            name={`vision_${model.pk}`}
                            checked={editValues.supports_vision || false}
                            onChange={(e) => setEditValues({ ...editValues, supports_vision: e.target.checked })}
                            size="small"
                          />
                        </Flex>
                      ) : (
                        <Text fontSize="small">{formatCapabilities(model)}</Text>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingModel === model.pk ? (
                        <Flex direction="column" gap="5px">
                          <CheckboxField
                            label="Active"
                            name={`active_${model.pk}`}
                            checked={editValues.is_active === 'true'}
                            onChange={(e) => setEditValues({ ...editValues, is_active: e.target.checked ? 'true' : 'false' })}
                            size="small"
                          />
                          <CheckboxField
                            label="Default"
                            name={`default_${model.pk}`}
                            checked={editValues.is_default || false}
                            onChange={(e) => setEditValues({ ...editValues, is_default: e.target.checked })}
                            size="small"
                          />
                        </Flex>
                      ) : (
                        <Flex direction="column" gap="5px">
                          {model.is_active === 'true' && <Badge size="small" variation="success">Active</Badge>}
                          {model.is_default && <Badge size="small" variation="info">Default</Badge>}
                        </Flex>
                      )}
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
                        <Flex gap="5px">
                          <Button 
                            size="small" 
                            variation="link" 
                            onClick={() => handleEdit(model)}
                            isDisabled={saveStatus === 'saving'}
                          >
                            Edit
                          </Button>
                          <Button 
                            size="small" 
                            variation="link" 
                            colorTheme="error"
                            onClick={() => handleDelete(model.pk)}
                          >
                            Delete
                          </Button>
                        </Flex>
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
        <Heading level={4}>Cost Calculation</Heading>
        <Text marginTop="10px">
          Prices are displayed per 1,000 tokens. Actual costs are calculated as:
        </Text>
        <View marginTop="10px" backgroundColor="rgba(0,0,0,0.05)" padding="10px" borderRadius="5px">
          <Text fontSize="small" fontFamily="monospace">
            Cost = (tokens ÷ 1,000) × price_per_1k
          </Text>
        </View>
      </Card>
    </View>
  )
}

export default ModelCosts