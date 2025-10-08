import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card,
  Heading,
  Text,
  View,
  Loader,
  Alert,
  Button,
  TextField,
  Flex,
  Badge,
  Divider,
  Tabs,
} from '@aws-amplify/ui-react';

interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: any;
}

interface ResourceDefinition {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

interface PromptDefinition {
  name: string;
  description?: string;
  arguments?: Array<{
    name: string;
    description?: string;
    required?: boolean;
  }>;
}

interface PromptMessage {
  role: 'user' | 'assistant';
  content: {
    type: string;
    text: string;
  };
}

interface FormField {
  name: string;
  label: string;
  field_type: string;
  required: boolean;
  description?: string;
  default_value?: any;
}

interface ToolResult {
  content?: Array<{
    type: string;
    text: string;
  }>;
  isError?: boolean;
  error?: string;
}

interface ResourceContent {
  contents?: Array<{
    uri: string;
    mimeType?: string;
    text?: string;
  }>;
  isError?: boolean;
  error?: string;
}

interface PromptResult {
  messages?: PromptMessage[];
  description?: string;
  isError?: boolean;
  error?: string;
}

interface WasmMcpClientProps {
  serverUrl: string;
  onToolsLoaded?: (tools: ToolDefinition[]) => void;
}

export default function WasmMcpClient({ serverUrl, onToolsLoaded }: WasmMcpClientProps) {
  const [client, setClient] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [selectedTool, setSelectedTool] = useState<ToolDefinition | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [toolResult, setToolResult] = useState<ToolResult | null>(null);
  const [executing, setExecuting] = useState(false);
  const [resources, setResources] = useState<ResourceDefinition[]>([]);
  const [selectedResource, setSelectedResource] = useState<ResourceDefinition | null>(null);
  const [resourceContent, setResourceContent] = useState<ResourceContent | null>(null);
  const [loadingResource, setLoadingResource] = useState(false);
  const [prompts, setPrompts] = useState<PromptDefinition[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptDefinition | null>(null);
  const [promptFormData, setPromptFormData] = useState<Record<string, any>>({});
  const [promptResult, setPromptResult] = useState<PromptResult | null>(null);
  const [executingPrompt, setExecutingPrompt] = useState(false);
  const wasmModule = useRef<any>(null);

  // Debug resources state
  useEffect(() => {
    console.log('Resources state updated:', resources);
  }, [resources]);

  // Initialize WASM client
  useEffect(() => {
    const initWasm = async () => {
      try {
        setLoading(true);
        setError(null);

        // Dynamically import the WASM module
        const wasm = await import('../wasm/mcp_management_wasm_client.js');

        // Load WASM file from public directory
        const wasmPath = new URL('/mcp_management_wasm_client_bg.wasm', window.location.origin).href;
        await wasm.default(wasmPath);
        wasmModule.current = wasm;

        console.log('WASM Client using endpoint:', serverUrl);

        // Create the WASM client
        const wasmClient = new wasm.PmcpWasmClient(serverUrl);
        setClient(wasmClient);

        // Initialize the client
        const initResult = await wasmClient.initialize();
        console.log('WASM Client initialized:', initResult);
        setInitialized(true);

        // List available tools
        const toolsList = await wasmClient.list_tools();
        console.log('Raw tools response:', toolsList);

        // Process tools list
        let processedTools: ToolDefinition[] = [];

        if (Array.isArray(toolsList)) {
          processedTools = toolsList.map((tool: any) => {
            // Handle if it's a Map or plain object
            if (tool instanceof Map) {
              const obj: any = {};
              tool.forEach((value: any, key: string) => {
                obj[key] = value;
              });
              return obj;
            }
            return tool;
          });
        }

        console.log('Processed tools:', processedTools);
        setTools(processedTools);

        if (onToolsLoaded) {
          onToolsLoaded(processedTools);
        }

        // List available resources
        try {
          const resourcesList = await wasmClient.list_resources();
          console.log('Raw resources response:', resourcesList);
          console.log('Is array?', Array.isArray(resourcesList));
          console.log('Type:', typeof resourcesList);

          // Process resources list
          let processedResources: ResourceDefinition[] = [];

          if (Array.isArray(resourcesList)) {
            processedResources = resourcesList.map((resource: any) => {
              if (resource instanceof Map) {
                const obj: any = {};
                resource.forEach((value: any, key: string) => {
                  obj[key] = value;
                });
                return obj;
              }
              return resource;
            });
          }

          console.log('Processed resources:', processedResources);
          console.log('Processed resources length:', processedResources.length);
          setResources(processedResources);
        } catch (resourceErr) {
          console.error('Failed to load resources:', resourceErr);
          // Don't fail initialization if resources fail
        }

        // List available prompts
        try {
          const promptsList = await wasmClient.list_prompts();
          console.log('Raw prompts response:', promptsList);

          // Process prompts list
          let processedPrompts: PromptDefinition[] = [];

          if (Array.isArray(promptsList)) {
            processedPrompts = promptsList.map((prompt: any) => {
              if (prompt instanceof Map) {
                const obj: any = {};
                prompt.forEach((value: any, key: string) => {
                  obj[key] = value;
                });
                return obj;
              }
              return prompt;
            });
          }

          console.log('Processed prompts:', processedPrompts);
          setPrompts(processedPrompts);
        } catch (promptErr) {
          console.error('Failed to load prompts:', promptErr);
          // Don't fail initialization if prompts fail
        }

      } catch (err) {
        console.error('Failed to initialize WASM client:', err);
        setError(err instanceof Error ? err.message : 'Failed to initialize WASM client');
      } finally {
        setLoading(false);
      }
    };

    initWasm();
  }, [serverUrl, onToolsLoaded]);

  // Generate form fields from tool schema
  const getFormFields = useCallback((tool: ToolDefinition): FormField[] => {
    const properties = tool.inputSchema?.properties || {};
    const required = tool.inputSchema?.required || [];

    return Object.entries(properties).map(([name, schema]: [string, any]) => ({
      name,
      label: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      field_type: schema.type === 'number' || schema.type === 'integer' ? 'number' :
                  schema.type === 'boolean' ? 'boolean' : 'string',
      required: required.includes(name),
      description: schema.description,
      default_value: schema.default
    }));
  }, []);

  // Handle tool selection
  const handleToolSelect = useCallback((tool: ToolDefinition) => {
    setSelectedTool(tool);
    setFormData({});
    setToolResult(null);
  }, []);

  // Handle form input changes
  const handleInputChange = useCallback((fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  }, []);

  // Execute the selected tool
  const executeTool = useCallback(async () => {
    if (!client || !selectedTool) return;

    setExecuting(true);
    setToolResult(null);

    try {
      const result = await client.call_tool(selectedTool.name, formData);
      setToolResult(result as ToolResult);
    } catch (err) {
      console.error('Tool execution failed:', err);
      setToolResult({
        isError: true,
        error: err instanceof Error ? err.message : 'Tool execution failed'
      });
    } finally {
      setExecuting(false);
    }
  }, [client, selectedTool, formData]);

  // Handle resource selection
  const handleResourceSelect = useCallback((resource: ResourceDefinition) => {
    setSelectedResource(resource);
    setResourceContent(null);
  }, []);

  // Read the selected resource
  const readResource = useCallback(async () => {
    if (!client || !selectedResource) return;

    setLoadingResource(true);
    setResourceContent(null);

    try {
      const content = await client.read_resource(selectedResource.uri);
      setResourceContent(content as ResourceContent);
    } catch (err) {
      console.error('Resource read failed:', err);
      setResourceContent({
        isError: true,
        error: err instanceof Error ? err.message : 'Resource read failed'
      });
    } finally {
      setLoadingResource(false);
    }
  }, [client, selectedResource]);

  // Handle prompt selection
  const handlePromptSelect = useCallback((prompt: PromptDefinition) => {
    setSelectedPrompt(prompt);
    setPromptFormData({});
    setPromptResult(null);
  }, []);

  // Handle prompt form input changes
  const handlePromptInputChange = useCallback((fieldName: string, value: any) => {
    setPromptFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  }, []);

  // Execute the selected prompt
  const executePrompt = useCallback(async () => {
    if (!client || !selectedPrompt) return;

    setExecutingPrompt(true);
    setPromptResult(null);

    try {
      const result = await client.get_prompt(selectedPrompt.name, promptFormData);
      setPromptResult(result as PromptResult);
    } catch (err) {
      console.error('Prompt execution failed:', err);
      setPromptResult({
        isError: true,
        error: err instanceof Error ? err.message : 'Prompt execution failed'
      });
    } finally {
      setExecutingPrompt(false);
    }
  }, [client, selectedPrompt, promptFormData]);

  // Render form field
  const renderFormField = (field: FormField) => {
    const value = formData[field.name] ?? field.default_value ?? '';

    return (
      <View key={field.name} marginBottom="1rem">
        <Text fontWeight="bold">
          {field.label}
          {field.required && <Text as="span" color="red"> *</Text>}
        </Text>
        {field.description && (
          <Text fontSize="0.875rem" color="gray">{field.description}</Text>
        )}
        {field.field_type === 'number' ? (
          <TextField
            label=""
            type="number"
            value={value}
            onChange={(e) => handleInputChange(field.name, e.target.valueAsNumber || 0)}
            placeholder={field.description || field.label}
          />
        ) : field.field_type === 'boolean' ? (
          <input
            type="checkbox"
            checked={value}
            onChange={(e) => handleInputChange(field.name, e.target.checked)}
          />
        ) : (
          <TextField
            label=""
            value={value}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
            placeholder={field.description || field.label}
          />
        )}
      </View>
    );
  };

  // Render result
  const renderResult = () => {
    if (!toolResult) return null;

    if (toolResult.isError || toolResult.error) {
      return (
        <Alert variation="error" marginTop="1rem">
          <Heading level={6}>Error</Heading>
          <Text>{toolResult.error}</Text>
        </Alert>
      );
    }

    if (toolResult.content && toolResult.content[0]) {
      const content = toolResult.content[0];

      // Handle text content
      if (content.type === 'text' && content.text) {
        try {
          // Try to parse as JSON first
          const parsed = JSON.parse(content.text);

          // If the parsed object has a 'result' field that's a string, display it as text
          if (parsed.result && typeof parsed.result === 'string') {
            return (
              <Card variation="outlined" marginTop="1rem">
                <Heading level={6}>Result</Heading>
                <Text
                  style={{
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    lineHeight: '1.5'
                  }}
                >
                  {parsed.result}
                </Text>
              </Card>
            );
          }

          // Otherwise show as formatted JSON
          return (
            <Card variation="outlined" marginTop="1rem">
              <Heading level={6}>Result</Heading>
              <pre style={{
                overflow: 'auto',
                padding: '1rem',
                backgroundColor: '#f5f5f5',
                borderRadius: '4px',
                fontSize: '0.875rem',
                lineHeight: '1.5'
              }}>
                {JSON.stringify(parsed, null, 2)}
              </pre>
            </Card>
          );
        } catch {
          // Not JSON, display as plain text
          return (
            <Card variation="outlined" marginTop="1rem">
              <Heading level={6}>Result</Heading>
              <Text style={{ whiteSpace: 'pre-wrap' }}>{content.text}</Text>
            </Card>
          );
        }
      }
    }

    // Fallback: show raw result
    return (
      <Card variation="outlined" marginTop="1rem">
        <Heading level={6}>Result</Heading>
        <pre style={{ overflow: 'auto', fontSize: '0.875rem' }}>
          {JSON.stringify(toolResult, null, 2)}
        </pre>
      </Card>
    );
  };

  // Render resource content
  const renderResourceContent = () => {
    if (!resourceContent) return null;

    if (resourceContent.isError || resourceContent.error) {
      return (
        <Alert variation="error" marginTop="1rem">
          <Heading level={6}>Error</Heading>
          <Text>{resourceContent.error}</Text>
        </Alert>
      );
    }

    if (resourceContent.contents && resourceContent.contents[0]) {
      const content = resourceContent.contents[0];

      return (
        <Card variation="outlined" marginTop="1rem">
          <Heading level={6}>Resource Content</Heading>
          {content.mimeType && (
            <Badge marginBottom="0.5rem">{content.mimeType}</Badge>
          )}
          <Divider marginBottom="1rem" />
          <Text
            style={{
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              lineHeight: '1.5',
              maxHeight: '600px',
              overflow: 'auto'
            }}
          >
            {content.text}
          </Text>
        </Card>
      );
    }

    // Fallback: show raw content
    return (
      <Card variation="outlined" marginTop="1rem">
        <Heading level={6}>Resource Content</Heading>
        <pre style={{ overflow: 'auto', fontSize: '0.875rem' }}>
          {JSON.stringify(resourceContent, null, 2)}
        </pre>
      </Card>
    );
  };

  // Get form fields from prompt arguments
  const getPromptFormFields = useCallback((prompt: PromptDefinition): FormField[] => {
    if (!prompt.arguments || prompt.arguments.length === 0) {
      return [];
    }

    return prompt.arguments.map((arg) => ({
      name: arg.name,
      label: arg.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      field_type: 'string',
      required: arg.required || false,
      description: arg.description,
      default_value: ''
    }));
  }, []);

  // Render prompt form field
  const renderPromptFormField = (field: FormField) => {
    const value = promptFormData[field.name] ?? field.default_value ?? '';

    return (
      <View key={field.name} marginBottom="1rem">
        <Text fontWeight="bold">
          {field.label}
          {field.required && <Text as="span" color="red"> *</Text>}
        </Text>
        {field.description && (
          <Text fontSize="0.875rem" color="gray">{field.description}</Text>
        )}
        <TextField
          label=""
          value={value}
          onChange={(e) => handlePromptInputChange(field.name, e.target.value)}
          placeholder={field.description || field.label}
        />
      </View>
    );
  };

  // Render prompt result (messages)
  const renderPromptResult = () => {
    if (!promptResult) return null;

    if (promptResult.isError || promptResult.error) {
      return (
        <Alert variation="error" marginTop="1rem">
          <Heading level={6}>Error</Heading>
          <Text>{promptResult.error}</Text>
        </Alert>
      );
    }

    if (promptResult.messages && promptResult.messages.length > 0) {
      return (
        <Card variation="outlined" marginTop="1rem">
          <Heading level={6}>Messages</Heading>
          {promptResult.description && (
            <Text fontSize="0.875rem" color="gray" marginBottom="1rem">
              {promptResult.description}
            </Text>
          )}
          <Divider marginBottom="1rem" />
          <View>
            {promptResult.messages.map((message, index) => (
              <Card
                key={index}
                variation={message.role === 'user' ? 'outlined' : 'elevated'}
                marginBottom="1rem"
              >
                <Badge variation={message.role === 'user' ? 'info' : 'success'}>
                  {message.role}
                </Badge>
                <Text
                  marginTop="0.5rem"
                  style={{
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    lineHeight: '1.5'
                  }}
                >
                  {message.content.text}
                </Text>
              </Card>
            ))}
          </View>
        </Card>
      );
    }

    // Fallback: show raw result
    return (
      <Card variation="outlined" marginTop="1rem">
        <Heading level={6}>Result</Heading>
        <pre style={{ overflow: 'auto', fontSize: '0.875rem' }}>
          {JSON.stringify(promptResult, null, 2)}
        </pre>
      </Card>
    );
  };

  if (loading) {
    return (
      <Flex direction="column" alignItems="center" padding="2rem">
        <Loader size="large" />
        <Text marginTop="1rem">Initializing WASM client...</Text>
      </Flex>
    );
  }

  if (error) {
    return (
      <Alert variation="error">
        <Heading level={5}>Failed to Initialize WASM Client</Heading>
        <Text>{error}</Text>
      </Alert>
    );
  }

  return (
    <View>
      {/* Status Banner */}
      <Card variation="outlined" marginBottom="1rem">
        <Flex direction="row" alignItems="center" gap="1rem">
          <Badge variation={initialized ? 'success' : 'warning'}>
            {initialized ? 'Connected' : 'Initializing'}
          </Badge>
          <View>
            <Text fontWeight="bold">WASM Client Status</Text>
            <Text fontSize="0.875rem" color="gray">
              Using pmcp SDK compiled to WebAssembly
            </Text>
          </View>
        </Flex>
      </Card>

      <Tabs
        defaultValue="tools"
        items={[
          {
            label: `Tools (${tools.length})`,
            value: 'tools',
            content: (
              <Flex direction="row" gap="1rem" marginTop="1rem">
            {/* Tool List */}
            <Card flex="1" variation="outlined">
              <Heading level={5}>Available Tools</Heading>
              <Divider marginTop="0.5rem" marginBottom="0.5rem" />
              <View>
                {tools.map((tool) => (
                  <Card
                    key={tool.name}
                    variation={selectedTool?.name === tool.name ? 'elevated' : 'outlined'}
                    marginBottom="0.5rem"
                    onClick={() => handleToolSelect(tool)}
                    style={{ cursor: 'pointer' }}
                  >
                    <Text fontWeight="bold">{tool.name}</Text>
                    <Text fontSize="0.875rem" color="gray">{tool.description}</Text>
                  </Card>
                ))}
              </View>
            </Card>

            {/* Tool Details */}
            {selectedTool && (
              <Card flex="2" variation="outlined">
                <Heading level={5}>{selectedTool.name}</Heading>
                <Text color="gray" marginBottom="1rem">{selectedTool.description}</Text>
                <Divider marginBottom="1rem" />

                {/* Form Fields */}
                <View>
                  {getFormFields(selectedTool).map(field => renderFormField(field))}
                </View>

                {/* Execute Button */}
                <Button
                  onClick={executeTool}
                  isLoading={executing}
                  loadingText="Executing..."
                  variation="primary"
                  marginTop="1rem"
                >
                  Execute Tool
                </Button>

                {/* Result Display */}
                {renderResult()}
              </Card>
            )}
              </Flex>
            )
          },
          {
            label: `Resources (${resources.length})`,
            value: 'resources',
            content: (
              <Flex direction="row" gap="1rem" marginTop="1rem">
            {/* Resource List */}
            <Card flex="1" variation="outlined">
              <Heading level={5}>Available Resources</Heading>
              <Divider marginTop="0.5rem" marginBottom="0.5rem" />
              {resources.length === 0 ? (
                <Text color="gray" padding="1rem">No resources available</Text>
              ) : (
                <View>
                  {resources.map((resource) => (
                  <Card
                    key={resource.uri}
                    variation={selectedResource?.uri === resource.uri ? 'elevated' : 'outlined'}
                    marginBottom="0.5rem"
                    onClick={() => handleResourceSelect(resource)}
                    style={{ cursor: 'pointer' }}
                  >
                    <Text fontWeight="bold">{resource.name}</Text>
                    {resource.description && (
                      <Text fontSize="0.875rem" color="gray">{resource.description}</Text>
                    )}
                    <Text fontSize="0.75rem" color="gray" marginTop="0.25rem">
                      {resource.uri}
                    </Text>
                  </Card>
                  ))}
                </View>
              )}
            </Card>

            {/* Resource Details */}
            {selectedResource && (
              <Card flex="2" variation="outlined">
                <Heading level={5}>{selectedResource.name}</Heading>
                {selectedResource.description && (
                  <Text color="gray" marginBottom="0.5rem">{selectedResource.description}</Text>
                )}
                <Text fontSize="0.875rem" color="gray" marginBottom="1rem">
                  URI: {selectedResource.uri}
                </Text>
                <Divider marginBottom="1rem" />

                {/* Read Button */}
                <Button
                  onClick={readResource}
                  isLoading={loadingResource}
                  loadingText="Loading..."
                  variation="primary"
                  marginTop="1rem"
                >
                  Read Resource
                </Button>

                {/* Resource Content Display */}
                {renderResourceContent()}
              </Card>
            )}
              </Flex>
            )
          },
          {
            label: `Prompts (${prompts.length})`,
            value: 'prompts',
            content: (
              <Flex direction="row" gap="1rem" marginTop="1rem">
            {/* Prompt List */}
            <Card flex="1" variation="outlined">
              <Heading level={5}>Available Prompts</Heading>
              <Divider marginTop="0.5rem" marginBottom="0.5rem" />
              {prompts.length === 0 ? (
                <Text color="gray" padding="1rem">No prompts available</Text>
              ) : (
                <View>
                  {prompts.map((prompt) => (
                  <Card
                    key={prompt.name}
                    variation={selectedPrompt?.name === prompt.name ? 'elevated' : 'outlined'}
                    marginBottom="0.5rem"
                    onClick={() => handlePromptSelect(prompt)}
                    style={{ cursor: 'pointer' }}
                  >
                    <Text fontWeight="bold">{prompt.name}</Text>
                    {prompt.description && (
                      <Text fontSize="0.875rem" color="gray">{prompt.description}</Text>
                    )}
                    {prompt.arguments && prompt.arguments.length > 0 && (
                      <Text fontSize="0.75rem" color="gray" marginTop="0.25rem">
                        Arguments: {prompt.arguments.map(a => a.name).join(', ')}
                      </Text>
                    )}
                  </Card>
                  ))}
                </View>
              )}
            </Card>

            {/* Prompt Details */}
            {selectedPrompt && (
              <Card flex="2" variation="outlined">
                <Heading level={5}>{selectedPrompt.name}</Heading>
                {selectedPrompt.description && (
                  <Text color="gray" marginBottom="1rem">{selectedPrompt.description}</Text>
                )}
                <Divider marginBottom="1rem" />

                {/* Prompt Arguments Form */}
                <View>
                  {getPromptFormFields(selectedPrompt).map(field => renderPromptFormField(field))}
                </View>

                {/* Execute Button */}
                <Button
                  onClick={executePrompt}
                  isLoading={executingPrompt}
                  loadingText="Executing..."
                  variation="primary"
                  marginTop="1rem"
                >
                  Get Prompt
                </Button>

                {/* Prompt Result Display */}
                {renderPromptResult()}
              </Card>
            )}
              </Flex>
            )
          }
        ]}
      />
    </View>
  );
}
