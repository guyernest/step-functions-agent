import { DynamoDBClient, GetItemCommand, PutItemCommand, QueryCommand } from '@aws-sdk/client-dynamodb';
import { LambdaClient, InvokeCommand } from '@aws-sdk/client-lambda';
import { SFNClient, StartExecutionCommand } from '@aws-sdk/client-sfn';

declare const process: { env: { 
  AWS_REGION?: string;
  TEST_EVENTS_TABLE_NAME?: string;
  TEST_RESULTS_TABLE_NAME?: string;
  TOOL_REGISTRY_TABLE_NAME?: string;
  AGENT_REGISTRY_TABLE_NAME?: string;
  ENV_NAME?: string;
}};

const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION });
const lambdaClient = new LambdaClient({ region: process.env.AWS_REGION });
const sfnClient = new SFNClient({ region: process.env.AWS_REGION });

interface ExecuteHealthTestInput {
  action: string;
  toolName?: string;
  agentName?: string;
  testEventId?: string;
  customInput?: any;
  prompt?: string;
  autoApprove?: boolean;
  providerOverride?: string;
  modelOverride?: string;
  resourceType?: string;
  resourceIds?: string[];
}

export const handler = async (event: any): Promise<any> => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  // Handle GraphQL context - determine action from field name
  let input: ExecuteHealthTestInput;
  
  if (event.info?.fieldName) {
    // Called from GraphQL resolver
    const args = event.arguments || {};
    
    switch (event.info.fieldName) {
      case 'executeToolTest':
        input = { 
          action: 'executeToolTest', 
          toolName: args.tool_name,  // Map GraphQL snake_case to camelCase
          testEventId: args.test_event_id,
          customInput: args.custom_input
        };
        break;
      case 'executeAgentTest':
        input = { 
          action: 'executeAgentTest',
          agentName: args.agent_name,  // Map GraphQL snake_case to camelCase
          prompt: args.prompt,
          autoApprove: args.auto_approve,
          providerOverride: args.provider_override,
          modelOverride: args.model_override
        };
        break;
      default:
        input = { action: event.info.fieldName, ...args };
    }
  } else if (event.fieldName) {
    // Alternative AppSync event structure
    const args = event.arguments || {};
    
    switch (event.fieldName) {
      case 'executeToolTest':
        input = { 
          action: 'executeToolTest', 
          toolName: args.tool_name,
          testEventId: args.test_event_id,
          customInput: args.custom_input
        };
        break;
      case 'executeAgentTest':
        input = { 
          action: 'executeAgentTest',
          agentName: args.agent_name,
          prompt: args.prompt,
          autoApprove: args.auto_approve,
          providerOverride: args.provider_override,
          modelOverride: args.model_override
        };
        break;
      default:
        input = { action: event.fieldName, ...args };
    }
  } else {
    // Direct invocation
    input = event.arguments || event;
  }

  try {
    switch (input.action) {
      case 'executeToolTest':
        return await executeToolTest(input);
      
      case 'executeAgentTest':
        return await executeAgentTest(input);
      
      case 'executeHealthCheck':
        return await executeHealthCheck(input);
      
      case 'discoverTestEvents':
        return await discoverTestEvents(input);
      
      default:
        throw new Error(`Unknown action: ${input.action}`);
    }
  } catch (error: any) {
    console.error('Error in executeHealthTest:', error);
    return {
      success: false,
      error: error.message || 'Unknown error occurred'
    };
  }
};

