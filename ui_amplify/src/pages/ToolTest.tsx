import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { generateClient } from 'aws-amplify/data';
import { Schema } from '../../amplify/data/resource';
import {
  Card,
  Heading,
  Text,
  View,
  Flex,
  Button,
  Alert,
  SelectField,
  TextAreaField,
  Badge,
  Divider,
  TextField
} from '@aws-amplify/ui-react';

const client = generateClient<Schema>();

interface ToolInfo {
  id: string;
  name: string;
  description?: string;
  lambda_arn?: string;
  lambda_function_name?: string;
  language?: string;
  inputSchema?: any;
}

interface TestResult {
  success: boolean;
  result?: string;  // Raw result from the Lambda
  output?: any;  // Parsed result for display
  error?: string;
  executionTime?: number;
  testEventId?: string;
  executionArn?: string;
  message?: string;
  metadata?: {
    lambdaArn?: string;
    statusCode?: number;
    functionError?: string;
    requestId?: string;
    logLevel?: string;
  };
  logs?: string[];
  cloudWatchUrl?: string;
  validationResult?: {
    passed: boolean;
    message: string;
    details?: any;
  };
}

interface TestEvent {
  id: string;
  resource_type: string;
  resource_id: string;
  test_name: string;
  description?: string | null;
  test_input: string;  // AWSJSON - comes as a JSON string
  expected_output?: string | null;  // AWSJSON - comes as a JSON string
  metadata?: string | null;  // AWSJSON - comes as a JSON string
  created_at?: string | null;
  updated_at?: string | null;
}

