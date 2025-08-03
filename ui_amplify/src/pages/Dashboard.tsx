import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Heading,
  Text,
  View,
  Grid,
  Icon,
  Flex,
  Button,
  Loader,
  Alert,
  Badge
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

interface MetricCardProps {
  title: string
  value: number | string
  icon?: React.ReactNode
  onClick?: () => void
  loading?: boolean
  description?: string
}

const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  icon, 
  onClick, 
  loading,
  description 
}) => {
  return (
    <Card
      variation="elevated"
      style={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s, box-shadow 0.2s',
        height: '100%'
      }}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(-2px)'
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = ''
      }}
      onClick={onClick}
    >
      <Flex direction="column" gap="10px">
        <Flex justifyContent="space-between" alignItems="center">
          <Text fontSize="small" color="gray">{title}</Text>
          {icon}
        </Flex>
        {loading ? (
          <Loader size="small" />
        ) : (
          <Heading level={3}>{value}</Heading>
        )}
        {description && (
          <Text fontSize="small" color="gray">{description}</Text>
        )}
      </Flex>
    </Card>
  )
}

interface ExecutionStats {
  totalExecutions: number
  runningExecutions: number
  succeededExecutions: number
  failedExecutions: number
  abortedExecutions: number
  averageDurationSeconds: number
  executionsByAgent: Record<string, number>
  recentFailures: Array<{
    agentName: string
    executionName: string
    startDate: string
    error?: string
  }>
  successRate: number
  todayExecutions: number
  weekExecutions: number
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [agentCount, setAgentCount] = useState<number>(0)
  const [toolCount, setToolCount] = useState<number>(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<ExecutionStats | null>(null)

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    await fetchCounts()
    await fetchStatistics()
  }

  const fetchCounts = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch agents - no tableName needed anymore
      const agentResponse = await client.queries.listAgentsFromRegistry({})
      
      if (agentResponse.data) {
        const agents = agentResponse.data.filter(agent => agent !== null && agent !== undefined)
        setAgentCount(agents.length)
      }

      // Fetch tools - no tableName needed anymore
      const toolResponse = await client.queries.listToolsFromRegistry({})
      
