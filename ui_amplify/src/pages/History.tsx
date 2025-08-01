import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Card,
  Heading,
  Text,
  View,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Loader,
  Alert,
  Badge,
  Button,
  Flex,
  SelectField
} from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

interface Execution {
  executionArn: string
  stateMachineArn: string
  name: string
  status: string
  startDate: string
  stopDate?: string
  agentName?: string
}

const getStatusBadgeVariation = (status: string) => {
  switch (status) {
    case 'SUCCEEDED':
      return 'success'
    case 'FAILED':
      return 'error'
    case 'RUNNING':
      return 'info'
    case 'ABORTED':
      return 'warning'
    default:
      return undefined
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString()
}

const formatDuration = (startDate: string, stopDate?: string) => {
  const start = new Date(startDate).getTime()
  const stop = stopDate ? new Date(stopDate).getTime() : Date.now()
  const durationMs = stop - start
  
  const seconds = Math.floor(durationMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

const History: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [allExecutions, setAllExecutions] = useState<Execution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [agentFilter, setAgentFilter] = useState<string>('')
  const [refreshing, setRefreshing] = useState(false)
  const [agents, setAgents] = useState<string[]>([])

  // Initialize filters from URL parameters
  useEffect(() => {
    const agentParam = searchParams.get('agent') || ''
    const statusParam = searchParams.get('status') || ''
    setAgentFilter(agentParam)
    setStatusFilter(statusParam)
  }, [])

  useEffect(() => {
    fetchExecutions()
  }, [])

  // Update URL parameters when filters change
  const updateUrlParams = (agent: string, status: string) => {
    const params: Record<string, string> = {}
    if (agent) params.agent = agent
    if (status) params.status = status
    setSearchParams(params)
  }

  const handleAgentFilterChange = (value: string) => {
    setAgentFilter(value)
    updateUrlParams(value, statusFilter)
  }

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value)
    updateUrlParams(agentFilter, value)
  }

  const fetchExecutions = async () => {
    if (!refreshing) setLoading(true)
    setError(null)

    try {
      const response = await client.queries.listStepFunctionExecutions({
        status: statusFilter || undefined,
        maxResults: 100
      })

      console.log('Executions response:', response)

      if (response.data) {
        const data = typeof response.data === 'string' 
          ? JSON.parse(response.data) 
          : response.data

        if (data.executions) {
          // Store all executions
          setAllExecutions(data.executions)
          
          // Extract unique agent names
          const uniqueAgents = [...new Set(data.executions
            .map((exec: Execution) => exec.agentName)
            .filter((name: string | undefined) => name)
          )] as string[]
          setAgents(uniqueAgents.sort())
        } else if (data.error) {
          setError(data.error + (data.details ? ': ' + data.details : ''))
        }
      }
    } catch (err) {
      console.error('Error fetching executions:', err)
      setError('Failed to fetch executions')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchExecutions()
  }

  // Apply filters to all executions
  const filteredExecutions = React.useMemo(() => {
    let filtered = allExecutions
    
    if (agentFilter) {
      filtered = filtered.filter(exec => exec.agentName === agentFilter)
    }
    
    if (statusFilter) {
      filtered = filtered.filter(exec => exec.status === statusFilter)
    }
    
    return filtered
  }, [allExecutions, agentFilter, statusFilter])

  return (
    <View>
      <Heading level={2}>Execution History</Heading>
      
      {error && (
        <Alert 
          variation="error" 
          marginTop="10px"
          onDismiss={() => setError(null)}
          isDismissible
        >
          {error}
        </Alert>
      )}

      <Card variation="elevated" marginTop="20px">
        <Flex justifyContent="space-between" alignItems="center" marginBottom="10px">
          <Heading level={4}>Recent Executions</Heading>
          <Flex gap="10px" alignItems="center">
            <SelectField
              label=""
              value={agentFilter}
              onChange={(e) => handleAgentFilterChange(e.target.value)}
              width="200px"
            >
              <option value="">All Agents</option>
              {agents.map(agent => (
                <option key={agent} value={agent}>{agent}</option>
              ))}
            </SelectField>
            <SelectField
              label=""
              value={statusFilter}
              onChange={(e) => handleStatusFilterChange(e.target.value)}
              width="200px"
            >
              <option value="">All Statuses</option>
              <option value="RUNNING">Running</option>
              <option value="SUCCEEDED">Succeeded</option>
              <option value="FAILED">Failed</option>
              <option value="ABORTED">Aborted</option>
            </SelectField>
            <Button 
              onClick={handleRefresh} 
              isLoading={refreshing}
              variation="primary"
              size="small"
            >
              Refresh
            </Button>
          </Flex>
        </Flex>
        
        {loading ? (
          <Loader size="large" />
        ) : filteredExecutions.length > 0 ? (
          <Table marginTop="10px">
            <TableHead>
              <TableRow>
                <TableCell as="th">Agent</TableCell>
                <TableCell as="th">Execution Name</TableCell>
                <TableCell as="th">Status</TableCell>
                <TableCell as="th">Start Time</TableCell>
                <TableCell as="th">Duration</TableCell>
                <TableCell as="th">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredExecutions.map((execution) => (
                <TableRow key={execution.executionArn}>
                  <TableCell>{execution.agentName || 'Unknown'}</TableCell>
                  <TableCell>{execution.name || 'Unnamed'}</TableCell>
                  <TableCell>
                    <Badge variation={getStatusBadgeVariation(execution.status)}>
                      {execution.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDate(execution.startDate)}</TableCell>
                  <TableCell>
                    {formatDuration(execution.startDate, execution.stopDate)}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      onClick={() => {
                        navigate(`/execution/${encodeURIComponent(execution.executionArn)}`)
                      }}
                    >
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Text marginTop="10px">
            {allExecutions.length === 0 
              ? 'No executions found. Start an agent execution to see it here.'
              : 'No executions match the current filters.'}
          </Text>
        )}
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>About Execution History</Heading>
        <Text marginTop="10px">
          This page shows the history of all Step Functions executions. You can filter by status 
          and view details of individual executions to see their input, output, and step-by-step progress.
        </Text>
      </Card>
    </View>
  )
}

export default History