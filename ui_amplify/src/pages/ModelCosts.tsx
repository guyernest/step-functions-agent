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

interface ModelPricing {
  id?: string
  modelName: string
  inputPrice: number
  outputPrice: number
  lastUpdated?: string | null
  updatedBy?: string | null
  isActive?: boolean | null
  isDefault?: boolean
}

const DEFAULT_MODELS: ModelPricing[] = [
  { modelName: 'gpt-4o', inputPrice: 2.50, outputPrice: 10.00, isDefault: true },
  { modelName: 'gpt-4o-mini', inputPrice: 0.15, outputPrice: 0.60, isDefault: true },
  { modelName: 'claude-3-7-sonnet-latest', inputPrice: 3.00, outputPrice: 15.00, isDefault: true },
  { modelName: 'gemini-2.0-flash-001', inputPrice: 0.10, outputPrice: 0.40, isDefault: true },
  { modelName: 'amazon.nova-pro', inputPrice: 0.80, outputPrice: 3.20, isDefault: true },
  { modelName: 'grok-2', inputPrice: 2.00, outputPrice: 10.00, isDefault: true }
]

const ModelCosts: React.FC = () => {
  const { user } = useAuthenticator()
  const [models, setModels] = useState<ModelPricing[]>([])
  const [loading, setLoading] = useState(true)
  const [editingModel, setEditingModel] = useState<string | null>(null)
  const [editValues, setEditValues] = useState<{ input: string; output: string }>({ input: '', output: '' })
  const [newModel, setNewModel] = useState<{ name: string; input: string; output: string }>({ 
    name: '', 
    input: '', 
    output: '' 
  })
  const [showAddForm, setShowAddForm] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  
  const getUserEmail = () => {
    return user?.signInDetails?.loginId || user?.username || 'Unknown'
  }

  useEffect(() => {
    fetchModelCosts()
  }, [])

  const fetchModelCosts = async () => {
    setLoading(true)
    try {
      const response = await client.models.ModelCost.list()
      const dbModels = response.data.map(item => ({
        id: item.id,
        modelName: item.modelName,
        inputPrice: item.inputPrice,
        outputPrice: item.outputPrice,
        lastUpdated: item.lastUpdated,
        updatedBy: item.updatedBy,
        isActive: item.isActive,
        isDefault: false
      }))

      // Merge with default models
      const modelMap = new Map<string, ModelPricing>()
      
      // Add defaults first
      DEFAULT_MODELS.forEach(model => {
        modelMap.set(model.modelName, model)
      })
      
      // Override with DB values
      dbModels.forEach(model => {
        if (model.isActive !== false) {
          modelMap.set(model.modelName, { ...model, isDefault: false })
        }
      })
      
      setModels(Array.from(modelMap.values()))
    } catch (error) {
      console.error('Error fetching model costs:', error)
      // Fall back to defaults on error
      setModels(DEFAULT_MODELS)
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (model: ModelPricing) => {
    setEditingModel(model.modelName)
    setEditValues({
      input: model.inputPrice.toString(),
      output: model.outputPrice.toString()
    })
  }

  const handleSave = async (modelName: string) => {
    const inputPrice = parseFloat(editValues.input)
    const outputPrice = parseFloat(editValues.output)

    if (!isNaN(inputPrice) && !isNaN(outputPrice) && inputPrice >= 0 && outputPrice >= 0) {
      setSaveStatus('saving')
      try {
        const existingModel = models.find(m => m.modelName === modelName && m.id)
        
        if (existingModel?.id) {
          // Update existing
          await client.models.ModelCost.update({
            id: existingModel.id,
            inputPrice,
            outputPrice,
            lastUpdated: new Date().toISOString(),
            updatedBy: getUserEmail()
          })
        } else {
          // Create new
          await client.models.ModelCost.create({
            modelName,
            inputPrice,
            outputPrice,
            lastUpdated: new Date().toISOString(),
            updatedBy: getUserEmail(),
            isActive: true
          })
        }
        
        await fetchModelCosts()
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

  const handleAddModel = async () => {
    const inputPrice = parseFloat(newModel.input)
    const outputPrice = parseFloat(newModel.output)

    if (newModel.name && !isNaN(inputPrice) && !isNaN(outputPrice) && inputPrice >= 0 && outputPrice >= 0) {
      const exists = models.find(m => m.modelName.toLowerCase() === newModel.name.toLowerCase())
      if (!exists) {
        setSaveStatus('saving')
        try {
          await client.models.ModelCost.create({
            modelName: newModel.name,
            inputPrice,
            outputPrice,
            lastUpdated: new Date().toISOString(),
            updatedBy: getUserEmail(),
            isActive: true
          })
          
          await fetchModelCosts()
          setNewModel({ name: '', input: '', output: '' })
          setShowAddForm(false)
          setSaveStatus('saved')
          setTimeout(() => setSaveStatus('idle'), 2000)
        } catch (error) {
          console.error('Error adding model:', error)
          setSaveStatus('error')
          setTimeout(() => setSaveStatus('idle'), 3000)
        }
      }
    }
  }

  const handleRemoveModel = async (model: ModelPricing) => {
    if (model.id) {
      setSaveStatus('saving')
      try {
        await client.models.ModelCost.update({
          id: model.id,
          isActive: false
        })
        await fetchModelCosts()
        setSaveStatus('saved')
        setTimeout(() => setSaveStatus('idle'), 2000)
      } catch (error) {
        console.error('Error removing model:', error)
        setSaveStatus('error')
        setTimeout(() => setSaveStatus('idle'), 3000)
      }
    }
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
          Model costs are stored in DynamoDB and used to calculate real-time usage expenses in the CloudWatch metrics dashboard. 
          Update these values when model providers change their pricing.
        </Text>
      </Alert>

      <Card variation="elevated">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
          <Heading level={4}>Model Pricing Configuration</Heading>
          <Button 
            size="small" 
            onClick={() => setShowAddForm(!showAddForm)}
            isDisabled={saveStatus === 'saving'}
          >
            {showAddForm ? 'Cancel' : 'Add Model'}
          </Button>
        </Flex>

        {showAddForm && (
          <Card variation="outlined" marginBottom="20px">
            <Heading level={5}>Add New Model</Heading>
            <Flex gap="10px" marginTop="10px">
              <TextField
                label="Model Name"
                value={newModel.name}
                onChange={(e) => setNewModel({ ...newModel, name: e.target.value })}
                placeholder="e.g., gpt-4-turbo"
                size="small"
              />
              <TextField
                label="Input Price"
                type="number"
                step="0.01"
                value={newModel.input}
                onChange={(e) => setNewModel({ ...newModel, input: e.target.value })}
                placeholder="0.00"
                size="small"
              />
              <TextField
                label="Output Price"
                type="number"
                step="0.01"
                value={newModel.output}
                onChange={(e) => setNewModel({ ...newModel, output: e.target.value })}
                placeholder="0.00"
                size="small"
              />
              <Button 
                onClick={handleAddModel}
                size="small"
                variation="primary"
                isDisabled={!newModel.name || !newModel.input || !newModel.output || saveStatus === 'saving'}
              >
                Add
              </Button>
            </Flex>
          </Card>
        )}

        <Table variation="striped">
          <TableHead>
            <TableRow>
              <TableCell as="th">Model</TableCell>
              <TableCell as="th">Input Price (per 1M tokens)</TableCell>
              <TableCell as="th">Output Price (per 1M tokens)</TableCell>
              <TableCell as="th">Status</TableCell>
              <TableCell as="th">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {models.map((model) => (
              <TableRow key={model.modelName}>
                <TableCell>
                  <Flex alignItems="center" gap="10px">
                    <Text fontWeight="bold">{model.modelName}</Text>
                    {!model.isDefault && <Badge size="small">Custom</Badge>}
                  </Flex>
                </TableCell>
                <TableCell>
                  {editingModel === model.modelName ? (
                    <TextField
                      label=""
                      value={editValues.input}
                      onChange={(e) => setEditValues({ ...editValues, input: e.target.value })}
                      type="number"
                      step="0.01"
                      size="small"
                    />
                  ) : (
                    <Text>{formatPrice(model.inputPrice)}</Text>
                  )}
                </TableCell>
                <TableCell>
                  {editingModel === model.modelName ? (
                    <TextField
                      label=""
                      value={editValues.output}
                      onChange={(e) => setEditValues({ ...editValues, output: e.target.value })}
                      type="number"
                      step="0.01"
                      size="small"
                    />
                  ) : (
                    <Text>{formatPrice(model.outputPrice)}</Text>
                  )}
                </TableCell>
                <TableCell>
                  {model.lastUpdated ? (
                    <View>
                      <Text fontSize="small" color="gray">
                        {new Date(model.lastUpdated).toLocaleDateString()}
                      </Text>
                      {model.updatedBy && (
                        <Text fontSize="x-small" color="gray">
                          by {model.updatedBy}
                        </Text>
                      )}
                    </View>
                  ) : (
                    <Text fontSize="small" color="gray">Default</Text>
                  )}
                </TableCell>
                <TableCell>
                  {editingModel === model.modelName ? (
                    <Flex gap="5px">
                      <Button 
                        size="small" 
                        onClick={() => handleSave(model.modelName)}
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
                      {!model.isDefault && (
                        <Button 
                          size="small" 
                          variation="link" 
                          colorTheme="error"
                          onClick={() => handleRemoveModel(model)}
                          isDisabled={saveStatus === 'saving'}
                        >
                          Remove
                        </Button>
                      )}
                    </Flex>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Cost Calculation Example</Heading>
        <Text marginTop="10px">
          For a conversation using GPT-4o with 1,000 input tokens and 500 output tokens:
        </Text>
        <View marginTop="10px" backgroundColor="rgba(0,0,0,0.05)" padding="10px" borderRadius="5px">
          <Text fontSize="small" fontFamily="monospace">
            Input Cost: 1,000 × ($2.50 / 1,000,000) = $0.0025
          </Text>
          <Text fontSize="small" fontFamily="monospace">
            Output Cost: 500 × ($10.00 / 1,000,000) = $0.0050
          </Text>
          <Text fontSize="small" fontFamily="monospace" fontWeight="bold">
            Total Cost: $0.0075
          </Text>
        </View>
      </Card>
    </View>
  )
}

export default ModelCosts