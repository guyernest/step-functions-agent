#!/usr/bin/env ts-node
/**
 * Backfill Execution Index Script
 *
 * This script populates the ExecutionIndex DynamoDB table with historical execution data
 * by querying the Step Functions API and writing to the index table.
 *
 * Usage:
 *   ts-node scripts/backfill-execution-index.ts [options]
 *
 * Options:
 *   --table-name <name>     DynamoDB table name (default: ExecutionIndex-prod)
 *   --days <number>         Number of days to backfill (default: 30)
 *   --dry-run               Show what would be written without actually writing
 *   --batch-size <number>   Number of items to write per batch (default: 25)
 */

import {
  SFNClient,
  ListStateMachinesCommand,
  ListExecutionsCommand,
  DescribeExecutionCommand,
  ListTagsForResourceCommand
} from '@aws-sdk/client-sfn';
import {
  DynamoDBClient,
  PutItemCommand,
  BatchWriteItemCommand
} from '@aws-sdk/client-dynamodb';

interface ExecutionRecord {
  executionArn: string;
  agentName: string;
  stateMachineArn: string;
  executionName: string;
  status: string;
  startDate: string;
  stopDate?: string;
  durationSeconds?: number;
  indexedAt: string;
}

// Parse command line arguments
const args = process.argv.slice(2);
const getArg = (flag: string, defaultValue: string): string => {
  const index = args.indexOf(flag);
  return index >= 0 && args[index + 1] ? args[index + 1] : defaultValue;
};

const TABLE_NAME = getArg('--table-name', 'ExecutionIndex-prod');
const DAYS_TO_BACKFILL = parseInt(getArg('--days', '30'));
const BATCH_SIZE = parseInt(getArg('--batch-size', '25'));
const DRY_RUN = args.includes('--dry-run');

const sfnClient = new SFNClient({ region: 'us-west-2' });
const dynamoClient = new DynamoDBClient({ region: 'us-west-2' });

// Statistics
let stats = {
  stateMachinesProcessed: 0,
  executionsFound: 0,
  agentExecutions: 0,
  nonAgentExecutions: 0,
  written: 0,
  errors: 0,
  skipped: 0
};

/**
 * Get agent name from state machine tags
 */
async function getAgentName(stateMachineArn: string): Promise<string | null> {
  try {
    const response = await sfnClient.send(
      new ListTagsForResourceCommand({
        resourceArn: stateMachineArn
      })
    );

    const tags = response.tags || [];
    const typeTag = tags.find(t => t.key === 'Type');
    const appTag = tags.find(t => t.key === 'Application');

    // Check if this is an agent state machine
    if (typeTag?.value === 'Agent' && appTag?.value === 'StepFunctionsAgent') {
      // Extract agent name from state machine name
      // Format: arn:aws:states:region:account:stateMachine:agent-name-prod
      const parts = stateMachineArn.split(':');
      const stateMachineName = parts[parts.length - 1];
      // Remove -prod or -dev suffix
      const agentName = stateMachineName.replace(/-prod$|-dev$/, '');
      return agentName;
    }

    return null;
  } catch (error) {
    console.error(`Error getting tags for ${stateMachineArn}:`, error);
    return null;
  }
}

/**
 * Convert execution to index record
 */
function executionToRecord(execution: any, agentName: string, stateMachineArn: string): ExecutionRecord {
  const startDate = new Date(execution.startDate);
  const stopDate = execution.stopDate ? new Date(execution.stopDate) : undefined;

  const record: ExecutionRecord = {
    executionArn: execution.executionArn,
    agentName,
    stateMachineArn,
    executionName: execution.name,
    status: execution.status,
    startDate: startDate.toISOString(),
    indexedAt: new Date().toISOString()
  };

  if (stopDate) {
    record.stopDate = stopDate.toISOString();
    record.durationSeconds = Math.floor((stopDate.getTime() - startDate.getTime()) / 1000);
  }

  return record;
}

/**
 * Write record to DynamoDB
 */
async function writeRecord(record: ExecutionRecord): Promise<boolean> {
  if (DRY_RUN) {
    console.log(`[DRY RUN] Would write:`, JSON.stringify(record, null, 2));
    return true;
  }

  try {
    const item: Record<string, any> = {
      executionArn: { S: record.executionArn },
      agentName: { S: record.agentName },
      stateMachineArn: { S: record.stateMachineArn },
      executionName: { S: record.executionName },
      status: { S: record.status },
      startDate: { S: record.startDate },
      indexedAt: { S: record.indexedAt }
    };

    if (record.stopDate) {
      item.stopDate = { S: record.stopDate };
    }

    if (record.durationSeconds !== undefined) {
      item.durationSeconds = { N: record.durationSeconds.toString() };
    }

    await dynamoClient.send(
      new PutItemCommand({
        TableName: TABLE_NAME,
        Item: item
      })
    );

    return true;
  } catch (error) {
    console.error(`Error writing record for ${record.executionArn}:`, error);
    return false;
  }
}

/**
 * Write records in batch
 */