async function executeToolTest(input: ExecuteHealthTestInput) {
  const { toolName, testEventId, customInput } = input;
  
  if (!toolName) {
    throw new Error('Tool name is required');
  }

  // Get tool info from registry
  const toolInfo = await getToolInfo(toolName);
  if (!toolInfo) {
    throw new Error(`Tool ${toolName} not found in registry`);
  }

  // Get test event if specified
  let testInput = customInput;
  let testEvent: any = null;
  
  if (testEventId && !customInput) {
    console.log(`Fetching test event: resource_type=tool, id=${testEventId}`);
    testEvent = await getTestEvent('tool', toolName, testEventId);
    if (!testEvent) {
      throw new Error(`Test event ${testEventId} not found`);
    }
    console.log('Retrieved test event:', JSON.stringify(testEvent, null, 2));
    
    // Handle both string format (correct) and Map format (legacy)
    if (testEvent.input?.S) {
      // Correct format: input stored as string
      testInput = JSON.parse(testEvent.input.S);
      console.log('Parsed test input from string:', JSON.stringify(testInput, null, 2));
    } else if (testEvent.input?.M) {
      // Legacy format: input stored as DynamoDB Map
      console.log('WARNING: Test event stored in legacy Map format, converting...');
      testInput = convertDynamoDBMapToObject(testEvent.input.M);
      console.log('Converted test input from Map:', JSON.stringify(testInput, null, 2));
    } else {
      testInput = {};
      console.log('No input found in test event, using empty object');
    }
  }
  
  if (customInput) {
    // customInput comes as AWSJSON (already parsed from string)
    testInput = customInput;
    console.log('Using custom input:', JSON.stringify(testInput, null, 2));
  }

  // Prepare tool invocation payload
  const toolPayload = {
    name: toolName,
    id: `test_${Date.now()}`,
    input: testInput,
    _test_mode: true
  };
  
  console.log('Tool invocation payload:', JSON.stringify(toolPayload, null, 2));

  // Invoke tool Lambda
  const invokeCommand = new InvokeCommand({
    FunctionName: toolInfo.lambda_arn?.S,
    InvocationType: 'RequestResponse',
    Payload: JSON.stringify(toolPayload)
  });

  const startTime = Date.now();
  const invokeResponse = await lambdaClient.send(invokeCommand);
  const executionTime = Date.now() - startTime;

  // Parse response
  let result;
  if (invokeResponse.Payload) {
    const payloadStr = new TextDecoder().decode(invokeResponse.Payload);
    try {
      result = JSON.parse(payloadStr);
    } catch {
      result = payloadStr;
    }
  }

  // Validate result if test event has expected output
  let validationResult = null;
  let validationPassed = true;
  
  if (testEvent && testEvent.expected_output?.S) {
    const expectedOutput = JSON.parse(testEvent.expected_output.S || '{}');
    const validationType = testEvent.validation_type?.S || 'exact';
    const validationConfig = testEvent.validation_config?.S ? JSON.parse(testEvent.validation_config.S) : {};
    
    validationResult = await validateOutput(result, expectedOutput, validationType, validationConfig);
    validationPassed = validationResult.passed;
    
    console.log('Validation result:', JSON.stringify(validationResult, null, 2));
  }

  // Store test result
  await storeTestResult({
    test_event_id: testEventId || `${toolName}_custom`,
    resource_id: toolName,
    execution_time: executionTime,
    success: invokeResponse.StatusCode === 200 && validationPassed,
    output: result,
    metadata: {
      tool_name: toolName,
      lambda_arn: toolInfo.lambda_arn?.S,
      validation_result: validationResult
    }
  });

  return {
    success: invokeResponse.StatusCode === 200 && validationPassed,
    result,
    executionTime,
    testEventId: testEventId,
    validationResult
  };
}

async function executeAgentTest(input: ExecuteHealthTestInput) {
  const { agentName, prompt, autoApprove, providerOverride, modelOverride } = input;
  
  if (!agentName || !prompt) {
    throw new Error('Agent name and prompt are required');
  }

  // Get agent info from registry
  const agentInfo = await getAgentInfo(agentName);
  if (!agentInfo) {
    throw new Error(`Agent ${agentName} not found in registry`);
  }

  // Prepare execution input
  const executionInput = {
    messages: [
      {
        role: 'user',
        content: prompt
      }
    ],
    metadata: {
      test_mode: true,
      auto_approve: autoApprove || false,
      provider_override: providerOverride,
      model_override: modelOverride
    }
  };

  // Start Step Functions execution
  const startCommand = new StartExecutionCommand({
    stateMachineArn: agentInfo.state_machine_arn?.S,
    input: JSON.stringify(executionInput),
    name: `test_${agentName}_${Date.now()}`
  });

  const startTime = Date.now();
  const executionResponse = await sfnClient.send(startCommand);
  const executionTime = Date.now() - startTime;

  // Store test result
  await storeTestResult({
    test_event_id: `${agentName}_prompt_test`,
    resource_id: agentName,
    execution_time: executionTime,
    success: true,
    output: {
      execution_arn: executionResponse.executionArn,
      start_date: executionResponse.startDate
    },
    metadata: {
      agent_name: agentName,
      prompt: prompt,
      auto_approve: autoApprove
    }
  });

  return {
    success: true,
    executionArn: executionResponse.executionArn,
    executionTime,
    message: 'Agent test execution started'
  };
}

