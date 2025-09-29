import React, { useState, useEffect, useCallback, useRef } from 'react'
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
  SelectField,
  TextField,
  Grid
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

interface ExecutionsResponse {
  executions: Execution[]
  nextToken?: string
  hasMore: boolean
  totalCount?: number
  metadata?: {
    fromCache: boolean
    fetchTime: number
  }
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

const formatDateForInput = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
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

const PAGE_SIZE = 25

const History: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [executions, setExecutions] = useState<Execution[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [agentFilter, setAgentFilter] = useState<string>('')
  const [startDateFrom, setStartDateFrom] = useState<string>('')
  const [startDateTo, setStartDateTo] = useState<string>('')
  const [refreshing, setRefreshing] = useState(false)
  const [agents, setAgents] = useState<string[]>([])
  const [registryAgents, setRegistryAgents] = useState<string[]>([])
  const [executionAgents, setExecutionAgents] = useState<string[]>([])
  const [nextToken, setNextToken] = useState<string | undefined>(undefined)
  const [hasMore, setHasMore] = useState(false)
  const [totalLoaded, setTotalLoaded] = useState(0)
  const [fetchMetadata, setFetchMetadata] = useState<{ fromCache: boolean; fetchTime: number } | null>(null)

  // Track scroll position for virtual scrolling
  const tableContainerRef = useRef<HTMLDivElement>(null)
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 50 })

  // Initialize filters from URL parameters
  useEffect(() => {
    const agentParam = searchParams.get('agent') || ''
    const statusParam = searchParams.get('status') || ''
    const fromParam = searchParams.get('from') || ''
    const toParam = searchParams.get('to') || ''

    setAgentFilter(agentParam)
    setStatusFilter(statusParam)
    setStartDateFrom(fromParam)
    setStartDateTo(toParam)

    // If agent parameter is set, ensure it's in the agents list
    if (agentParam && !agents.includes(agentParam)) {
      setAgents(prev => [...prev, agentParam].sort())
    }
  }, [])

  // Fetch registry agents on mount
  useEffect(() => {
    fetchRegistryAgents()
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchExecutions(true)
  }, [statusFilter, agentFilter, startDateFrom, startDateTo])

  // Update URL parameters when filters change
  // Fetch all agents from registry
  const fetchRegistryAgents = async () => {
    try {
      const response = await client.queries.listAgentsFromRegistry({})

      if (response.data) {
        const agentNames = response.data
          .filter(agent => agent !== null && agent !== undefined && agent.name)
          .map(agent => agent!.name)
          .filter((name): name is string => typeof name === 'string')
          .sort()

        setRegistryAgents(agentNames)
        updateAgentsList(agentNames, executionAgents)
      }
    } catch (err) {
      console.error('Error fetching registry agents:', err)
      // Non-critical error - registry agents are optional enhancement
    }
  }

  // Merge registry agents with execution agents
  const updateAgentsList = (registry: string[], executions: string[]) => {
    // Create a Set to ensure uniqueness
    const allAgents = new Set<string>()

    // Add execution agents first (they're more relevant)
    executions.forEach(agent => allAgents.add(agent))

    // Add registry agents
    registry.forEach(agent => allAgents.add(agent))

    // Convert to sorted array
    setAgents(Array.from(allAgents).sort())
  }

  const updateUrlParams = useCallback((agent: string, status: string, from: string, to: string) => {
    const params: Record<string, string> = {}
    if (agent) params.agent = agent
    if (status) params.status = status
    if (from) params.from = from
    if (to) params.to = to
    setSearchParams(params)
  }, [setSearchParams])

  const handleAgentFilterChange = (value: string) => {
    setAgentFilter(value)
    updateUrlParams(value, statusFilter, startDateFrom, startDateTo)
  }

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value)
    updateUrlParams(agentFilter, value, startDateFrom, startDateTo)
  }

  const handleStartDateFromChange = (value: string) => {
    setStartDateFrom(value)
    updateUrlParams(agentFilter, statusFilter, value, startDateTo)
  }

  const handleStartDateToChange = (value: string) => {
    setStartDateTo(value)
    updateUrlParams(agentFilter, statusFilter, startDateFrom, value)
  }

  const fetchExecutions = async (reset: boolean = false) => {
    if (reset) {
      setLoading(true)
      setExecutions([])
      setNextToken(undefined)
      setTotalLoaded(0)
    } else {
      setLoadingMore(true)
    }

    setError(null)

    try {
      const params: any = {
        maxResults: PAGE_SIZE,
        status: statusFilter || undefined,
        agentName: agentFilter || undefined,
        startDateFrom: startDateFrom || undefined,
        startDateTo: startDateTo || undefined
      }

      if (!reset && nextToken) {
        params.nextToken = nextToken
      }

      const response = await client.queries.listStepFunctionExecutions(params)

      console.log('Executions response:', response)

      if (response.data) {
        const data = typeof response.data === 'string'
          ? JSON.parse(response.data)
          : response.data as ExecutionsResponse

        if (data.executions) {
          if (reset) {
            setExecutions(data.executions)

            // Extract unique agent names from first batch
            const uniqueAgents = [...new Set(data.executions
              .map((exec: Execution) => exec.agentName)
              .filter((name: string | undefined) => name)
            )] as string[]

            setExecutionAgents(uniqueAgents)
            updateAgentsList(registryAgents, uniqueAgents)
          } else {
            setExecutions(prev => [...prev, ...data.executions])

            // Update agent list with any new agents
            const newAgents = data.executions
              .map((exec: Execution) => exec.agentName)
              .filter((name: string | undefined) => name && !executionAgents.includes(name)) as string[]

            if (newAgents.length > 0) {
              const updatedExecutionAgents = [...executionAgents, ...newAgents]
              setExecutionAgents(updatedExecutionAgents)
              updateAgentsList(registryAgents, updatedExecutionAgents)
            }
          }

          setNextToken(data.nextToken)
          setHasMore(data.hasMore || false)
          setTotalLoaded(prev => prev + data.executions.length)

          if (data.metadata) {
            setFetchMetadata(data.metadata)
          }
        } else if ('error' in data) {
          setError((data as any).error + ((data as any).details ? ': ' + (data as any).details : ''))
        }
      }
    } catch (err) {
      console.error('Error fetching executions:', err)
      setError('Failed to fetch executions')
    } finally {
      setLoading(false)
      setLoadingMore(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchExecutions(true)
  }

  const handleLoadMore = () => {
    if (!loadingMore && hasMore) {
      fetchExecutions(false)
    }
  }

  // Virtual scrolling handler
  const handleScroll = useCallback(() => {
    if (!tableContainerRef.current) return

    const container = tableContainerRef.current
    const scrollTop = container.scrollTop
    const rowHeight = 50 // Approximate row height in pixels
    const containerHeight = container.clientHeight
    const buffer = 10 // Number of rows to render outside visible area

    const start = Math.max(0, Math.floor(scrollTop / rowHeight) - buffer)
    const end = Math.min(
      executions.length,
      Math.ceil((scrollTop + containerHeight) / rowHeight) + buffer
    )

    setVisibleRange({ start, end })

    // Auto-load more when near bottom
    const scrollPercentage = (scrollTop + containerHeight) / container.scrollHeight
    if (scrollPercentage > 0.8 && hasMore && !loadingMore) {
      handleLoadMore()
    }
  }, [executions.length, hasMore, loadingMore])

  // Visible executions for virtual scrolling
  const visibleExecutions = executions.slice(visibleRange.start, visibleRange.end)

  // Calculate quick preset dates
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const weekAgo = new Date(today)
  weekAgo.setDate(weekAgo.getDate() - 7)
  const monthAgo = new Date(today)
  monthAgo.setMonth(monthAgo.getMonth() - 1)

  const applyDatePreset = (from: Date, to: Date) => {
    const fromStr = formatDateForInput(from)
    const toStr = formatDateForInput(to)
    setStartDateFrom(fromStr)
    setStartDateTo(toStr)
    updateUrlParams(agentFilter, statusFilter, fromStr, toStr)
  }

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
          <Heading level={4}>Executions</Heading>
          <Button
            onClick={handleRefresh}
            isLoading={refreshing}
            variation="primary"
            size="small"
          >
            Refresh
          </Button>
        </Flex>

        {/* Filters */}
        <Grid
          templateColumns="1fr 1fr 1fr 1fr"
          gap="10px"
          marginBottom="15px"
        >
          <SelectField
            label="Agent"
            value={agentFilter}
            onChange={(e) => handleAgentFilterChange(e.target.value)}
          >
            <option value="">All Agents</option>

            {/* Agents with recent executions */}
            {executionAgents.length > 0 && (
              <optgroup label="Recently Executed">
                {executionAgents.map(agent => (
                  <option key={`exec-${agent}`} value={agent}>{agent}</option>
                ))}
              </optgroup>
            )}

            {/* Registry agents not in executions */}
            {(() => {
              const registryOnlyAgents = registryAgents.filter(
                agent => !executionAgents.includes(agent)
              )
              return registryOnlyAgents.length > 0 ? (
                <optgroup label="Available Agents">
                  {registryOnlyAgents.map(agent => (
                    <option key={`reg-${agent}`} value={agent}>{agent}</option>
                  ))}
                </optgroup>
              ) : null
            })()}

            {/* Agent from URL parameter not in registry or executions */}
            {agentFilter &&
             !executionAgents.includes(agentFilter) &&
             !registryAgents.includes(agentFilter) && (
              <optgroup label="Other">
                <option value={agentFilter}>{agentFilter}</option>
              </optgroup>
            )}
          </SelectField>

          <SelectField
            label="Status"
            value={statusFilter}
            onChange={(e) => handleStatusFilterChange(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="RUNNING">Running</option>
            <option value="SUCCEEDED">Succeeded</option>
            <option value="FAILED">Failed</option>
            <option value="ABORTED">Aborted</option>
          </SelectField>

          <TextField
            label="From Date"
            type="date"
            value={startDateFrom}
            onChange={(e) => handleStartDateFromChange(e.target.value)}
          />

          <TextField
            label="To Date"
            type="date"
            value={startDateTo}
            onChange={(e) => handleStartDateToChange(e.target.value)}
          />
        </Grid>

        {/* Date presets */}
        <Flex gap="10px" marginBottom="15px">
          <Text>Quick filters:</Text>
          <Button size="small" onClick={() => applyDatePreset(today, today)}>
            Today
          </Button>
          <Button size="small" onClick={() => applyDatePreset(yesterday, today)}>
            Last 24h
          </Button>
          <Button size="small" onClick={() => applyDatePreset(weekAgo, today)}>
            Last 7 days
          </Button>
          <Button size="small" onClick={() => applyDatePreset(monthAgo, today)}>
            Last 30 days
          </Button>
          <Button size="small" onClick={() => {
            setStartDateFrom('')
            setStartDateTo('')
            updateUrlParams(agentFilter, statusFilter, '', '')
          }}>
            Clear dates
          </Button>
        </Flex>

        {/* Metadata display */}
        {fetchMetadata && (
          <Flex gap="20px" marginBottom="10px">
            <Text fontSize="small" color="font.tertiary">
              Loaded: {totalLoaded} executions
            </Text>
            <Text fontSize="small" color="font.tertiary">
              Fetch time: {fetchMetadata.fetchTime}ms
            </Text>
            <Text fontSize="small" color="font.tertiary">
              {fetchMetadata.fromCache ? '(from cache)' : '(fresh data)'}
            </Text>
          </Flex>
        )}

        {loading ? (
          <Loader size="large" />
        ) : executions.length > 0 ? (
          <>
            <div
              ref={tableContainerRef}
              onScroll={handleScroll}
              style={{
                maxHeight: '600px',
                overflowY: 'auto',
                position: 'relative'
              }}
            >
              {/* Virtual spacer for scroll position */}
              {visibleRange.start > 0 && (
                <div style={{ height: `${visibleRange.start * 50}px` }} />
              )}

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
                  {visibleExecutions.map((execution) => (
                    <TableRow key={execution.executionArn} style={{ height: '50px' }}>
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

              {/* Virtual spacer for scroll position */}
              {visibleRange.end < executions.length && (
                <div style={{ height: `${(executions.length - visibleRange.end) * 50}px` }} />
              )}
            </div>

            {/* Load more button */}
            {hasMore && (
              <Flex justifyContent="center" marginTop="20px">
                <Button
                  onClick={handleLoadMore}
                  isLoading={loadingMore}
                  variation="primary"
                >
                  Load More
                </Button>
              </Flex>
            )}
          </>
        ) : (
          <Text marginTop="10px">
            No executions found. {agentFilter || statusFilter || startDateFrom || startDateTo
              ? 'Try adjusting your filters.'
              : 'Start an agent execution to see it here.'}
          </Text>
        )}
      </Card>

      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Performance Information</Heading>
        <Text marginTop="10px">
          This page uses pagination and virtual scrolling for optimal performance. Only {PAGE_SIZE} executions
          are loaded at a time. Use filters to narrow down your search, and click "Load More" to fetch
          additional results. The table only renders visible rows to maintain smooth scrolling even with
          thousands of executions.
        </Text>
      </Card>
    </View>
  )
}

export default History