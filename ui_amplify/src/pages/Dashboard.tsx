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
  Alert
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

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [agentCount, setAgentCount] = useState<number>(0)
  const [toolCount, setToolCount] = useState<number>(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCounts()
  }, [])

  const fetchCounts = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch agents
      const agentTableName = localStorage.getItem('agentRegistryTableName') || 'AgentRegistry-prod'
      const agentResponse = await client.queries.listAgentsFromRegistry({ tableName: agentTableName })
      
      if (agentResponse.data) {
        const agentData = typeof agentResponse.data === 'string' 
          ? JSON.parse(agentResponse.data) 
          : agentResponse.data
        
        if (agentData.agents) {
          setAgentCount(agentData.agents.length)
        }
      }

      // Fetch tools
      const toolTableName = localStorage.getItem('toolRegistryTableName') || 'tool-registry-prod'
      const toolResponse = await client.queries.listToolsFromRegistry({ tableName: toolTableName })
      
      if (toolResponse.data) {
        const toolData = typeof toolResponse.data === 'string' 
          ? JSON.parse(toolResponse.data) 
          : toolResponse.data
        
        if (toolData.tools) {
          setToolCount(toolData.tools.length)
        }
      }
    } catch (err) {
      console.error('Error fetching counts:', err)
      setError('Failed to fetch registry data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <View>
      <Flex justifyContent="space-between" alignItems="center" marginBottom="20px">
        <Heading level={2}>Dashboard</Heading>
        <Button onClick={fetchCounts} size="small" variation="link">
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
          value="Coming Soon"
          description="Currently running agents"
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
          title="Pending Approvals"
          value="Coming Soon"
          description="Waiting for human input"
          icon={
            <View
              backgroundColor="purple.20"
              borderRadius="4px"
              padding="8px"
            >
              <Icon
                ariaLabel="Approvals"
                viewBox={{ width: 24, height: 24 }}
                paths={[
                  {
                    d: "M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z",
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
          <Heading level={4}>System Overview</Heading>
          <Text marginTop="15px">
            Welcome to the Step Functions Agent Management Console. This dashboard provides
            quick access to all agent operations and monitoring capabilities.
          </Text>
          <Text marginTop="10px" fontSize="small" color="gray">
            Click on any metric card above to navigate to detailed views.
          </Text>
        </Card>
      </Grid>
    </View>
  )
}

export default Dashboard