async function executeHealthCheck(input: ExecuteHealthTestInput) {
  const { resourceType, resourceIds } = input;
  
  const results: any[] = [];
  
  if (resourceType === 'tool' || !resourceType) {
    // Get all tools or specific tools
    const tools = resourceIds || await getAllTools();
    
    for (const toolName of tools) {
      // Get default test event for tool
      const testEvents = await getTestEventsForResource('tool', toolName);
      if (testEvents.length > 0) {
        const testResult = await executeToolTest({
          action: 'executeToolTest',
          toolName,
          testEventId: testEvents[0].id
        });
        results.push({
          resource: toolName,
          type: 'tool',
          ...testResult
        });
      }
    }
  }
  
  if (resourceType === 'agent' || !resourceType) {
    // Get all agents or specific agents
    const agents = resourceIds || await getAllAgents();
    
    for (const agentName of agents) {
      // Get default test prompt for agent
      const testEvents = await getTestEventsForResource('agent', agentName);
      if (testEvents.length > 0 && testEvents[0].input) {
        const testEvent = JSON.parse(testEvents[0].input);
        const testResult = await executeAgentTest({
          action: 'executeAgentTest',
          agentName,
          prompt: testEvent.prompt,
          autoApprove: true
        });
        results.push({
          resource: agentName,
          type: 'agent',
          ...testResult
        });
      }
    }
  }
  
  return {
    success: true,
    results,
    timestamp: new Date().toISOString()
  };
}

async function discoverTestEvents(input: any) {
  // This function would be called when a new tool is deployed
  // It would check standard locations for test events and register them
  // Implementation would depend on Lambda package structure
  
  return {
    success: true,
    message: 'Test event discovery not yet implemented'
  };
}

// Helper functions

async function getToolInfo(toolName: string) {
  const command = new GetItemCommand({
    TableName: process.env.TOOL_REGISTRY_TABLE_NAME,
    Key: {
      tool_name: { S: toolName }
    }
  });
  
  const response = await dynamoClient.send(command);
  return response.Item;
}

async function getAgentInfo(agentName: string) {
  const command = new QueryCommand({
    TableName: process.env.AGENT_REGISTRY_TABLE_NAME,
    KeyConditionExpression: 'agent_name = :name',
    ExpressionAttributeValues: {
      ':name': { S: agentName }
    },
    Limit: 1
  });
  
  const response = await dynamoClient.send(command);
  return response.Items?.[0];
}

async function getTestEvent(resourceType: string, resourceId: string, testEventId: string) {
  const command = new GetItemCommand({
    TableName: process.env.TEST_EVENTS_TABLE_NAME,
    Key: {
      resource_type: { S: resourceType },
      id: { S: testEventId }
    }
  });
  
  const response = await dynamoClient.send(command);
  return response.Item;
}

async function getTestEventsForResource(resourceType: string, resourceId: string) {
  const command = new QueryCommand({
    TableName: process.env.TEST_EVENTS_TABLE_NAME,
    KeyConditionExpression: 'resource_type = :type AND begins_with(id, :prefix)',
    ExpressionAttributeValues: {
      ':type': { S: resourceType },
      ':prefix': { S: `${resourceId}#` }
    }
  });
  
  const response = await dynamoClient.send(command);
  return (response.Items || []).map(item => ({
    id: item.id?.S,
    test_name: item.test_name?.S,
    input: item.input?.S,
    metadata: item.metadata?.S
  }));
}

async function storeTestResult(result: any) {
  const now = new Date();
  const ttl = Math.floor(now.getTime() / 1000) + (30 * 24 * 60 * 60); // 30 days
  
  const command = new PutItemCommand({
    TableName: process.env.TEST_RESULTS_TABLE_NAME,
    Item: {
      test_event_id: { S: result.test_event_id },
      executed_at: { S: now.toISOString() },
      resource_id: { S: result.resource_id },
      execution_time: { N: result.execution_time.toString() },
      success: { BOOL: result.success },
      output: { S: JSON.stringify(result.output) },
      metadata: { S: JSON.stringify(result.metadata || {}) },
      ttl: { N: ttl.toString() }
    }
  });
  
  await dynamoClient.send(command);
}

async function getAllTools(): Promise<string[]> {
  // Query tool registry for all tools
  // This is a simplified implementation
  return [];
}

