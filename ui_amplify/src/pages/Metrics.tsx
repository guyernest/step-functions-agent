import React, { useState, useEffect } from 'react'
import {
  Card,
  Heading,
  Text,
  View,
  Button,
  Loader,
  Alert,
  Flex,
  SelectField,
  Grid
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'

const client = generateClient<Schema>()

interface MetricData {
  id: string
  label: string
  timestamps: string[]
  values: number[]
  statusCode: string
}

interface ChartData {
  time: string
  cost?: number
  inputTokens?: number
  outputTokens?: number
  [key: string]: any // For dynamic model/agent costs
}

interface CostBreakdown {
  totalCost: MetricData
  costByModel: { [model: string]: MetricData }
  costByAgent: { [agent: string]: MetricData }
  summary: {
    totalSpent: number
    topModel?: {
      name: string
      cost: number
      percentage: number
    }
    topAgent?: {
      name: string
      cost: number
      percentage: number
    }
    modelBreakdown?: Array<{
      name: string
      cost: number
      percentage: number
    }>
    agentBreakdown?: Array<{
      name: string
      cost: number
      percentage: number
    }>
  }
}

const CHART_COLORS = [
  '#047D95', // Primary teal
  '#A23B72', // Rose
  '#2E86AB', // Blue
  '#F18F01', // Orange
  '#C73E1D', // Red
  '#6A994E', // Green
  '#BC4B51', // Coral
  '#5B8E7D', // Sea green
]

const Metrics: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [costData, setCostData] = useState<ChartData[]>([])
  const [tokenData, setTokenData] = useState<ChartData[]>([])
  const [totalCost, setTotalCost] = useState(0)
  const [timeRange, setTimeRange] = useState('24h')
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [agents, setAgents] = useState<{id: string, name: string}[]>([])
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown | null>(null)
  const [viewMode, setViewMode] = useState<'total' | 'model' | 'agent'>('total')

  useEffect(() => {
    fetchAgents()
  }, [])

  useEffect(() => {
    fetchMetrics()
  }, [timeRange, selectedAgent])

  const fetchAgents = async () => {
    try {
      const response = await client.queries.listAgentsFromRegistry({})
      if (response.data) {
        const agentList = response.data
          .filter(agent => agent !== null && agent !== undefined)
          .map(agent => ({
            id: agent!.id,
            name: agent!.name
          }))
        setAgents(agentList)
      }
    } catch (err) {
      console.error('Error fetching agents:', err)
    }
  }

  const fetchMetrics = async () => {
    setLoading(true)
    setError(null)
    setCostBreakdown(null) // Clear previous breakdown

    try {
      // Calculate time range
      const endTime = new Date()
      let startTime = new Date()
      let period = 300 // 5 minutes default

      switch (timeRange) {
        case '1h':
          startTime = new Date(endTime.getTime() - 60 * 60 * 1000)
          period = 60 // 1 minute
          break
        case '3h':
          startTime = new Date(endTime.getTime() - 3 * 60 * 60 * 1000)
          period = 300 // 5 minutes
          break
        case '6h':
          startTime = new Date(endTime.getTime() - 6 * 60 * 60 * 1000)
          period = 300 // 5 minutes
          break
        case '12h':
          startTime = new Date(endTime.getTime() - 12 * 60 * 60 * 1000)
          period = 300 // 5 minutes
          break
        case '24h':
          startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000)
          period = 3600 // 1 hour
          break
        case '7d':
          startTime = new Date(endTime.getTime() - 7 * 24 * 60 * 60 * 1000)
          period = 3600 // 1 hour
          break
        default:
          startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000)
          period = 3600 // 1 hour
      }

      // Fetch cost metrics
      const costResponse = await client.queries.getCloudWatchMetrics({
        metricType: 'cost',
        startTime: startTime.toISOString(),
        endTime: endTime.toISOString(),
        period: period
      })

      if (costResponse.data) {
        const data = typeof costResponse.data === 'string' 
          ? JSON.parse(costResponse.data) 
          : costResponse.data

        // Handle new breakdown structure
        if (data.totalCost) {
          setCostBreakdown(data as CostBreakdown)
          
          // Set total cost from summary
          if (data.summary?.totalSpent !== undefined) {
            setTotalCost(data.summary.totalSpent)
          }
          
          // Prepare chart data based on view mode
          const timestamps = data.totalCost.timestamps || []
          const chartData: ChartData[] = timestamps.map((timestamp: string, index: number) => {
            const dataPoint: ChartData = {
              time: formatTimeAxis(timestamp, timeRange),
              totalCost: data.totalCost.values[index] || 0
            }
            
            // Add model breakdown data
            if (data.costByModel) {
              Object.entries(data.costByModel).forEach(([model, modelData]) => {
                const metricData = modelData as MetricData
                dataPoint[`model_${model}`] = metricData.values[index] || 0
              })
            }
            
            // Add agent breakdown data
            if (data.costByAgent) {
              Object.entries(data.costByAgent).forEach(([agent, agentData]) => {
                const metricData = agentData as MetricData
                dataPoint[`agent_${agent}`] = metricData.values[index] || 0
              })
            }
            
            return dataPoint
          })
          
          setCostData(chartData)
        } else if (data.data && Array.isArray(data.data)) {
          // Fallback to old format
          const costMetric = data.data.find((m: MetricData) => m.id === 'cost')
          if (costMetric && costMetric.timestamps && costMetric.values) {
            const chartData = costMetric.timestamps.map((timestamp: string, index: number) => ({
              time: formatTimeAxis(timestamp, timeRange),
              cost: costMetric.values[index] || 0
            }))
            setCostData(chartData)
            
            // Calculate total cost
            const total = costMetric.values.reduce((sum: number, val: number) => sum + (val || 0), 0)
            setTotalCost(total)
          }
        }
      }

      // Fetch token metrics if an agent is selected
      if (selectedAgent) {
        const tokenResponse = await client.queries.getCloudWatchMetrics({
          metricType: 'tokens',
          startTime: startTime.toISOString(),
          endTime: endTime.toISOString(),
          period: period,
          agentName: selectedAgent
        })

        if (tokenResponse.data) {
          const data = typeof tokenResponse.data === 'string' 
            ? JSON.parse(tokenResponse.data) 
            : tokenResponse.data

          if (data.data && Array.isArray(data.data)) {
            const inputTokens = data.data.find((m: MetricData) => m.id === 'input_tokens')
            const outputTokens = data.data.find((m: MetricData) => m.id === 'output_tokens')
            
            if (inputTokens && inputTokens.timestamps) {
              const chartData = inputTokens.timestamps.map((timestamp: string, index: number) => ({
                time: formatTimeAxis(timestamp, timeRange),
                inputTokens: inputTokens.values?.[index] || 0,
                outputTokens: outputTokens?.values?.[index] || 0
              }))
              setTokenData(chartData)
            }
          }
        }
      }
    } catch (err) {
      console.error('Error fetching metrics:', err)
      setError('Failed to fetch metrics')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    }).format(value)
  }

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(Math.round(value))
  }

  const formatTimeAxis = (timestamp: string, range: string): string => {
    const date = new Date(timestamp)
    
    // For ranges less than 24 hours, show time
    if (['1h', '3h', '6h', '12h'].includes(range)) {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })
    }
    
    // For 24 hours, show day and time
    if (range === '24h') {
      return date.toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric',
        hour12: true 
      })
    }
    
    // For 7 days, show date only
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    })
  }

  const getModelDisplayName = (model: string): string => {
    const displayNames: { [key: string]: string } = {
      'claude-3-7-sonnet-latest': 'Claude 3.7 Sonnet',
      'gemini-2.0-flash-001': 'Gemini 2.0 Flash',
      'gpt-4o': 'GPT-4o',
      'gpt-4o-mini': 'GPT-4o Mini',
      'amazon.nova-pro': 'Amazon Nova Pro',
      'grok-2': 'Grok 2'
    }
    return displayNames[model] || model
  }

  return (
    <View>
      <Heading level={2}>CloudWatch Metrics</Heading>
      
      {error && (
        <Alert variation="error" marginTop="10px" marginBottom="10px">
          {error}
        </Alert>
      )}

      <Card variation="elevated" marginTop="20px">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
          <Heading level={4}>Model Usage Cost</Heading>
          <Flex gap="10px" alignItems="center">
            <SelectField
              label=""
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              size="small"
            >
              <option value="1h">Last Hour</option>
              <option value="3h">Last 3 Hours</option>
              <option value="6h">Last 6 Hours</option>
              <option value="12h">Last 12 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </SelectField>
            <Button size="small" onClick={fetchMetrics}>
              Refresh
            </Button>
          </Flex>
        </Flex>

        {loading ? (
          <Flex justifyContent="center" padding="40px">
            <Loader size="large" />
          </Flex>
        ) : (
          <>
            {/* Summary Cards */}
            <Grid templateColumns="1fr 1fr 1fr" gap="15px" marginBottom="20px">
              <Card variation="outlined">
                <View>
                  <Text fontSize="small" color="gray">Total Cost ({timeRange})</Text>
                  <Text fontSize="xl" fontWeight="bold" color="#047D95">
                    {formatCurrency(totalCost)}
                  </Text>
                </View>
              </Card>
              
              {costBreakdown?.summary?.topModel && (
                <Card variation="outlined">
                  <View>
                    <Text fontSize="small" color="gray">Top Model</Text>
                    <Text fontSize="medium" fontWeight="bold">
                      {getModelDisplayName(costBreakdown.summary.topModel.name)}
                    </Text>
                    <Text fontSize="small" color="#047D95">
                      {formatCurrency(costBreakdown.summary.topModel.cost)} ({costBreakdown.summary.topModel.percentage.toFixed(0)}%)
                    </Text>
                  </View>
                </Card>
              )}
              
              {costBreakdown?.summary?.topAgent && (
                <Card variation="outlined">
                  <View>
                    <Text fontSize="small" color="gray">Top Agent</Text>
                    <Text fontSize="medium" fontWeight="bold">
                      {costBreakdown.summary.topAgent.name}
                    </Text>
                    <Text fontSize="small" color="#047D95">
                      {formatCurrency(costBreakdown.summary.topAgent.cost)} ({costBreakdown.summary.topAgent.percentage.toFixed(0)}%)
                    </Text>
                  </View>
                </Card>
              )}
            </Grid>

            {/* View Mode Selector */}
            <Flex justifyContent="center" marginBottom="20px">
              <Button
                size="small"
                variation={viewMode === 'total' ? 'primary' : 'link'}
                onClick={() => setViewMode('total')}
              >
                Total Cost
              </Button>
              <Button
                size="small"
                variation={viewMode === 'model' ? 'primary' : 'link'}
                onClick={() => setViewMode('model')}
              >
                By Model
              </Button>
              <Button
                size="small"
                variation={viewMode === 'agent' ? 'primary' : 'link'}
                onClick={() => setViewMode('agent')}
              >
                By Agent
              </Button>
            </Flex>

            {/* Cost Chart */}
            {costData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  {viewMode === 'total' ? (
                    <AreaChart data={costData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis tickFormatter={(value) => `$${value.toFixed(3)}`} />
                      <Tooltip formatter={(value: number) => formatCurrency(value)} />
                      <Area 
                        type="monotone" 
                        dataKey="totalCost" 
                        stroke="#047D95" 
                        fill="#047D95" 
                        fillOpacity={0.3}
                        name="Total Cost (USD)"
                      />
                    </AreaChart>
                  ) : viewMode === 'model' ? (
                    <AreaChart data={costData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis tickFormatter={(value) => `$${value.toFixed(3)}`} />
                      <Tooltip 
                        formatter={(value: number, name: string) => [
                          formatCurrency(value),
                          getModelDisplayName(name.replace('model_', ''))
                        ]}
                      />
                      <Legend 
                        formatter={(value: string) => getModelDisplayName(value.replace('model_', ''))}
                      />
                      {costBreakdown?.costByModel && Object.keys(costBreakdown.costByModel).map((model, index) => (
                        <Area
                          key={model}
                          type="monotone"
                          dataKey={`model_${model}`}
                          stackId="1"
                          stroke={CHART_COLORS[index % CHART_COLORS.length]}
                          fill={CHART_COLORS[index % CHART_COLORS.length]}
                          fillOpacity={0.6}
                          name={`model_${model}`}
                        />
                      ))}
                    </AreaChart>
                  ) : (
                    <AreaChart data={costData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis tickFormatter={(value) => `$${value.toFixed(3)}`} />
                      <Tooltip 
                        formatter={(value: number, name: string) => [
                          formatCurrency(value),
                          name.replace('agent_', '')
                        ]}
                      />
                      <Legend 
                        formatter={(value: string) => value.replace('agent_', '')}
                      />
                      {costBreakdown?.costByAgent && Object.keys(costBreakdown.costByAgent).map((agent, index) => (
                        <Area
                          key={agent}
                          type="monotone"
                          dataKey={`agent_${agent}`}
                          stackId="1"
                          stroke={CHART_COLORS[index % CHART_COLORS.length]}
                          fill={CHART_COLORS[index % CHART_COLORS.length]}
                          fillOpacity={0.6}
                          name={`agent_${agent}`}
                        />
                      ))}
                    </AreaChart>
                  )}
                </ResponsiveContainer>

                {/* Breakdown Tables */}
                {viewMode !== 'total' && costBreakdown?.summary && (
                  <Grid templateColumns="1fr 1fr" gap="20px" marginTop="20px">
                    {viewMode === 'model' && costBreakdown.summary.modelBreakdown && (
                      <Card variation="outlined">
                        <Heading level={5}>Model Breakdown</Heading>
                        <View marginTop="10px">
                          {costBreakdown.summary.modelBreakdown.map((model, index) => (
                            <Flex key={model.name} justifyContent="space-between" padding="5px 0">
                              <Flex alignItems="center" gap="10px">
                                <View
                                  backgroundColor={CHART_COLORS[index % CHART_COLORS.length]}
                                  width="12px"
                                  height="12px"
                                  borderRadius="2px"
                                />
                                <Text fontSize="small">{getModelDisplayName(model.name)}</Text>
                              </Flex>
                              <Text fontSize="small" fontWeight="bold">
                                {formatCurrency(model.cost)} ({model.percentage.toFixed(1)}%)
                              </Text>
                            </Flex>
                          ))}
                        </View>
                      </Card>
                    )}
                    
                    {viewMode === 'agent' && costBreakdown.summary.agentBreakdown && (
                      <Card variation="outlined">
                        <Heading level={5}>Agent Breakdown</Heading>
                        <View marginTop="10px">
                          {costBreakdown.summary.agentBreakdown.map((agent, index) => (
                            <Flex key={agent.name} justifyContent="space-between" padding="5px 0">
                              <Flex alignItems="center" gap="10px">
                                <View
                                  backgroundColor={CHART_COLORS[index % CHART_COLORS.length]}
                                  width="12px"
                                  height="12px"
                                  borderRadius="2px"
                                />
                                <Text fontSize="small">{agent.name}</Text>
                              </Flex>
                              <Text fontSize="small" fontWeight="bold">
                                {formatCurrency(agent.cost)} ({agent.percentage.toFixed(1)}%)
                              </Text>
                            </Flex>
                          ))}
                        </View>
                      </Card>
                    )}
                  </Grid>
                )}
              </>
            ) : (
              <Text color="gray" textAlign="center" padding="40px">
                No cost data available for the selected time range
              </Text>
            )}
          </>
        )}
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
          <Heading level={4}>Token Usage by Agent</Heading>
          <SelectField
            label=""
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            size="small"
            placeholder="Select an agent"
          >
            <option value="">-- Select an agent --</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.name}>
                {agent.name}
              </option>
            ))}
          </SelectField>
        </Flex>

        {selectedAgent && !loading ? (
          tokenData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={tokenData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis tickFormatter={formatNumber} />
                <Tooltip formatter={(value: number) => formatNumber(value)} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="inputTokens" 
                  stroke="#2E86AB" 
                  name="Input Tokens"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="outputTokens" 
                  stroke="#A23B72" 
                  name="Output Tokens"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <Text color="gray" textAlign="center" padding="40px">
              No token data available for the selected agent and time range
            </Text>
          )
        ) : (
          <Text color="gray" textAlign="center" padding="40px">
            {loading ? 'Loading...' : 'Select an agent to view token usage'}
          </Text>
        )}
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>About Metrics</Heading>
        <Text marginTop="10px">
          This page displays CloudWatch metrics for your AI agents:
        </Text>
        <View marginTop="10px">
          <Text fontSize="small">
            • <strong>Model Usage Cost</strong>: Total cost with breakdown by model and agent
          </Text>
          <Text fontSize="small" marginTop="5px">
            • <strong>Cost Views</strong>: Switch between total, by-model, and by-agent breakdowns
          </Text>
          <Text fontSize="small" marginTop="5px">
            • <strong>Token Usage</strong>: Input and output token consumption per agent
          </Text>
          <Text fontSize="small" marginTop="5px">
            • <strong>Time Range</strong>: Metrics available up to 15 days (1-min), 63 days (5-min), or 455 days (1-hour)
          </Text>
          <Text fontSize="small" marginTop="5px">
            • <strong>Pricing</strong>: Dynamically loaded from Model Costs configuration
          </Text>
          <Text fontSize="small" marginTop="5px">
            • <strong>Summary Cards</strong>: Quick insights on total cost, top model, and top agent
          </Text>
        </View>
        <Alert variation="info" marginTop="10px">
          <Text fontSize="small">
            Model pricing is loaded from DynamoDB. Visit the <strong>Model Costs</strong> page to update pricing.
          </Text>
        </Alert>
      </Card>
    </View>
  )
}

export default Metrics