export default function ToolTest() {
  const [searchParams] = useSearchParams();
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [testInput, setTestInput] = useState('{}');
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [inputSchema, setInputSchema] = useState<any>(null);
  const [logLevel, setLogLevel] = useState<string>('INFO');
  const [testEvents, setTestEvents] = useState<TestEvent[]>([]);
  const [selectedTestEvent, setSelectedTestEvent] = useState<string>('');
  const [showSaveTestModal, setShowSaveTestModal] = useState(false);
  const [newTestName, setNewTestName] = useState('');
  const [newTestDescription, setNewTestDescription] = useState('');
  const [validationType, setValidationType] = useState('exact');
  const [validationConfig, setValidationConfig] = useState('{}');
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [updateValidationType, setUpdateValidationType] = useState('exact');
  const [updateValidationConfig, setUpdateValidationConfig] = useState('{}');
  const [updateExpectedOutput, setUpdateExpectedOutput] = useState('');
  const [previewValidationResult, setPreviewValidationResult] = useState<{ passed: boolean; message: string } | null>(null);

  useEffect(() => {
    loadTools();
  }, []);

  useEffect(() => {
    // Check if a tool was specified in the URL
    const toolParam = searchParams.get('tool');
    if (toolParam && tools.length > 0) {
      const tool = tools.find(t => t.name === toolParam);
      if (tool) {
        setSelectedTool(toolParam);
        handleToolSelection(toolParam);
      }
    }
  }, [searchParams, tools]);

  const loadTools = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await client.queries.listToolsFromRegistry({});
      if (response.data) {
        // Filter out null/undefined values and map to ToolInfo type
        const validTools = response.data
          .filter((tool): tool is NonNullable<typeof tool> => tool !== null && tool !== undefined)
          .map(tool => ({
            id: tool.id,
            name: tool.name,
            description: tool.description || undefined,
            lambda_arn: tool.lambda_arn || undefined,
            lambda_function_name: tool.lambda_function_name || undefined,
            language: tool.language || undefined,
            inputSchema: tool.inputSchema || undefined,
          }));
        setTools(validTools);
      }
    } catch (err) {
      console.error('Error loading tools:', err);
      setError('Failed to load tools from registry');
    } finally {
      setLoading(false);
    }
  };

  const loadTestEvents = async (toolName: string) => {
    try {
      const response = await client.queries.listTestEvents({
        resource_type: 'tool',
        resource_id: toolName
      });
      
      if (response.data) {
        const events = response.data
          .filter((event): event is NonNullable<typeof event> => event !== null && event !== undefined)
          .map(event => ({
            ...event,
            description: event.description || null,
            expected_output: event.expected_output || null,
            metadata: event.metadata || null,
            created_at: event.created_at || null,
            updated_at: event.updated_at || null
          } as TestEvent));
        setTestEvents(events);
      }
    } catch (err) {
      console.error('Error loading test events:', err);
      // Don't show error - test events are optional
    }
  };

  const handleToolSelection = async (toolName: string) => {
    setTestResult(null);
    setError(null);
    setSelectedTestEvent('');
    setTestEvents([]);
    
    // Load test events for this tool
    await loadTestEvents(toolName);
    
    // Try to get input schema from tool
    const tool = tools.find(t => t.name === toolName);
    console.log('Selected tool:', tool);
    console.log('Tool inputSchema:', tool?.inputSchema);
    
    if (tool) {
      // Parse input_schema if it exists (it might be stored as a string in DynamoDB)
      try {
        if (typeof tool.inputSchema === 'string') {
          const schema = JSON.parse(tool.inputSchema);
          console.log('Parsed schema:', schema);
          setInputSchema(schema);
          // Generate example input based on schema
          const exampleInput = generateExampleFromSchema(schema);
          setTestInput(JSON.stringify(exampleInput, null, 2));
        } else if (tool.inputSchema) {
          console.log('Schema is object:', tool.inputSchema);
          setInputSchema(tool.inputSchema);
          const exampleInput = generateExampleFromSchema(tool.inputSchema);
          setTestInput(JSON.stringify(exampleInput, null, 2));
        } else {
          console.log('No input schema found for tool');
          setInputSchema(null);
          setTestInput('{}');
        }
      } catch (e) {
        console.error('Error parsing input schema:', e);
        setInputSchema(null);
        setTestInput('{}');
      }
    }
  };

  const handleToolChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const toolName = e.target.value;
    setSelectedTool(toolName);
    handleToolSelection(toolName);
  };

  const generateExampleFromSchema = (schema: any): any => {
    if (!schema || !schema.properties) {
      return {};
    }

    const example: any = {};
    
    for (const [key, prop] of Object.entries(schema.properties as Record<string, any>)) {
      if (prop.type === 'string') {
        example[key] = prop.example || prop.default || `example_${key}`;
      } else if (prop.type === 'number' || prop.type === 'integer') {
        example[key] = prop.example || prop.default || 0;
      } else if (prop.type === 'boolean') {
        example[key] = prop.example || prop.default || false;
      } else if (prop.type === 'array') {
        example[key] = prop.example || [];
      } else if (prop.type === 'object') {
        example[key] = prop.example || {};
      }
    }
    
    return example;
  };

  const handleTestEventChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const testEventId = e.target.value;
    setSelectedTestEvent(testEventId);
    
    if (testEventId) {
      const testEvent = testEvents.find(t => t.id === testEventId);
      if (testEvent) {
        // test_input is already a JSON string from AWSJSON type
        const parsedInput = typeof testEvent.test_input === 'string' 
          ? testEvent.test_input 
          : JSON.stringify(testEvent.test_input, null, 2);
        setTestInput(parsedInput);
      }
    }
  };

  const handleSaveTestEvent = async () => {
    if (!selectedTool || !newTestName) {
      setError('Tool and test name are required');
      return;
    }

    try {
      let parsedInput;
      try {
        parsedInput = JSON.parse(testInput || '{}');
      } catch (e) {
        setError('Invalid JSON input');
        return;
      }

      // Parse validation config if needed
      let parsedConfig = null;
      if (validationType !== 'exact' && validationType !== 'ignore') {
        try {
          parsedConfig = JSON.parse(validationConfig || '{}');
        } catch (e) {
          setError('Invalid validation configuration JSON');
          return;
        }
      }

      // Handle expected output formatting for AWSJSON
      let formattedExpectedOutput = null;
      if (testResult?.success) {
        const outputValue = testResult.result || testResult.output;
        if (typeof outputValue === 'string') {
          // If already a string, check if it's valid JSON
          try {
            JSON.parse(outputValue);
            formattedExpectedOutput = outputValue; // Already valid JSON string
          } catch {
            // Not valid JSON, so JSON-encode the string
            formattedExpectedOutput = JSON.stringify(outputValue);
          }
        } else {
          // It's an object/array/number, stringify it
          formattedExpectedOutput = JSON.stringify(outputValue);
        }
      }

      const response = await client.mutations.saveTestEvent({
        resource_type: 'tool',
        resource_id: selectedTool,
        test_name: newTestName,
        description: newTestDescription || null,
        test_input: JSON.stringify(parsedInput),  // Renamed from 'input' to avoid GraphQL conflicts
        validation_type: validationType,
        validation_config: parsedConfig ? JSON.stringify(parsedConfig) : null,
        expected_output: formattedExpectedOutput,
        metadata: JSON.stringify({
          saved_from_test: true,
          execution_time: testResult?.executionTime || null,
          saved_at: new Date().toISOString()
        })
      });

      if (response.data) {
        // Reload test events
        await loadTestEvents(selectedTool);
        setShowSaveTestModal(false);
        setNewTestName('');
        setNewTestDescription('');
        setValidationType('exact');
        setValidationConfig('{}');
        setError(null);
        // Show success message
        setSuccess(`Test event "${newTestName}" saved successfully!`);
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      console.error('Error saving test event:', err);
      setError('Failed to save test event');
    }
  };

  const handleTest = async () => {
    if (!selectedTool) {
      setError('Please select a tool to test');
      return;
    }

    try {
      setTesting(true);
      setError(null);
      setTestResult(null);

      // Validate JSON input
      let parsedInput;
      try {
        parsedInput = JSON.parse(testInput);
      } catch (e) {
        setError('Invalid JSON input');
        return;
      }

      // Call the test execution Lambda
      console.log('Calling executeToolTest with:', {
        tool_name: selectedTool,
        test_event_id: selectedTestEvent || undefined,
        custom_input: !selectedTestEvent ? parsedInput : undefined,
      });
      
      const response = await client.mutations.executeToolTest({
        tool_name: selectedTool,
        test_event_id: selectedTestEvent || undefined,
        custom_input: !selectedTestEvent ? JSON.stringify(parsedInput) : undefined,
      });
      
      console.log('Response from testToolExecution:', response);
      console.log('Response data type:', typeof response.data);
      console.log('Response data:', response.data);

      if (response.data) {
        // The response comes back with executeToolTest property
        let dataToProcess: any = response.data;
        
        // Check for executeToolTest property (the actual mutation name)
        if (response.data && typeof response.data === 'object' && 'executeToolTest' in response.data) {
          dataToProcess = (response.data as any).executeToolTest;
        }
        
        // Now process the result
        let result;
        if (typeof dataToProcess === 'string') {
          try {
            result = JSON.parse(dataToProcess);
            console.log('Parsed test result:', result);
          } catch (e) {
            console.error('Failed to parse response:', e);
            // If it's not JSON, use it as is
            result = dataToProcess;
          }
        } else {
          result = dataToProcess;
          console.log('Test result:', result);
        }
        
        // Parse the nested result if it's a string
        if (result.result && typeof result.result === 'string') {
          try {
            result.output = JSON.parse(result.result);
          } catch (e) {
            // If parsing fails, use as is
            result.output = result.result;
          }
        }
        
        console.log('Setting test result:', result);
        setTestResult(result as TestResult);
      } else if (response.errors) {
        const errorMessage = response.errors[0]?.message;
        setError(typeof errorMessage === 'string' ? errorMessage : 'Test execution failed');
      }
    } catch (err) {
      console.error('Error testing tool:', err);
      setError(err instanceof Error ? err.message : 'Failed to test tool');
    } finally {
      setTesting(false);
    }
  };

  const formatJson = () => {
    try {
      const parsed = JSON.parse(testInput);
      setTestInput(JSON.stringify(parsed, null, 2));
      setError(null);
    } catch (e) {
      setError('Invalid JSON - cannot format');
    }
  };

  const selectedToolInfo = tools.find(t => t.name === selectedTool);

  return (
    <View padding="1rem">
      <Card>
        <Heading level={2}>Tool Testing Interface</Heading>
        <Text marginBottom="1rem">Test tools with custom input and view real-time results</Text>
        
        {error && (
          <Alert variation="error" isDismissible onDismiss={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert variation="success" isDismissible onDismiss={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        <Flex direction="column" gap="1rem">
          <SelectField
            label="Select Tool"
            descriptiveText="Choose a tool from the registry to test"
            value={selectedTool}
            onChange={handleToolChange}
            disabled={loading}
          >
            <option value="">Select a tool...</option>
            {tools
              .sort((a, b) => a.name.localeCompare(b.name))
              .map(tool => (
                <option key={tool.name} value={tool.name}>
                  {tool.name} {tool.language && `(${tool.language})`}
                </option>
              ))}
          </SelectField>

          {selectedTool && selectedToolInfo && (
            <>
              <Card variation="outlined">
                <Heading level={4}>Tool Details</Heading>
                <Flex direction="column" gap="0.5rem">
                  <Text><strong>Name:</strong> {selectedToolInfo.name}</Text>
                  {selectedToolInfo.description && (
                    <Text><strong>Description:</strong> {selectedToolInfo.description}</Text>
                  )}
                  {selectedToolInfo.language && (
                    <Text><strong>Language:</strong> <Badge>{selectedToolInfo.language}</Badge></Text>
                  )}
                  {selectedToolInfo.lambda_function_name && (
                    <Text fontSize="small"><strong>Lambda:</strong> {selectedToolInfo.lambda_function_name}</Text>
                  )}
                </Flex>
              </Card>

              <Flex direction="column" gap="0.5rem">
                <Flex justifyContent="space-between" alignItems="center">
                  <Text fontWeight="bold">Test Events</Text>
                  <Button 
                    size="small" 
                    onClick={() => {
                      // Ensure we have valid JSON before opening modal
                      if (!testInput || testInput.trim() === '' || testInput.trim() === '{}') {
                        // Set example input if empty or just {}
                        try {
                          const example = inputSchema && inputSchema.properties ? generateExampleFromSchema(inputSchema) : {};
                          setTestInput(JSON.stringify(example, null, 2));
                        } catch (err) {
                          console.error('Error generating example:', err);
                          // Use empty object as fallback
                          setTestInput('{}');
                        }
                      } else {
                        // Try to format existing input
                        try {
                          const parsed = JSON.parse(testInput);
                          setTestInput(JSON.stringify(parsed, null, 2));
                        } catch (e) {
                          setError('Please enter valid JSON in the Test Input field before adding a test event');
                          return;
                        }
                      }
                      setShowSaveTestModal(true);
                    }}
                    isDisabled={!selectedTool}
                  >
                    Add Test Event
                  </Button>
                </Flex>
                {testEvents.length > 0 ? (
                  <Flex direction="column" gap="0.5rem">
                    <SelectField
                      label=""
                      descriptiveText="Select a predefined test event or create custom input below"
                      value={selectedTestEvent}
                      onChange={handleTestEventChange}
                    >
                      <option value="">Custom input</option>
                      {testEvents.map(event => (
                        <option key={event.id} value={event.id}>
                          {event.test_name} {event.description && `- ${event.description}`}
                        </option>
                      ))}
                    </SelectField>
                    {selectedTestEvent && (
                      <Button
                        size="small"
                        variation="warning"
                        onClick={async () => {
                          if (window.confirm(`Delete test event "${testEvents.find(t => t.id === selectedTestEvent)?.test_name}"?`)) {
                            try {
                              await client.mutations.deleteTestEvent({
                                resource_type: 'tool',
                                id: selectedTestEvent
                              });
                              await loadTestEvents(selectedTool);
                              setSelectedTestEvent('');
                            } catch (err) {
                              console.error('Error deleting test event:', err);
                              setError('Failed to delete test event');
                            }
                          }
                        }}
                      >
                        Delete Selected Test Event
                      </Button>
                    )}
                  </Flex>
                ) : (
                  <Alert variation="info">
                    No test events saved for this tool. Create one using the "Add Test Event" button.
                  </Alert>
                )}
              </Flex>

              {inputSchema && inputSchema.properties && (
                <Card variation="outlined">
                  <Heading level={4}>Input Parameters</Heading>
                  <Flex direction="column" gap="0.5rem">
                    {Object.entries(inputSchema.properties as Record<string, any>).map(([key, prop]) => (
                      <View key={key} padding="0.5rem" backgroundColor="rgba(0,0,0,0.02)" borderRadius="4px">
                        <Flex direction="column" gap="0.25rem">
                          <Flex alignItems="center" gap="0.5rem">
                            <Text fontWeight="bold">{key}</Text>
                            {inputSchema.required?.includes(key) && (
                              <Badge variation="error" size="small">Required</Badge>
                            )}
                            <Badge size="small">{prop.type}</Badge>
                          </Flex>
                          {prop.description && (
                            <Text fontSize="small" color="gray">{prop.description}</Text>
                          )}
                          {prop.default !== undefined && (
                            <Text fontSize="small" color="gray">Default: {JSON.stringify(prop.default)}</Text>
                          )}
                          {prop.enum && (
                            <Text fontSize="small" color="gray">Allowed values: {prop.enum.join(', ')}</Text>
                          )}
                        </Flex>
                      </View>
                    ))}
                  </Flex>
                </Card>
              )}

              <Flex direction="column" gap="0.5rem">
                <Flex justifyContent="space-between" alignItems="center">
                  <Text fontWeight="bold">Test Input (JSON)</Text>
                  <Button size="small" onClick={formatJson}>
                    Format JSON
                  </Button>
                </Flex>
                <Text fontSize="small" color="gray">
                  Enter only the tool's input parameters as JSON
                </Text>
                <TextAreaField
                  label=""
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  rows={10}
                  placeholder={inputSchema ? JSON.stringify(generateExampleFromSchema(inputSchema), null, 2) : '{}'}
                  style={{ fontFamily: 'monospace' }}
                />
              </Flex>

              <SelectField
                label="Log Level"
                descriptiveText="Set the logging level for detailed debugging"
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value)}
              >
                <option value="ERROR">ERROR - Only errors</option>
                <option value="WARNING">WARNING - Errors and warnings</option>
                <option value="INFO">INFO - Standard logging (default)</option>
                <option value="DEBUG">DEBUG - Detailed debugging with CloudWatch logs</option>
              </SelectField>

              <Button
                variation="primary"
                onClick={handleTest}
                isLoading={testing}
                isDisabled={testing || !selectedTool}
              >
                {testing ? 'Testing...' : 'Test Tool'}
              </Button>
            </>
          )}

          {testResult && (
            <>
              <Divider />
              <Card variation={testResult.success ? 'outlined' : 'elevated'}>
                <Heading level={4}>Test Results</Heading>
                
                <Alert variation={testResult.success ? 'success' : 'error'}>
                  {testResult.success 
                    ? (testResult.validationResult 
                        ? `Test ${testResult.validationResult.passed ? 'passed' : 'failed'}: ${testResult.validationResult.message}${testResult.executionTime ? ` (${testResult.executionTime}ms)` : ''}`
                        : `Test successful${testResult.executionTime ? ` - Execution time: ${testResult.executionTime}ms` : ''}`)
                    : testResult.error || 'Test failed'}
                </Alert>
                
                {/* Show validation details if present */}
                {testResult.validationResult && (
                  <Card variation="outlined" marginTop="1rem" backgroundColor={testResult.validationResult.passed ? "rgba(0,255,0,0.05)" : "rgba(255,0,0,0.05)"}>
                    <Heading level={5}>Validation Details</Heading>
                    <Flex direction="column" gap="0.5rem" marginTop="0.5rem">
                      <Text>
                        <strong>Validation Type:</strong> {testResult.validationResult.details?.validationType || 'Unknown'}
                      </Text>
                      {testResult.validationResult.details?.expected !== undefined && (
                        <View>
                          <Text fontWeight="bold">Expected:</Text>
                          <View backgroundColor="rgba(0,0,0,0.05)" padding="0.5rem" borderRadius="4px">
                            <pre style={{ margin: 0, fontSize: '11px', fontFamily: 'monospace' }}>
                              {testResult.validationResult.details.expected}
                            </pre>
                          </View>
                        </View>
                      )}
                      {testResult.validationResult.details?.actual !== undefined && (
                        <View>
                          <Text fontWeight="bold">Actual:</Text>
                          <View backgroundColor="rgba(0,0,0,0.05)" padding="0.5rem" borderRadius="4px">
                            <pre style={{ margin: 0, fontSize: '11px', fontFamily: 'monospace' }}>
                              {testResult.validationResult.details.actual}
                            </pre>
                          </View>
                        </View>
                      )}
                    </Flex>
                  </Card>
                )}

                {testResult.output && (
                  <>
                    {testResult.output.type === 'tool_result' && (
                      <View marginTop="1rem">
                        <Text fontWeight="bold" marginBottom="0.5rem">Tool Response:</Text>
                        <Flex direction="column" gap="0.25rem">
                          <Text fontSize="small">
                            Type: <Badge>{testResult.output.type}</Badge>
                          </Text>
                          <Text fontSize="small">
                            Tool: <Badge>{testResult.output.name}</Badge>
                          </Text>
                          <Text fontSize="small">
                            Tool Use ID: <code style={{ fontSize: '11px' }}>{testResult.output.tool_use_id}</code>
                          </Text>
                        </Flex>
                      </View>
                    )}
                    
                    <View marginTop="1rem">
                      <Text fontWeight="bold" marginBottom="0.5rem">Output Data:</Text>
                      <View backgroundColor="rgba(0,0,0,0.05)" padding="0.5rem" borderRadius="4px">
                        <pre style={{ margin: 0, fontSize: '12px', overflow: 'auto' }}>
                          {(() => {
                            // Check if output has the tool result format
                            if (testResult.output.content) {
                              // Parse the content if it's a JSON string
                              try {
                                const content = typeof testResult.output.content === 'string' 
                                  ? JSON.parse(testResult.output.content)
                                  : testResult.output.content;
                                return JSON.stringify(content, null, 2);
                              } catch {
                                return testResult.output.content;
                              }
                            }
                            // Otherwise show the full output
                            return typeof testResult.output === 'string'
                              ? testResult.output
                              : JSON.stringify(testResult.output, null, 2);
                          })()}
                        </pre>
                      </View>
                    </View>
                  </>
                )}

                {testResult.metadata && (
                  <View marginTop="1rem">
                    <Text fontWeight="bold" marginBottom="0.5rem">Execution Metadata:</Text>
                    <Flex direction="column" gap="0.25rem">
                      {testResult.metadata.statusCode && (
                        <Text fontSize="small">
                          Status Code: <Badge>{testResult.metadata.statusCode}</Badge>
                        </Text>
                      )}
                      {testResult.metadata.functionError && (
                        <Text fontSize="small">
                          Function Error: <Badge variation="error">{testResult.metadata.functionError}</Badge>
                        </Text>
                      )}
                      {testResult.metadata.lambdaArn && (
                        <Text fontSize="small">
                          Lambda ARN: <code style={{ fontSize: '11px' }}>{testResult.metadata.lambdaArn}</code>
                        </Text>
                      )}
                      {testResult.metadata.requestId && (
                        <Text fontSize="small">
                          Request ID: <code style={{ fontSize: '11px' }}>{testResult.metadata.requestId}</code>
                        </Text>
                      )}
                      {testResult.metadata.logLevel && (
                        <Text fontSize="small">
                          Log Level: <Badge>{testResult.metadata.logLevel}</Badge>
                        </Text>
                      )}
                    </Flex>
                  </View>
                )}

                {testResult.logs && testResult.logs.length > 0 && (
                  <View marginTop="1rem">
                    <Text fontWeight="bold" marginBottom="0.5rem">Execution Logs:</Text>
                    <View backgroundColor="rgba(0,0,0,0.05)" padding="0.5rem" borderRadius="4px" maxHeight="300px" style={{ overflow: 'auto' }}>
                      <pre style={{ margin: 0, fontSize: '11px', fontFamily: 'monospace' }}>
                        {testResult.logs.join('\n')}
                      </pre>
                    </View>
                  </View>
                )}

                {testResult.cloudWatchUrl && (
                  <View marginTop="1rem">
                    <Button
                      variation="link"
                      onClick={() => window.open(testResult.cloudWatchUrl, '_blank')}
                    >
                      View Detailed Logs in CloudWatch →
                    </Button>
                  </View>
                )}

                {testResult.success && (
                  <Flex marginTop="1rem" gap="0.5rem">
                    <Button
                      variation="primary"
                      onClick={() => setShowSaveTestModal(true)}
                    >
                      Save as Test Event with Expected Output
                    </Button>
                    {testResult.testEventId && (
                      <Button
                        onClick={() => {
                          // Set initial values for update modal
                          const outputToSave = testResult.result || JSON.stringify(testResult.output);
                          setUpdateExpectedOutput(
                            typeof outputToSave === 'string' ? outputToSave : JSON.stringify(outputToSave, null, 2)
                          );
                          setUpdateValidationType('exact');
                          setUpdateValidationConfig('{}');
                          setPreviewValidationResult(null);
                          setShowUpdateModal(true);
                        }}
                      >
                        Update Expected Output
                      </Button>
                    )}
                  </Flex>
                )}
              </Card>
            </>
          )}

          {showUpdateModal && testResult && (
            <Card variation="elevated" marginTop="1rem">
              <Heading level={4}>Update Expected Output</Heading>
              <Flex direction="column" gap="1rem">
                <Text fontSize="small" color="gray">
                  Test Event: {testResult.testEventId}
                </Text>
                
                <TextAreaField
                  label="Expected Output"
                  value={updateExpectedOutput}
                  onChange={(e) => setUpdateExpectedOutput(e.target.value)}
                  rows={8}
                  descriptiveText="Enter the expected value. For 'contains' validation, you can enter just the text to search for (e.g., '174 mi'). For 'exact' match, enter the complete expected output."
                />
                
                <SelectField
                  label="Validation Type"
                  value={updateValidationType}
                  onChange={(e) => setUpdateValidationType(e.target.value)}
                  descriptiveText="How to validate the output against expected results"
                >
                  <option value="exact">Exact Match - Output must match exactly</option>
                  <option value="contains">Contains - Output must contain the expected text</option>
                  <option value="regex">Regex - Output must match the pattern</option>
                  <option value="schema">JSON Schema - Validate structure and types</option>
                  <option value="range">Numeric Range - Value must be within range</option>
                  <option value="semantic">Semantic - Similar meaning (for LLM outputs)</option>
                  <option value="ignore">No Validation - Always passes</option>
                </SelectField>

                {updateValidationType === 'regex' && (
                  <TextAreaField
                    label="Validation Configuration"
                    value={updateValidationConfig}
                    onChange={(e) => setUpdateValidationConfig(e.target.value)}
                    placeholder='{"flags": "gi"}'
                    rows={2}
                    descriptiveText="JSON configuration for regex flags"
                  />
                )}

                {updateValidationType === 'contains' && (
                  <Text fontSize="small" color="gray">
                    The test will pass if the actual output contains the expected text anywhere within it.
                  </Text>
                )}

                {updateValidationType === 'schema' && (
                  <TextAreaField
                    label="Validation Configuration"
                    value={updateValidationConfig}
                    onChange={(e) => setUpdateValidationConfig(e.target.value)}
                    placeholder='{"type": "object", "required": ["field1"], "properties": {"field1": {"type": "string"}}}'
                    rows={4}
                    descriptiveText="JSON Schema definition"
                  />
                )}

                {updateValidationType === 'range' && (
                  <TextAreaField
                    label="Validation Configuration"
                    value={updateValidationConfig}
                    onChange={(e) => setUpdateValidationConfig(e.target.value)}
                    placeholder='{"min": 0, "max": 100, "tolerance": 5}'
                    rows={2}
                    descriptiveText="Numeric range configuration"
                  />
                )}

                {updateValidationType === 'semantic' && (
                  <TextAreaField
                    label="Validation Configuration"
                    value={updateValidationConfig}
                    onChange={(e) => setUpdateValidationConfig(e.target.value)}
                    placeholder='{"threshold": 0.8, "concepts": ["key", "important", "terms"]}'
                    rows={3}
                    descriptiveText="Similarity threshold (0-1) or key concepts to check"
                  />
                )}
                
                {/* Local Validation Preview */}
                <Card variation="outlined">
                  <Flex direction="column" gap="0.5rem">
                    <Text fontWeight="bold">Test Validation Locally</Text>
                    <Button
                      size="small"
                      variation="link"
                      onClick={() => {
                        // Perform local validation
                        const actualOutput = testResult.result || JSON.stringify(testResult.output);
                        const actualStr = typeof actualOutput === 'string' ? actualOutput : JSON.stringify(actualOutput);
                        
                        let expectedValue;
                        try {
                          expectedValue = JSON.parse(updateExpectedOutput);
                        } catch {
                          expectedValue = updateExpectedOutput;
                        }
                        const expectedStr = typeof expectedValue === 'string' ? expectedValue : JSON.stringify(expectedValue);
                        
                        // For contains and regex, also search within JSON structure values
                        const getSearchableText = (obj: any): string => {
                          if (typeof obj === 'string') return obj;
                          if (typeof obj === 'number') return obj.toString();
                          if (typeof obj === 'object' && obj !== null) {
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
                        
                        let validationPassed = false;
                        let validationMessage = '';
                        
                        switch (updateValidationType) {
                          case 'exact':
                            validationPassed = actualStr === expectedStr;
                            validationMessage = validationPassed ? '✓ Exact match' : '✗ Output does not match';
                            break;
                          case 'contains':
                            // Search in both stringified and extracted values
                            const searchableText = getSearchableText(testResult.output || testResult.result);
                            validationPassed = actualStr.includes(expectedStr) || searchableText.includes(expectedStr);
                            validationMessage = validationPassed 
                              ? `✓ Output contains "${expectedStr}"` 
                              : `✗ Output does not contain "${expectedStr}"`;
                            break;
                          case 'regex':
                            try {
                              const config = JSON.parse(updateValidationConfig || '{}');
                              const pattern = new RegExp(expectedStr, config.flags || 'g');
                              const searchable = getSearchableText(testResult.output || testResult.result);
                              validationPassed = pattern.test(actualStr) || pattern.test(searchable);
                              validationMessage = validationPassed 
                                ? `✓ Pattern matches` 
                                : `✗ Pattern does not match`;
                            } catch (e) {
                              validationMessage = '✗ Invalid regex pattern';
                            }
                            break;
                          case 'ignore':
                            validationPassed = true;
                            validationMessage = '✓ Validation skipped (always passes)';
                            break;
                          default:
                            validationMessage = 'Validation type requires server-side execution';
                        }
                        
                        // Update the preview result state
                        setPreviewValidationResult({
                          passed: validationPassed,
                          message: validationMessage
                        });
                      }}
                    >
                      Preview Validation Result
                    </Button>
                    
                    {/* Display validation preview result */}
                    {previewValidationResult && (
                      <Alert
                        variation={previewValidationResult.passed ? 'success' : 'error'}
                        isDismissible
                        onDismiss={() => setPreviewValidationResult(null)}
                      >
                        {previewValidationResult.message}
                      </Alert>
                    )}
                    
                    <Text fontSize="small" color="gray">
                      Test if your validation logic would pass with the current output
                    </Text>
                  </Flex>
                </Card>
                
                <Flex gap="0.5rem">
                  <Button
                    variation="primary"
                    onClick={async () => {
                      try {
                        // Parse validation config if needed
                        let parsedConfig = null;
                        if (updateValidationType !== 'exact' && updateValidationType !== 'ignore' && updateValidationType !== 'contains') {
                          try {
                            parsedConfig = JSON.parse(updateValidationConfig || '{}');
                          } catch (e) {
                            setError('Invalid validation configuration JSON');
                            return;
                          }
                        }

                        // Handle expected output formatting for AWSJSON
                        let formattedExpectedOutput;
                        try {
                          // Try to parse as JSON first
                          JSON.parse(updateExpectedOutput);
                          formattedExpectedOutput = updateExpectedOutput; // Already valid JSON
                        } catch {
                          // If not valid JSON, treat as string/number and JSON encode it
                          formattedExpectedOutput = JSON.stringify(updateExpectedOutput);
                        }

                        await client.mutations.saveTestEvent({
                          resource_type: 'tool',
                          resource_id: selectedTool,
                          test_name: testResult.testEventId ? testResult.testEventId.split('#')[1] : 'unknown',
                          test_input: testInput,
                          expected_output: formattedExpectedOutput,
                          validation_type: updateValidationType,
                          validation_config: parsedConfig ? JSON.stringify(parsedConfig) : null,
                          metadata: JSON.stringify({
                            last_successful_run: new Date().toISOString(),
                            execution_time: testResult.executionTime,
                            updated_validation: true
                          })
                        });
                        setSuccess(`Expected output updated with ${updateValidationType} validation!`);
                        setShowUpdateModal(false);
                        setTimeout(() => setSuccess(null), 3000);
                      } catch (err) {
                        console.error('Error updating expected output:', err);
                        setError('Failed to update expected output');
                      }
                    }}
                  >
                    Update
                  </Button>
                  <Button
                    onClick={() => {
                      setShowUpdateModal(false);
                      setUpdateExpectedOutput('');
                      setUpdateValidationType('exact');
                      setUpdateValidationConfig('{}');
                      setPreviewValidationResult(null);
                    }}
                  >
                    Cancel
                  </Button>
                </Flex>
              </Flex>
            </Card>
          )}

          {showSaveTestModal && (
            <Card variation="elevated" marginTop="1rem">
              <Heading level={4}>Save Test Event</Heading>
              <Flex direction="column" gap="1rem">
                <TextField
                  label="Test Name"
                  value={newTestName}
                  onChange={(e) => setNewTestName(e.target.value)}
                  placeholder="e.g., smoke_test, edge_case_test"
                  required
                />
                <TextAreaField
                  label="Description"
                  value={newTestDescription}
                  onChange={(e) => setNewTestDescription(e.target.value)}
                  placeholder="Describe what this test validates"
                  rows={3}
                />
                
                {testResult?.success && (
                  <>
                    <SelectField
                      label="Validation Type"
                      value={validationType}
                      onChange={(e) => setValidationType(e.target.value)}
                      descriptiveText="How to validate the output against expected results"
                    >
                      <option value="exact">Exact Match - Output must match exactly</option>
                      <option value="contains">Contains - Output must contain the expected text</option>
                      <option value="regex">Regex - Output must match the pattern</option>
                      <option value="schema">JSON Schema - Validate structure and types</option>
                      <option value="range">Numeric Range - Value must be within range</option>
                      <option value="semantic">Semantic - Similar meaning (for LLM outputs)</option>
                      <option value="ignore">No Validation - Always passes</option>
                    </SelectField>

                    {validationType === 'regex' && (
                      <TextAreaField
                        label="Validation Configuration"
                        value={validationConfig}
                        onChange={(e) => setValidationConfig(e.target.value)}
                        placeholder='{"flags": "gi"}'
                        rows={2}
                        descriptiveText="JSON configuration for regex flags"
                      />
                    )}

                    {validationType === 'schema' && (
                      <TextAreaField
                        label="Validation Configuration"
                        value={validationConfig}
                        onChange={(e) => setValidationConfig(e.target.value)}
                        placeholder='{"type": "object", "required": ["field1"], "properties": {"field1": {"type": "string"}}}'
                        rows={4}
                        descriptiveText="JSON Schema definition"
                      />
                    )}

                    {validationType === 'range' && (
                      <TextAreaField
                        label="Validation Configuration"
                        value={validationConfig}
                        onChange={(e) => setValidationConfig(e.target.value)}
                        placeholder='{"min": 0, "max": 100, "tolerance": 5}'
                        rows={2}
                        descriptiveText="Numeric range configuration"
                      />
                    )}

                    {validationType === 'semantic' && (
                      <TextAreaField
                        label="Validation Configuration"
                        value={validationConfig}
                        onChange={(e) => setValidationConfig(e.target.value)}
                        placeholder='{"threshold": 0.8, "concepts": ["key", "important", "terms"]}'
                        rows={3}
                        descriptiveText="Similarity threshold (0-1) or key concepts to check"
                      />
                    )}
                  </>
                )}
                
                <View>
                  <Text fontWeight="bold" marginBottom="0.5rem">Test Input Preview:</Text>
                  <View backgroundColor="rgba(0,0,0,0.05)" padding="0.5rem" borderRadius="4px">
                    <pre style={{ margin: 0, fontSize: '12px', overflow: 'auto', maxHeight: '200px' }}>
                      {testInput}
                    </pre>
                  </View>
                </View>
                {testResult?.success && (
                  <View>
                    <Text fontWeight="bold" marginBottom="0.5rem">Expected Output (for automated health testing):</Text>
                    <Alert variation="info" marginBottom="0.5rem">
                      The current test output will be saved as the expected output for automated health testing
                    </Alert>
                    <View backgroundColor="rgba(0,0,0,0.05)" padding="0.5rem" borderRadius="4px">
                      <pre style={{ margin: 0, fontSize: '12px', overflow: 'auto', maxHeight: '200px' }}>
                        {testResult.result ? 
                          (typeof testResult.result === 'string' ? 
                            JSON.stringify(JSON.parse(testResult.result), null, 2) : 
                            JSON.stringify(testResult.result, null, 2)) :
                          JSON.stringify(testResult.output, null, 2)}
                      </pre>
                    </View>
                  </View>
                )}
                <Flex gap="0.5rem">
                  <Button
                    variation="primary"
                    onClick={handleSaveTestEvent}
                  >
                    Save Test Event
                  </Button>
                  <Button
                    onClick={() => {
                      setShowSaveTestModal(false);
                      setNewTestName('');
                      setNewTestDescription('');
                      setValidationType('exact');
                      setValidationConfig('{}');
                    }}
                  >
                    Cancel
                  </Button>
                </Flex>
              </Flex>
            </Card>
          )}
        </Flex>
      </Card>
    </View>
  );
}