async function getAllAgents(): Promise<string[]> {
  // Query agent registry for all agents
  // This is a simplified implementation
  return [];
}

// Validation function for different types of output validation
async function validateOutput(
  actual: any,
  expected: any,
  validationType: string,
  config: any = {}
): Promise<{ passed: boolean; message: string; details?: any }> {
  console.log(`Validating output with type: ${validationType}`);
  console.log('Actual:', JSON.stringify(actual, null, 2));
  console.log('Expected:', JSON.stringify(expected, null, 2));
  console.log('Config:', JSON.stringify(config, null, 2));

  // Parse expected if it's a JSON string
  let expectedValue = expected;
  if (typeof expected === 'string') {
    try {
      expectedValue = JSON.parse(expected);
    } catch {
      // Keep as string if not valid JSON
      expectedValue = expected;
    }
  }

  // Create string representations for comparison
  const actualStr = typeof actual === 'string' ? actual : JSON.stringify(actual);
  const expectedStr = typeof expectedValue === 'string' ? expectedValue : JSON.stringify(expectedValue);

  // For contains and regex, also search within JSON structure
  const getSearchableText = (obj: any): string => {
    if (typeof obj === 'string') return obj;
    if (typeof obj === 'number') return obj.toString();
    if (typeof obj === 'object' && obj !== null) {
      // Collect all string/number values from the object
      const values: string[] = [];
      const traverse = (o: any) => {
        for (const key in o) {
          const val = o[key];
          if (typeof val === 'string' || typeof val === 'number') {
            values.push(val.toString());
          } else if (typeof val === 'object' && val !== null) {
            traverse(val);
          }
        }
      };
      traverse(obj);
      return values.join(' ');
    }
    return JSON.stringify(obj);
  };

  switch (validationType) {
    case 'exact':
      // Exact match comparison - compare parsed values if both are objects
      let exactMatch = false;
      if (typeof actual === 'object' && typeof expectedValue === 'object') {
        exactMatch = JSON.stringify(actual) === JSON.stringify(expectedValue);
      } else {
        exactMatch = actualStr === expectedStr;
      }
      return {
        passed: exactMatch,
        message: exactMatch ? 'Exact match' : 'Output does not match expected value',
        details: { 
          actual: actualStr.substring(0, 500), 
          expected: expectedStr.substring(0, 500),
          validationType: 'exact'
        }
      };

    case 'contains':
      // Check if actual output contains the expected string
      // Search both in stringified form and within object values
      const searchableText = getSearchableText(actual);
      const contains = searchableText.includes(expectedStr) || actualStr.includes(expectedStr);
      return {
        passed: contains,
        message: contains ? 'Output contains expected value' : 'Output does not contain expected value',
        details: { 
          actual: actualStr.substring(0, 500), 
          expected: expectedStr,
          searchableText: searchableText.substring(0, 500),
          validationType: 'contains'
        }
      };

    case 'regex':
      // Regex pattern matching - search both stringified and within values
      try {
        const pattern = new RegExp(expectedStr, config.flags || 'g');
        const searchableText = getSearchableText(actual);
        const matches = pattern.test(searchableText) || pattern.test(actualStr);
        return {
          passed: matches,
          message: matches ? 'Pattern matched' : 'Pattern did not match',
          details: { 
            actual: actualStr.substring(0, 500), 
            pattern: expectedStr, 
            flags: config.flags || 'g',
            matchGroups: searchableText.match(pattern),
            validationType: 'regex'
          }
        };
      } catch (error: any) {
        return {
          passed: false,
          message: `Invalid regex pattern: ${error.message}`,
          details: { error: error.message, validationType: 'regex' }
        };
      }

    case 'schema':
      // JSON schema validation (simplified - you could use ajv library for full support)
      try {
        if (config.type === 'object' && typeof actual !== 'object') {
          return {
            passed: false,
            message: 'Expected object type',
            details: { actualType: typeof actual }
          };
        }
        
        if (config.required) {
          const missingFields = config.required.filter((field: string) => 
            !(field in (actual as any))
          );
          if (missingFields.length > 0) {
            return {
              passed: false,
              message: 'Missing required fields',
              details: { missingFields }
            };
          }
        }
        
        if (config.properties) {
          for (const prop in config.properties) {
            const propConfig = config.properties[prop];
            if (propConfig.type && prop in (actual as any)) {
              const actualType = typeof (actual as any)[prop];
              if (actualType !== propConfig.type) {
                return {
                  passed: false,
                  message: `Property ${prop} has wrong type`,
                  details: { property: prop, expected: propConfig.type, actual: actualType }
                };
              }
            }
          }
        }
        
        return {
          passed: true,
          message: 'Schema validation passed',
          details: { schema: config, validationType: 'schema' }
        };
      } catch (error: any) {
        return {
          passed: false,
          message: `Schema validation error: ${error.message}`,
          details: { error: error.message }
        };
      }

    case 'range':
      // Numeric range validation
      const actualNum = typeof actual === 'number' ? actual : parseFloat(actualStr);
      const expectedNum = typeof expected === 'number' ? expected : parseFloat(expectedStr);
      
      if (isNaN(actualNum)) {
        return {
          passed: false,
          message: 'Actual value is not a number',
          details: { actual: actualStr }
        };
      }
      
      const tolerance = config.tolerance || 0;
      const minValue = config.min !== undefined ? config.min : expectedNum - tolerance;
      const maxValue = config.max !== undefined ? config.max : expectedNum + tolerance;
      
      const inRange = actualNum >= minValue && actualNum <= maxValue;
      return {
        passed: inRange,
        message: inRange ? 'Value is within range' : 'Value is outside range',
        details: { actual: actualNum, min: minValue, max: maxValue }
      };

    case 'semantic':
      // Semantic similarity for LLM outputs (simplified - could use embeddings for better comparison)
      // For now, just check if key concepts are present
      if (config.concepts) {
        const actualLower = actualStr.toLowerCase();
        const missingConcepts = config.concepts.filter((concept: string) => 
          !actualLower.includes(concept.toLowerCase())
        );
        
        const passed = missingConcepts.length === 0;
        return {
          passed,
          message: passed ? 'All key concepts present' : 'Missing key concepts',
          details: { 
            concepts: config.concepts,
            missingConcepts,
            threshold: config.threshold || 0.8 
          }
        };
      }
      
      // Fallback to fuzzy string matching
      const similarity = calculateSimilarity(actualStr, expectedStr);
      const threshold = config.threshold || 0.8;
      const passed = similarity >= threshold;
      
      return {
        passed,
        message: `Similarity: ${(similarity * 100).toFixed(2)}%`,
        details: { similarity, threshold }
      };

    case 'ignore':
    case 'none':
      // No validation - always passes
      return {
        passed: true,
        message: 'Validation skipped',
        details: {}
      };

    default:
      // Default to exact match
      console.warn(`Unknown validation type: ${validationType}, defaulting to exact match`);
      const defaultMatch = actualStr === expectedStr;
      return {
        passed: defaultMatch,
        message: defaultMatch ? 'Exact match (default)' : 'Output does not match (default)',
        details: { actual: actualStr, expected: expectedStr }
      };
  }
}

