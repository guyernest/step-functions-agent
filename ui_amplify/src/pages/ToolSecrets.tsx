import React, { useState, useEffect } from 'react';
import {
  View,
  Card,
  Heading,
  Button,
  TextField,
  Alert,
  Loader,
  Badge,
  Flex,
  Text,
  Divider,
  Collection
} from '@aws-amplify/ui-react';
import { generateClient } from 'aws-amplify/api';
import '@aws-amplify/ui-react/styles.css';

const client = generateClient();

interface ToolSecret {
  tool_name: string;
  secret_keys: string[];
  description?: string;
  registered_at?: string;
}

interface SecretValues {
  [toolName: string]: {
    [key: string]: string;
  };
}

const ToolSecrets: React.FC = () => {
  const [toolSecrets, setToolSecrets] = useState<ToolSecret[]>([]);
  const [secretValues, setSecretValues] = useState<SecretValues>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState<{ [tool: string]: boolean }>({});
  const [tempValues, setTempValues] = useState<SecretValues>({});
  const [showPasswords, setShowPasswords] = useState<{ [key: string]: boolean }>({});
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  useEffect(() => {
    loadToolSecrets();
  }, []);

  const loadToolSecrets = async () => {
    setLoading(true);
    try {
      // Load tool registry from GraphQL API
      const toolsResult = await client.graphql({
        query: `
          query ListToolSecrets {
            listToolSecrets
          }
        `
      }) as any;
      
      const toolsData = toolsResult.data?.listToolSecrets;
      if (toolsData?.success && toolsData?.tools) {
        setToolSecrets(toolsData.tools);
      }
      
      // Load current secret values from GraphQL API
      const valuesResult = await client.graphql({
        query: `
          query GetToolSecretValues {
            getToolSecretValues
          }
        `
      }) as any;
      
      const valuesData = valuesResult.data?.getToolSecretValues;
      if (valuesData?.success && valuesData?.rawValues) {
        setSecretValues(valuesData.rawValues);
        setTempValues(valuesData.rawValues);
      }
    } catch (error) {
      console.error('Error loading tool secrets:', error);
      setMessage({ type: 'error', text: 'Failed to load tool secrets' });
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (toolName: string) => {
    setEditMode({ ...editMode, [toolName]: true });
  };

  const handleCancel = (toolName: string) => {
    setEditMode({ ...editMode, [toolName]: false });
    // Reset temp values to original
    setTempValues({
      ...tempValues,
      [toolName]: secretValues[toolName] || {}
    });
  };

  const handleSave = async (toolName: string) => {
    setSaving(true);
    setMessage(null);
    
    try {
      // Update secrets via GraphQL API
      const result = await client.graphql({
        query: `
          mutation UpdateToolSecrets($toolName: String!, $secrets: AWSJSON!) {
            updateToolSecrets(toolName: $toolName, secrets: $secrets)
          }
        `,
        variables: {
          toolName,
          secrets: JSON.stringify(tempValues[toolName] || {})
        }
      }) as any;
      
      const updateData = result.data?.updateToolSecrets;
      if (updateData?.success) {
        setSecretValues({
          ...secretValues,
          [toolName]: tempValues[toolName] || {}
        });
        setEditMode({ ...editMode, [toolName]: false });
        setMessage({ type: 'success', text: updateData.message || `Successfully updated secrets for ${toolName}` });
      } else {
        throw new Error(updateData?.error || 'Failed to update secrets');
      }
    } catch (error) {
      console.error('Error saving secrets:', error);
      setMessage({ type: 'error', text: `Failed to save secrets for ${toolName}` });
    } finally {
      setSaving(false);
    }
  };

  const handleSecretChange = (toolName: string, key: string, value: string) => {
    setTempValues({
      ...tempValues,
      [toolName]: {
        ...tempValues[toolName],
        [key]: value
      }
    });
  };

  const maskSecret = (value: string): string => {
    if (!value || value.startsWith('PLACEHOLDER_')) return value;
    if (value.length <= 8) return '••••••••';
    return value.substring(0, 4) + '••••••••' + value.substring(value.length - 4);
  };

  const togglePasswordVisibility = (key: string) => {
    setShowPasswords({
      ...showPasswords,
      [key]: !showPasswords[key]
    });
  };

  if (loading) {
    return (
      <View padding="large">
        <Flex direction="column" alignItems="center" gap="1rem">
          <Loader size="large" />
          <Text>Loading tool secrets...</Text>
        </Flex>
      </View>
    );
  }

  return (
    <View padding="large">
      <Flex direction="column" gap="1rem">
        <Heading level={2}>Tool Secrets Management</Heading>
        
        {message && (
          <Alert
            variation={message.type === 'error' ? 'error' : message.type === 'success' ? 'success' : 'info'}
            isDismissible
            onDismiss={() => setMessage(null)}
          >
            {message.text}
          </Alert>
        )}

        <Card>
          <Text>
            Manage API keys and secrets for all registered tools. These secrets are stored securely in AWS Secrets Manager
            and are used by the tool Lambda functions.
          </Text>
        </Card>

        <Collection
          items={toolSecrets}
          type="list"
          direction="column"
          gap="1rem"
        >
          {(tool) => (
            <Card key={tool.tool_name} variation="outlined">
              <Flex direction="column" gap="1rem">
                <Flex justifyContent="space-between" alignItems="center">
                  <Flex direction="column" gap="0.25rem">
                    <Heading level={4}>{tool.tool_name}</Heading>
                    {tool.description && (
                      <Text variation="secondary" fontSize="small">
                        {tool.description}
                      </Text>
                    )}
                  </Flex>
                  {!editMode[tool.tool_name] ? (
                    <Button onClick={() => handleEdit(tool.tool_name)} size="small">
                      Edit Secrets
                    </Button>
                  ) : (
                    <Flex gap="0.5rem">
                      <Button
                        onClick={() => handleSave(tool.tool_name)}
                        variation="primary"
                        size="small"
                        isLoading={saving}
                      >
                        Save
                      </Button>
                      <Button
                        onClick={() => handleCancel(tool.tool_name)}
                        size="small"
                        isDisabled={saving}
                      >
                        Cancel
                      </Button>
                    </Flex>
                  )}
                </Flex>

                <Divider />

                <Flex direction="column" gap="0.75rem">
                  {tool.secret_keys.map((key) => {
                    const currentValue = tempValues[tool.tool_name]?.[key] || 
                                        secretValues[tool.tool_name]?.[key] || '';
                    const isPlaceholder = currentValue.startsWith('PLACEHOLDER_');
                    const fieldKey = `${tool.tool_name}-${key}`;
                    
                    return (
                      <Flex key={key} direction="column" gap="0.25rem">
                        <Flex justifyContent="space-between" alignItems="center">
                          <Text fontWeight="bold">{key}</Text>
                          {isPlaceholder && (
                            <Badge variation="warning" size="small">
                              Not Configured
                            </Badge>
                          )}
                        </Flex>
                        
                        {editMode[tool.tool_name] ? (
                          <Flex alignItems="center" gap="0.5rem">
                            <TextField
                              label=""
                              value={currentValue}
                              onChange={(e) => handleSecretChange(tool.tool_name, key, e.target.value)}
                              type={showPasswords[fieldKey] ? "text" : "password"}
                              placeholder={`Enter ${key}`}
                              width="100%"
                            />
                            <Button
                              size="small"
                              onClick={() => togglePasswordVisibility(fieldKey)}
                            >
                              {showPasswords[fieldKey] ? 'Hide' : 'Show'}
                            </Button>
                          </Flex>
                        ) : (
                          <Text
                            variation="secondary"
                            fontFamily="monospace"
                            backgroundColor={isPlaceholder ? "var(--amplify-colors-orange-10)" : "var(--amplify-colors-neutral-10)"}
                            padding="0.25rem 0.5rem"
                            borderRadius="0.25rem"
                          >
                            {isPlaceholder ? 'Not configured - click Edit to add' : maskSecret(currentValue)}
                          </Text>
                        )}
                      </Flex>
                    );
                  })}
                </Flex>

                {tool.registered_at && (
                  <Text fontSize="small" variation="secondary">
                    Registered: {new Date(tool.registered_at).toLocaleString()}
                  </Text>
                )}
              </Flex>
            </Card>
          )}
        </Collection>

        <Card variation="elevated">
          <Flex direction="column" gap="0.5rem">
            <Heading level={5}>Security Notes</Heading>
            <Text fontSize="small">
              • Secrets are stored encrypted in AWS Secrets Manager
            </Text>
            <Text fontSize="small">
              • Changes take effect immediately for all tool invocations
            </Text>
            <Text fontSize="small">
              • Only users with appropriate IAM permissions can view or modify secrets
            </Text>
            <Text fontSize="small">
              • API keys are masked for security - click Edit to view or modify
            </Text>
          </Flex>
        </Card>
      </Flex>
    </View>
  );
};

export default ToolSecrets;