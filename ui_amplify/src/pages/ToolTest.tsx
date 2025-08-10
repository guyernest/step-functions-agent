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
  Divider
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
  output?: any;
  error?: string;
  executionTime?: number;
  metadata?: {
    lambdaArn?: string;
    statusCode?: number;
    functionError?: string;
  };
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
  const [inputSchema, setInputSchema] = useState<any>(null);

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

  const handleToolSelection = (toolName: string) => {
    setTestResult(null);
    setError(null);
    
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
      const testInputString = JSON.stringify(parsedInput);
      console.log('Calling testToolExecution with:', {
        toolName: selectedTool,
        testInput: testInputString,
      });
      
      const response = await client.mutations.testToolExecution({
        toolName: selectedTool,
        testInput: testInputString,
      });
      
      console.log('Response from testToolExecution:', response);
      console.log('Response data type:', typeof response.data);
      console.log('Response data:', response.data);

      if (response.data) {
        // Check if response.data is the string directly or has testToolExecution property
        let dataToProcess: any = response.data;
        
        // If response has a testToolExecution property, use that
        if (response.data && typeof response.data === 'object' && 'testToolExecution' in response.data) {
          dataToProcess = (response.data as any).testToolExecution;
        }
        
        // Now parse the data if it's a string
        let result;
        if (typeof dataToProcess === 'string') {
          try {
            result = JSON.parse(dataToProcess);
            console.log('Parsed test result:', result);
          } catch (e) {
            console.error('Failed to parse response:', e);
            setError('Failed to parse test execution response');
            return;
          }
        } else {
          result = dataToProcess;
          console.log('Test result (not string):', result);
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
                    ? `Test successful${testResult.executionTime ? ` - Execution time: ${testResult.executionTime}ms` : ''}`
                    : testResult.error || 'Test failed'}
                </Alert>

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
                    </Flex>
                  </View>
                )}
              </Card>
            </>
          )}
        </Flex>
      </Card>
    </View>
  );
}