      if (toolResponse.data) {
        const tools = toolResponse.data.filter(tool => tool !== null && tool !== undefined)
        setToolCount(tools.length)
      }
    } catch (err) {
      console.error('Error fetching counts:', err)
      setError('Failed to fetch registry data')
    } finally {
      setLoading(false)
    }
  }

  const fetchStatistics = async () => {
    try {
      const response = await client.queries.getExecutionStatistics({})
      
      if (response.data) {
        const data = typeof response.data === 'string' 
          ? JSON.parse(response.data) 
          : response.data
        
        if (data.statistics) {
          setStats(data.statistics)
        } else if (data.error) {
          console.error('Error in statistics response:', data.error)
        }
      }
    } catch (err) {
      console.error('Error fetching statistics:', err)
    }
  }

  return (
    <View>
      <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
        <Heading level={2}>Dashboard</Heading>
        <Button onClick={fetchAllData} size="small" variation="link">
          Refresh
        </Button>
      </Flex>

      {error && (
        <Alert 
          variation="error" 
          marginBottom="20px"
          onDismiss={() => setError(null)}
          isDismissible
        >
          {error}
        </Alert>
      )}

      <Grid
        templateColumns="1fr 1fr 1fr 1fr"
        gap="20px"
        marginBottom="30px"
      >
        <MetricCard
          title="Registered Agents"
          value={agentCount}
          loading={loading}
          description="AI agents available for execution"
          onClick={() => navigate('/registries')}
          icon={
            <View
              backgroundColor="blue.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Agents"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M12 2C13.1 2 14 2.9 14 4S13.1 6 12 6 10 5.1 10 4 10.9 2 12 2M12 7C14.2 7 16 8.8 16 11S14.2 15 12 15 8 13.2 8 11 9.8 7 12 7M12 16.5C14.5 16.5 19 17.8 19 20.5V22H5V20.5C5 17.8 9.5 16.5 12 16.5Z",
                    fill: "currentColor"
                  }
                ]}
              />
            </View>
          }
        />

        <MetricCard
          title="Available Tools"
          value={toolCount}
          loading={loading}
          description="Tools that agents can use"
          onClick={() => navigate('/registries')}
          icon={
            <View
              backgroundColor="green.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Tools"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M22.7 19L13.6 9.9C14.5 7.6 14 4.9 12.1 3C10.1 1 7.1 0.6 4.7 1.7L9 6L6 9L1.6 4.7C0.4 7.1 0.9 10.1 2.9 12.1C4.8 14 7.5 14.5 9.8 13.6L18.9 22.7C19.3 23.1 19.9 23.1 20.3 22.7L22.6 20.4C23.1 20 23.1 19.4 22.7 19Z",
                    fill: "currentColor"
                  }
                ]}
              />
            </View>
          }
        />

        <MetricCard
          title="Active Executions"
          value={stats?.runningExecutions || 0}
          description="Currently running agents"
          onClick={() => navigate('/history?status=RUNNING')}
          icon={
            <View
              backgroundColor="orange.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Running"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M13 2.05V5.08C16.39 5.57 19 8.47 19 12C19 15.87 15.87 19 12 19C8.13 19 5 15.87 5 12C5 8.47 7.61 5.57 11 5.08V2.05C5.94 2.55 2 6.81 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.81 18.06 2.55 13 2.05ZM12 6C8.69 6 6 8.69 6 12C6 15.31 8.69 18 12 18C15.31 18 18 15.31 18 12C18 8.69 15.31 6 12 6Z",
                    fill: "currentColor"
                  }
                ]}
              />
            </View>
          }
        />

        <MetricCard
          title="Success Rate"
          value={stats ? `${stats.successRate}%` : '0%'}
          description="Successful executions"
          icon={
            <View
              backgroundColor="purple.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Success"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z",
                    fill: "currentColor"
                  }
                ]}
              />
            </View>
          }
        />
      </Grid>

      {/* Additional Statistics Row */}
      <Grid
        templateColumns="1fr 1fr 1fr 1fr"
        gap="20px"
        marginBottom="30px"
      >
        <MetricCard
          title="Total Executions"
          value={stats?.totalExecutions || 0}
          description="All time executions"
          onClick={() => navigate('/history')}
          icon={
            <View
              backgroundColor="gray.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Total"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z",
                    fill: "currentColor"
                  }
                ]}
              />
            </View>
          }
        />
        
        <MetricCard
          title="Today's Executions"
          value={stats?.todayExecutions || 0}
          description="Executions started today"
          icon={
            <View
              backgroundColor="blue.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Today"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z",
                    fill: "currentColor"
                  }
                ]}
              />
            </View>
          }
        />
        
        <MetricCard
          title="Failed Executions"
          value={stats?.failedExecutions || 0}
          description="Total failures"
          onClick={() => navigate('/history?status=FAILED')}
          icon={
            <View
              backgroundColor="red.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Failed"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z",
                    fill: "currentColor"
                  }
                ]}
              />
            </View>
          }
        />
        
        <MetricCard
          title="Avg. Duration"
          value={stats ? formatDuration(stats.averageDurationSeconds) : '0s'}
          description="Average execution time"
          icon={
            <View
              backgroundColor="green.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Duration"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z",
                    fill: "currentColor"
                  }
                ]}
              />
            </View>
          }
        />
      </Grid>

      <Grid
        templateColumns="1fr 1fr"
        gap="20px"
      >
        <Card variation="elevated">
          <Heading level={4}>Quick Actions</Heading>
          <Flex direction="column" gap="10px" marginTop="15px">
            <Button 
              variation="primary" 
              onClick={() => navigate('/execute')}
              isFullWidth
            >
              Start New Execution
            </Button>
            <Button 
              variation="link" 
              onClick={() => navigate('/history')}
              isFullWidth
            >
              View Execution History
            </Button>
            <Button 
              variation="link" 
              onClick={() => navigate('/approvals')}
              isFullWidth
            >
              Check Pending Approvals
            </Button>
          </Flex>
        </Card>

        <Card variation="elevated">
          <Heading level={4}>Execution Summary</Heading>
          {stats && stats.executionsByAgent && Object.keys(stats.executionsByAgent).length > 0 ? (
            <View marginTop="15px">
              <Text fontSize="small" fontWeight="bold" marginBottom="10px">Executions by Agent:</Text>
              {Object.entries(stats.executionsByAgent)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([agent, count]) => (
                  <Flex key={agent} justifyContent="space-between" alignItems="center" marginBottom="5px">
                    <Text fontSize="small">{agent}</Text>
                    <Badge>{count}</Badge>
                  </Flex>
                ))
              }
              {Object.keys(stats.executionsByAgent).length > 5 && (
                <Text fontSize="small" color="gray" marginTop="5px">
                  And {Object.keys(stats.executionsByAgent).length - 5} more...
                </Text>
              )}
            </View>
          ) : (
            <Text marginTop="15px" fontSize="small" color="gray">
              No execution data available yet.
            </Text>
          )}
        </Card>
      </Grid>
    </View>
  )
}

export default Dashboard