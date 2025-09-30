import {
  SFNClient,
  ListExecutionsCommand,
  ListStateMachinesCommand,
  ListTagsForResourceCommand,
  ExecutionListItem
} from '@aws-sdk/client-sfn';

declare const process: { env: { AWS_REGION?: string } };

const client = new SFNClient({ region: process.env.AWS_REGION });

interface Execution {
  executionArn: string;
  stateMachineArn: string;
  name: string;
  status: string;
  startDate: string;
  stopDate?: string;
  agentName?: string;
}

interface PaginatedResponse {
  executions: Execution[];
  nextToken?: string;
  hasMore: boolean;
  totalCount?: number;
  metadata?: {
    fromCache: boolean;
    fetchTime: number;
  };
}

interface StateMachineMetadata {
  arn: string;
  agentName: string;
  tags: { key?: string; value?: string }[];
  lastUpdated: number;
}

// In-memory cache for state machine metadata (Lambda container reuse)
const stateMachineCache = new Map<string, StateMachineMetadata>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// Cache for state machine list
let cachedStateMachines: { arns: string[]; timestamp: number } | null = null;

async function getStateMachineMetadata(arn: string): Promise<StateMachineMetadata> {
  const cached = stateMachineCache.get(arn);
  if (cached && Date.now() - cached.lastUpdated < CACHE_TTL) {
    return cached;
  }

  try {
    const tagsCommand = new ListTagsForResourceCommand({ resourceArn: arn });
    const tagsResponse = await client.send(tagsCommand);
    const tags = tagsResponse.tags || [];

    const agentNameTag = tags.find(tag => tag.key === 'AgentName');
    const agentName = agentNameTag?.value || arn.split(':').pop() || 'unknown';

    const metadata: StateMachineMetadata = {
      arn,
      agentName,
      tags,
      lastUpdated: Date.now()
    };

    stateMachineCache.set(arn, metadata);
    return metadata;
  } catch (error) {
    console.error('Error fetching metadata for state machine:', arn, error);
    return {
      arn,
      agentName: arn.split(':').pop() || 'unknown',
      tags: [],
      lastUpdated: Date.now()
    };
  }
}

async function getAgentStateMachines(): Promise<string[]> {
  // Check cache first
  if (cachedStateMachines && Date.now() - cachedStateMachines.timestamp < CACHE_TTL) {
    return cachedStateMachines.arns;
  }

  const listSMCommand = new ListStateMachinesCommand({ maxResults: 1000 });
  const listSMResponse = await client.send(listSMCommand);

  // Parallel tag checking
  const checkPromises = (listSMResponse.stateMachines || [])
    .filter(sm => sm.stateMachineArn)
    .map(async (sm) => {
      const metadata = await getStateMachineMetadata(sm.stateMachineArn!);
      const hasAgentTag = metadata.tags.some(tag => tag.key === 'Type' && tag.value === 'Agent');
      const hasApplicationTag = metadata.tags.some(tag => tag.key === 'Application' && tag.value === 'StepFunctionsAgent');

      return (hasAgentTag && hasApplicationTag) ? sm.stateMachineArn : null;
    });

  const results = await Promise.all(checkPromises);
  const filteredArns = results.filter((arn): arn is string => arn !== null);

  // Update cache
  cachedStateMachines = { arns: filteredArns, timestamp: Date.now() };

  return filteredArns;
}

