import { DynamoDBClient, GetItemCommand } from '@aws-sdk/client-dynamodb';
import { LambdaClient, InvokeCommand } from '@aws-sdk/client-lambda';
import { CloudWatchLogsClient, FilterLogEventsCommand } from '@aws-sdk/client-cloudwatch-logs';

declare const process: { env: { AWS_REGION?: string } };

const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION });
const lambdaClient = new LambdaClient({ region: process.env.AWS_REGION });
const logsClient = new CloudWatchLogsClient({ region: process.env.AWS_REGION });

interface TestToolInput {
  toolName: string;
  testInput: string;
  logLevel?: string;  // Add support for log level
}

export const handler = async (event: any): Promise<any> => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  try {
    // Handle both direct Lambda invocation and GraphQL AppSync context
    let toolName: string;
    let testInput: Record<string, any>;
    let logLevel: string = 'INFO';  // Default log level
    
    if (event.arguments) {
      // GraphQL AppSync context
      const args = event.arguments as TestToolInput;
      toolName = args.toolName;
      logLevel = args.logLevel || 'INFO';
      // Parse the JSON string
      try {
        const parsedInput = JSON.parse(args.testInput);
        
        // Check if the input is already wrapped in tool_use (from UI mistake)
        if (parsedInput.tool_use && parsedInput.tool_use.input) {
          console.log('Input already contains tool_use wrapper, extracting inner input');
          testInput = parsedInput.tool_use.input;
        } else {
          console.log('Using input as-is:', parsedInput);
          testInput = parsedInput;
        }
        console.log('Final testInput for validation:', testInput);
      } catch (e) {
        return {
          success: false,
          error: 'Invalid JSON in testInput parameter'
        };
      }
    } else {
      // Direct Lambda invocation
      ({ toolName, testInput } = event as { toolName: string; testInput: Record<string, any> });
      logLevel = event.logLevel || 'INFO';
    }
    
    if (!toolName) {
      return {
        success: false,
        error: 'Tool name is required'
      };
    }

    // Get tool information from Tool Registry
    const getItemCommand = new GetItemCommand({
      TableName: 'ToolRegistry-prod',
      Key: {
        tool_name: { S: toolName }
      }
    });

    const toolResponse = await dynamoClient.send(getItemCommand);
    
    if (!toolResponse.Item) {
      return {
        success: false,
        error: `Tool ${toolName} not found in registry`
      };
    }

    // Extract Lambda ARN and input schema
    const lambdaArn = toolResponse.Item.lambda_arn?.S;
    const inputSchemaStr = toolResponse.Item.input_schema?.S;
    
    if (!lambdaArn) {
      return {
        success: false,
        error: `Lambda ARN not found for tool ${toolName}`
      };
    }

    let inputSchema;
    try {
      inputSchema = inputSchemaStr ? JSON.parse(inputSchemaStr) : {};
    } catch (e) {
      console.error('Failed to parse input schema:', e);
      inputSchema = {};
    }

    // Validate input against schema (basic validation)
    const validationResult = validateInput(testInput, inputSchema);
    if (!validationResult.valid) {
      return {
        success: false,
        error: `Input validation failed: ${validationResult.error}`,
        schema: inputSchema
      };
    }

    // The Step Functions sends this directly as the Payload, and it works
    // The error says: tool_use['name'] - so the Lambda expects the event to have 'name'
    // Let's send exactly what Step Functions sends
    const toolPayload = {
      name: toolName,
      id: `toolu_test_${Date.now()}`, // Generate a test ID similar to Step Functions format
      input: testInput,
      // Include debug info for tools that support it
      _debug: {
        log_level: logLevel
      },
      _test_mode: true  // Flag to indicate this is a test invocation
    };
    
    console.log('Invoking tool with payload:', JSON.stringify(toolPayload, null, 2));
    console.log('Tool Lambda ARN:', lambdaArn);
    console.log('Log level:', logLevel);
    
    const invokeCommand = new InvokeCommand({
      FunctionName: lambdaArn,
      InvocationType: 'RequestResponse',
      Payload: JSON.stringify(toolPayload)
    });

    const startTime = Date.now();
    const invokeResponse = await lambdaClient.send(invokeCommand);
    const executionTime = Date.now() - startTime;

    // Parse the response
    let result;
    let isError = false;
    let requestId: string | undefined;
    
    if (invokeResponse.Payload) {
      const payloadStr = new TextDecoder().decode(invokeResponse.Payload);
      try {
        result = JSON.parse(payloadStr);
        // Check if this is an error response from the Lambda
        if (result.errorMessage || result.errorType) {
          isError = true;
          console.error('Tool Lambda returned an error:', result);
        }
        // Extract request ID from debug info if available
        if (result._debug && result._debug.request_id) {
          requestId = result._debug.request_id;
        }
      } catch (e) {
        result = payloadStr;
      }
    }

    // Query CloudWatch logs if we have a request ID and log level is DEBUG
    let logs: string[] = [];
    let cloudWatchUrl: string | undefined;
    
    if (requestId && logLevel === 'DEBUG') {
      try {
        // Extract function name from ARN
        const functionName = lambdaArn.split(':').pop() || lambdaArn;
        const logGroupName = `/aws/lambda/${functionName}`;
        
        // Wait a moment for logs to be available
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Query logs for this request
        const logCommand = new FilterLogEventsCommand({
          logGroupName,
          filterPattern: `"${requestId}"`,
          startTime: startTime - 5000, // 5 seconds before
          endTime: Date.now() + 5000, // 5 seconds after
          limit: 100
        });
        
        const logResponse = await logsClient.send(logCommand);
        
        if (logResponse.events) {
          logs = logResponse.events
            .filter(event => event.message)
            .map(event => event.message!);
        }
        
        // Generate CloudWatch Insights URL
        const region = process.env.AWS_REGION || 'us-west-2';
        const encodedQuery = encodeURIComponent(`fields @timestamp, @message | filter @requestId="${requestId}" | sort @timestamp desc`);
        cloudWatchUrl = `https://console.aws.amazon.com/cloudwatch/home?region=${region}#logsV2:logs-insights$3FqueryDetail$3D~(query~'${encodedQuery}~source~'${encodeURIComponent(logGroupName)})`;
        
      } catch (logError) {
        console.error('Failed to retrieve CloudWatch logs:', logError);
      }
    }

    return {
      success: !isError && invokeResponse.StatusCode === 200,
      toolName,
      input: testInput,
      output: result,
      executionTime,
      metadata: {
        lambdaArn,
        statusCode: invokeResponse.StatusCode,
        functionError: invokeResponse.FunctionError || (isError ? 'Unhandled' : undefined),
        logResult: invokeResponse.LogResult,
        requestId,
        logLevel
      },
      logs: logs.length > 0 ? logs : undefined,
      cloudWatchUrl,
      schema: inputSchema,
      error: isError ? (result.errorMessage || 'Tool execution failed') : undefined
    };

  } catch (error: any) {
    console.error('Error testing tool:', error);
    return {
      success: false,
      error: error.message || 'Unknown error occurred',
      details: error
    };
  }
};