// Simple string similarity calculation (Levenshtein distance based)
function calculateSimilarity(str1: string, str2: string): number {
  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;
  
  if (longer.length === 0) return 1.0;
  
  const distance = levenshteinDistance(longer, shorter);
  return (longer.length - distance) / longer.length;
}

// Levenshtein distance implementation
function levenshteinDistance(str1: string, str2: string): number {
  const matrix: number[][] = [];
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // substitution
          matrix[i][j - 1] + 1,     // insertion
          matrix[i - 1][j] + 1      // deletion
        );
      }
    }
  }
  
  return matrix[str2.length][str1.length];
}

// Helper function to convert DynamoDB Map to plain object
function convertDynamoDBMapToObject(map: any): any {
  const result: any = {};
  for (const key in map) {
    const value = map[key];
    if (value.S !== undefined) {
      result[key] = value.S;
    } else if (value.N !== undefined) {
      result[key] = parseFloat(value.N);
    } else if (value.BOOL !== undefined) {
      result[key] = value.BOOL;
    } else if (value.M !== undefined) {
      result[key] = convertDynamoDBMapToObject(value.M);
    } else if (value.L !== undefined) {
      result[key] = value.L.map((item: any) => {
        if (item.S !== undefined) return item.S;
        if (item.N !== undefined) return parseFloat(item.N);
        if (item.BOOL !== undefined) return item.BOOL;
        if (item.M !== undefined) return convertDynamoDBMapToObject(item.M);
        return item;
      });
    }
  }
  return result;
}