function parseNextToken(token?: string): { stateMachineIndex: number; executionToken?: string } | null {
  if (!token) return null;

  try {
    const decoded = Buffer.from(token, 'base64').toString('utf-8');
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

function createNextToken(stateMachineIndex: number, executionToken?: string): string {
  const tokenData = { stateMachineIndex, executionToken };
  return Buffer.from(JSON.stringify(tokenData)).toString('base64');
}

function filterByDateRange(executions: Execution[], startDateFrom?: string, startDateTo?: string): Execution[] {
  if (!startDateFrom && !startDateTo) return executions;

  return executions.filter(exec => {
    const execDate = new Date(exec.startDate).getTime();

    // For "from" date, start at beginning of day (00:00:00 UTC)
    const fromDate = startDateFrom ? new Date(startDateFrom + 'T00:00:00.000Z').getTime() : 0;

    // For "to" date, end at end of day (23:59:59.999 UTC)
    const toDate = startDateTo
      ? new Date(startDateTo + 'T23:59:59.999Z').getTime()
      : Date.now();

    return execDate >= fromDate && execDate <= toDate;
  });
}

export const handler = async (event: any): Promise<string> => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  const startTime = Date.now();

  try {
    const {
      stateMachineArn,
      status,
      maxResults = 50,
      nextToken,
      agentName,
      startDateFrom,
      startDateTo
    } = event.arguments || {};

    // Parse pagination token
    const tokenData = parseNextToken(nextToken);
    const startIndex = tokenData?.stateMachineIndex || 0;

    // Get state machines to query
    let stateMachineArns: string[] = [];

    if (stateMachineArn) {
      stateMachineArns = [stateMachineArn];
    } else {
      const allArns = await getAgentStateMachines();

      // Filter by agent name if provided
      if (agentName) {
        const filterPromises = allArns.map(async (arn) => {
          const metadata = await getStateMachineMetadata(arn);
          return metadata.agentName.toLowerCase().includes(agentName.toLowerCase()) ? arn : null;
        });

        const filtered = await Promise.all(filterPromises);
        stateMachineArns = filtered.filter((arn): arn is string => arn !== null);
      } else {
        // No agent filter specified - for efficiency, require agent filter or only fetch recent
        // To avoid iterating through too many state machines, we'll limit to recent executions
        // by sorting state machines by most recent activity
        console.log('No agent filter specified, will query all agent state machines');
        stateMachineArns = allArns;
      }
    }

    // If no state machines found, return empty
    if (stateMachineArns.length === 0) {
      console.log('No matching state machines found');
      const response = {
        executions: [],
        hasMore: false,
        totalCount: 0,
        metadata: {
          fromCache: cachedStateMachines !== null,
          fetchTime: Date.now() - startTime
        }
      };
      return JSON.stringify(response);
    }

    console.log(`Processing ${stateMachineArns.length} state machines starting from index ${startIndex}`);

    // If we have date filters and no specific agent, use a more efficient approach
    // Fetch more from each state machine to find matching dates
    const fetchMultiplier = (startDateFrom || startDateTo) ? 10 : 2;

    // Collect executions with pagination
    const allExecutions: Execution[] = [];
    let currentStateMachineIndex = startIndex;
    let currentExecutionToken = tokenData?.executionToken;
    let hasMoreExecutions = false;
    let totalFetched = 0;
    const MAX_ITERATIONS = 200; // Increase safety limit for date filtering

    // Process state machines starting from the pagination index
    while (currentStateMachineIndex < stateMachineArns.length && allExecutions.length < maxResults && totalFetched < MAX_ITERATIONS) {
      const arn = stateMachineArns[currentStateMachineIndex];
      const remainingResults = maxResults - allExecutions.length;

      // Get metadata for this state machine
      const metadata = await getStateMachineMetadata(arn);

      // Fetch more executions when using date filters to ensure we find matches
      const fetchSize = Math.min(1000, remainingResults * fetchMultiplier);

      // Fetch executions for this state machine
      const command = new ListExecutionsCommand({
        stateMachineArn: arn,
        statusFilter: status,
        maxResults: fetchSize,
        nextToken: currentExecutionToken
      });

      const response = await client.send(command);
      const executions = response.executions || [];
      totalFetched++;

      // Map executions with agent name
      const mappedExecutions = executions.map((exec: ExecutionListItem) => ({
        executionArn: exec.executionArn || '',
        stateMachineArn: exec.stateMachineArn || arn,
        name: exec.name || '',
        status: exec.status || 'UNKNOWN',
        startDate: exec.startDate?.toISOString() || '',
        stopDate: exec.stopDate?.toISOString(),
        agentName: metadata.agentName
      }));

      // Apply date range filter if provided
      const filteredExecutions = filterByDateRange(mappedExecutions, startDateFrom, startDateTo);

      // Add only what we need
      const toAdd = filteredExecutions.slice(0, remainingResults);
      allExecutions.push(...toAdd);

      console.log(`SM ${currentStateMachineIndex}: fetched=${executions.length}, filtered=${filteredExecutions.length}, added=${toAdd.length}, total=${allExecutions.length}, nextToken=${!!response.nextToken}`);

      // Check if we have enough results
      if (allExecutions.length >= maxResults) {
        // We have enough, but check if there might be more
        hasMoreExecutions = response.nextToken !== undefined || currentStateMachineIndex < stateMachineArns.length - 1;
        if (response.nextToken) {
          currentExecutionToken = response.nextToken;
        }
        break;
      }

      // Check if there are more executions in this state machine
      if (response.nextToken && executions.length > 0) {
        // Continue with next page of same state machine
        currentExecutionToken = response.nextToken;
      } else {
        // Move to next state machine
        currentStateMachineIndex++;
        currentExecutionToken = undefined;
      }
    }

    // Only set hasMore if we actually have results or potential for more
    if (!hasMoreExecutions && currentStateMachineIndex < stateMachineArns.length) {
      hasMoreExecutions = allExecutions.length > 0;
    }

    // Sort by start date (most recent first)
    allExecutions.sort((a, b) =>
      new Date(b.startDate).getTime() - new Date(a.startDate).getTime()
    );

    // Create next token if there are more results
    const responseNextToken = hasMoreExecutions
      ? createNextToken(currentStateMachineIndex, currentExecutionToken)
      : undefined;

    const fetchTime = Date.now() - startTime;

    console.log(`Returning ${allExecutions.length} executions, hasMore=${hasMoreExecutions}, nextToken=${!!responseNextToken}`);
    if (allExecutions.length > 0) {
      console.log(`First execution: ${JSON.stringify(allExecutions[0])}`);
      console.log(`Last execution: ${JSON.stringify(allExecutions[allExecutions.length - 1])}`);
    }

    const response = {
      executions: allExecutions,
      nextToken: responseNextToken,
      hasMore: hasMoreExecutions,
      totalCount: allExecutions.length,
      metadata: {
        fromCache: cachedStateMachines !== null,
        fetchTime
      }
    };

    // Return as JSON string for AppSync AWSJSON type
    return JSON.stringify(response);
  } catch (error) {
    console.error('Error listing executions:', error);
    const errorResponse = {
      executions: [],
      hasMore: false,
      metadata: {
        fromCache: false,
        fetchTime: Date.now() - startTime
      }
    };
    // Return as JSON string for AppSync AWSJSON type
    return JSON.stringify(errorResponse);
  }
};