// Basic input validation against JSON schema
function validateInput(input: any, schema: any): { valid: boolean; error?: string } {
  if (!schema || !schema.properties) {
    return { valid: true };
  }

  // Check required fields
  if (schema.required && Array.isArray(schema.required)) {
    for (const field of schema.required) {
      if (!(field in input)) {
        return { 
          valid: false, 
          error: `Missing required field: ${field}` 
        };
      }
    }
  }

  // Check field types
  for (const [field, fieldSchema] of Object.entries(schema.properties as Record<string, any>)) {
    if (field in input) {
      const value = input[field];
      const expectedType = fieldSchema.type;
      
      if (expectedType) {
        const actualType = Array.isArray(value) ? 'array' : typeof value;
        
        if (expectedType === 'number' && actualType === 'string') {
          // Try to parse as number
          if (isNaN(Number(value))) {
            return { 
              valid: false, 
              error: `Field ${field} must be a number` 
            };
          }
        } else if (expectedType === 'array' && !Array.isArray(value)) {
          return { 
            valid: false, 
            error: `Field ${field} must be an array` 
          };
        } else if (expectedType === 'object' && typeof value !== 'object') {
          return { 
            valid: false, 
            error: `Field ${field} must be an object` 
          };
        } else if (expectedType === 'string' && typeof value !== 'string') {
          return { 
            valid: false, 
            error: `Field ${field} must be a string` 
          };
        } else if (expectedType === 'boolean' && typeof value !== 'boolean') {
          return { 
            valid: false, 
            error: `Field ${field} must be a boolean` 
          };
        }
      }
    }
  }

  return { valid: true };
}