async function writeBatch(records: ExecutionRecord[]): Promise<number> {
  if (DRY_RUN) {
    console.log(`[DRY RUN] Would write batch of ${records.length} records`);
    return records.length;
  }

  if (records.length === 0) return 0;

  // Split into chunks of 25 (DynamoDB batch limit)
  const chunks: ExecutionRecord[][] = [];
  for (let i = 0; i < records.length; i += 25) {
    chunks.push(records.slice(i, i + 25));
  }

  let written = 0;

  for (const chunk of chunks) {
    try {
      const putRequests = chunk.map(record => {
        const item: Record<string, any> = {
          executionArn: { S: record.executionArn },
          agentName: { S: record.agentName },
          stateMachineArn: { S: record.stateMachineArn },
          executionName: { S: record.executionName },
          status: { S: record.status },
          startDate: { S: record.startDate },
          indexedAt: { S: record.indexedAt }
        };

        if (record.stopDate) {
          item.stopDate = { S: record.stopDate };
        }

        if (record.durationSeconds !== undefined) {
          item.durationSeconds = { N: record.durationSeconds.toString() };
        }

        return {
          PutRequest: { Item: item }
        };
      });

      await dynamoClient.send(
        new BatchWriteItemCommand({
          RequestItems: {
            [TABLE_NAME]: putRequests
          }
        })
      );

      written += chunk.length;
    } catch (error) {
      console.error(`Error writing batch:`, error);
      stats.errors += chunk.length;
    }
  }

  return written;
}

/**
 * Process executions for a state machine
 */
async function processStateMachine(stateMachineArn: string): Promise<void> {
  console.log(`\nProcessing state machine: ${stateMachineArn}`);

  // Check if this is an agent
  const agentName = await getAgentName(stateMachineArn);

  if (!agentName) {
    console.log(`  Skipping: Not an agent state machine`);
    stats.nonAgentExecutions++;
    return;
  }

  console.log(`  Agent: ${agentName}`);

  // Calculate date range
  const now = new Date();
  const startDate = new Date(now);
  startDate.setDate(startDate.getDate() - DAYS_TO_BACKFILL);

  console.log(`  Fetching executions from ${startDate.toISOString()} to ${now.toISOString()}`);

  let nextToken: string | undefined;
  let executionCount = 0;
  const records: ExecutionRecord[] = [];

  do {
    try {
      const response = await sfnClient.send(
        new ListExecutionsCommand({
          stateMachineArn,
          maxResults: 100,
          nextToken
        })
      );

      const executions = response.executions || [];

      for (const execution of executions) {
        stats.executionsFound++;
        executionCount++;

        // Filter by date
        const execStartDate = new Date(execution.startDate!);
        if (execStartDate < startDate) {
          console.log(`  Reached executions older than ${DAYS_TO_BACKFILL} days, stopping`);
          nextToken = undefined;
          break;
        }

        // Convert to record
        const record = executionToRecord(execution, agentName, stateMachineArn);
        records.push(record);
        stats.agentExecutions++;

        // Write in batches
        if (records.length >= BATCH_SIZE) {
          const written = await writeBatch(records.splice(0, BATCH_SIZE));
          stats.written += written;
          console.log(`  Progress: ${executionCount} executions, ${stats.written} written`);
        }
      }

      nextToken = response.nextToken;

      if (!nextToken) {
        break;
      }
    } catch (error) {
      console.error(`Error listing executions:`, error);
      stats.errors++;
      break;
    }
  } while (nextToken);

  // Write remaining records
  if (records.length > 0) {
    const written = await writeBatch(records);
    stats.written += written;
  }

  console.log(`  Completed: ${executionCount} executions processed`);
}

/**
 * Main function
 */
async function main() {
  console.log('='.repeat(80));
  console.log('Execution Index Backfill Script');
  console.log('='.repeat(80));
  console.log(`Table: ${TABLE_NAME}`);
  console.log(`Days: ${DAYS_TO_BACKFILL}`);
  console.log(`Batch Size: ${BATCH_SIZE}`);
  console.log(`Dry Run: ${DRY_RUN}`);
  console.log('='.repeat(80));

  const startTime = Date.now();

  // List all state machines
  console.log('\nFetching state machines...');

  let nextToken: string | undefined;
  const stateMachines: string[] = [];

  do {
    try {
      const response = await sfnClient.send(
        new ListStateMachinesCommand({
          maxResults: 100,
          nextToken
        })
      );

      for (const sm of response.stateMachines || []) {
        stateMachines.push(sm.stateMachineArn!);
      }

      nextToken = response.nextToken;
    } catch (error) {
      console.error('Error listing state machines:', error);
      process.exit(1);
    }
  } while (nextToken);

  console.log(`Found ${stateMachines.length} state machines`);

  // Process each state machine
  for (const stateMachineArn of stateMachines) {
    await processStateMachine(stateMachineArn);
    stats.stateMachinesProcessed++;
  }

  const duration = ((Date.now() - startTime) / 1000).toFixed(2);

  // Print summary
  console.log('\n' + '='.repeat(80));
  console.log('Backfill Complete');
  console.log('='.repeat(80));
  console.log(`State machines processed: ${stats.stateMachinesProcessed}`);
  console.log(`Total executions found: ${stats.executionsFound}`);
  console.log(`Agent executions: ${stats.agentExecutions}`);
  console.log(`Non-agent executions: ${stats.nonAgentExecutions}`);
  console.log(`Records written: ${stats.written}`);
  console.log(`Errors: ${stats.errors}`);
  console.log(`Duration: ${duration}s`);
  console.log('='.repeat(80));

  if (DRY_RUN) {
    console.log('\n⚠️  This was a DRY RUN. No data was written to DynamoDB.');
    console.log('Remove --dry-run flag to actually write the data.');
  }
}

// Run the script
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});