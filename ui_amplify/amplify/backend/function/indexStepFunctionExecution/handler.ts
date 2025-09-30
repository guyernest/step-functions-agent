import {
  DynamoDBClient,
  PutItemCommand,
  DeleteItemCommand,
} from '@aws-sdk/client-dynamodb';
import {
  SFNClient,
  ListTagsForResourceCommand,
} from '@aws-sdk/client-sfn';

const dynamoClient = new DynamoDBClient({});
const sfnClient = new SFNClient({});

const TABLE_NAME = process.env.EXECUTION_INDEX_TABLE_NAME || 'ExecutionIndex';

interface StepFunctionsEvent {
  detail: {
    executionArn: string;
    stateMachineArn: string;
    name: string;
    status: string;
    startDate: number;
    stopDate?: number;
  };
}

async function getAgentName(stateMachineArn: string): Promise<string | null> {
  try {
    const command = new ListTagsForResourceCommand({ resourceArn: stateMachineArn });
    const response = await sfnClient.send(command);
    const tags = response.tags || [];

    // Check if this is an agent state machine
    const hasAgentTag = tags.some(tag => tag.key === 'Type' && tag.value === 'Agent');
    const hasApplicationTag = tags.some(tag => tag.key === 'Application' && tag.value === 'StepFunctionsAgent');

    if (!hasAgentTag || !hasApplicationTag) {
      return null; // Not an agent state machine, skip indexing
    }

    // Get agent name from tags
    const agentNameTag = tags.find(tag => tag.key === 'AgentName');
    return agentNameTag?.value || stateMachineArn.split(':').pop() || 'unknown';
  } catch (error) {
    console.error('Error fetching state machine tags:', error);
    return stateMachineArn.split(':').pop() || 'unknown';
  }
}

export const handler = async (event: StepFunctionsEvent) => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  const { executionArn, stateMachineArn, name, status, startDate, stopDate } = event.detail;

  // Get agent name from state machine tags
  const agentName = await getAgentName(stateMachineArn);

  if (!agentName) {
    console.log('Not an agent state machine, skipping index');
    return { statusCode: 200, body: 'Skipped (not an agent)' };
  }

  const startDateIso = new Date(startDate).toISOString();

  try {
    // Build the item with executionArn as primary key
    const item: Record<string, any> = {
      executionArn: { S: executionArn },
      agentName: { S: agentName },
      stateMachineArn: { S: stateMachineArn },
      executionName: { S: name },
      status: { S: status },
      startDate: { S: startDateIso },
    };

    // Add stopDate for terminal states
    if (stopDate && ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED'].includes(status)) {
      const stopDateIso = new Date(stopDate).toISOString();
      item.stopDate = { S: stopDateIso };

      // Calculate duration in seconds
      const durationSeconds = Math.floor((stopDate - startDate) / 1000);
      item.durationSeconds = { N: durationSeconds.toString() };
    }

    // Add timestamp for when this index entry was created/updated
    item.indexedAt = { S: new Date().toISOString() };

    const putCommand = new PutItemCommand({
      TableName: TABLE_NAME,
      Item: item,
    });

    await dynamoClient.send(putCommand);

    const action = status === 'RUNNING' ? 'Indexed execution start' : `Updated execution to ${status}`;
    console.log(`${action}:`, executionArn, {
      agent: agentName,
      status,
      startDate: startDateIso,
      ...(item.stopDate && { stopDate: item.stopDate.S }),
      ...(item.durationSeconds && { duration: `${item.durationSeconds.N}s` }),
    });

    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Indexed successfully',
        executionArn,
        agentName,
        status,
      })
    };
  } catch (error) {
    console.error('Error indexing execution:', error);
    // Log but don't fail - we don't want to block Step Functions execution
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error indexing execution',
        error: error instanceof Error ? error.message : 'Unknown error',
      }),
    };
  }
};