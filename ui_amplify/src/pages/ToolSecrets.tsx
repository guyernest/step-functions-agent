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

interface SecretValues {
  [toolName: string]: {
    [key: string]: string;
  };
}

const ToolSecrets: React.FC = () => {
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
      // Load tool secrets directly from Secrets Manager via GraphQL API
      // The consolidated secret at /ai-agent/tool-secrets/{env} contains all tools
      // as top-level keys, so we don't need a separate registry
      const valuesResult = await client.graphql({
        query: `
          query GetToolSecretValues {
            getToolSecretValues
          }
        `
      }) as any;

      const valuesData = valuesResult.data?.getToolSecretValues;
      const parsedData = typeof valuesData === 'string' ? JSON.parse(valuesData) : valuesData;
      if (parsedData?.success && parsedData?.values) {
        // Filter out the placeholder entry
        const filteredValues = Object.keys(parsedData.values).reduce((acc, key) => {
          if (key !== 'placeholder') {
            acc[key] = parsedData.values[key];
          }
          return acc;
        }, {} as any);

        setSecretValues(filteredValues);
        // Don't populate tempValues with masked values - start empty for editing
        setTempValues({});
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
    // Initialize empty temp values for this tool when starting edit
    if (!tempValues[toolName]) {
      setTempValues({ ...tempValues, [toolName]: {} });
    }
  };

  const handleCancel = (toolName: string) => {
    setEditMode({ ...editMode, [toolName]: false });
    // Clear temp values on cancel
    setTempValues({
      ...tempValues,
      [toolName]: {}
    });
  };

  const handleSave = async (toolName: string) => {
    setSaving(true);
    setMessage(null);
    
    try {
      // Only send non-empty values to update (empty means keep existing)
      const secretsToUpdate = tempValues[toolName] || {};
      const filteredSecrets = Object.keys(secretsToUpdate).reduce((acc, key) => {
        if (secretsToUpdate[key] && secretsToUpdate[key].trim() !== '') {
          acc[key] = secretsToUpdate[key];
        }
        return acc;
      }, {} as any);
      
      // Only proceed if there are values to update
      if (Object.keys(filteredSecrets).length === 0) {
        setMessage({ type: 'info', text: 'No changes to save. Enter new values or cancel.' });
        setSaving(false);
        return;
      }
      
      // Update secrets via GraphQL API
      const result = await client.graphql({
        query: `
          mutation UpdateToolSecrets($toolName: String!, $secrets: AWSJSON!) {
            updateToolSecrets(toolName: $toolName, secrets: $secrets)
          }
        `,
        variables: {
          toolName,
          secrets: JSON.stringify(filteredSecrets)
        }
      }) as any;
      
      const updateData = result.data?.updateToolSecrets;
      // Parse the response if it's a string
      const parsedUpdate = typeof updateData === 'string' ? JSON.parse(updateData) : updateData;
      if (parsedUpdate?.success) {
        setSecretValues({
          ...secretValues,
          [toolName]: tempValues[toolName] || {}
        });
        setEditMode({ ...editMode, [toolName]: false });
        setMessage({ type: 'success', text: parsedUpdate.message || `Successfully updated secrets for ${toolName}` });
      } else {
        throw new Error(parsedUpdate?.error || 'Failed to update secrets');
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
          items={Object.keys(secretValues).sort()}
          type="list"
          direction="column"
          gap="1rem"
        >
          {(toolName) => (
            <Card key={toolName} variation="outlined">
              <Flex direction="column" gap="1rem">
                <Flex justifyContent="space-between" alignItems="center">
                  <Heading level={4}>{toolName}</Heading>
                  {!editMode[toolName] ? (
                    <Button onClick={() => handleEdit(toolName)} size="small">
                      Edit Secrets
                    </Button>
                  ) : (
                    <Flex gap="0.5rem">
                      <Button
                        onClick={() => handleSave(toolName)}
                        variation="primary"
                        size="small"
                        isLoading={saving}
                      >
                        Save
                      </Button>
                      <Button
                        onClick={() => handleCancel(toolName)}
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
                  {(() => {
                    const keys = Object.keys(secretValues[toolName] || {}).sort();

                    if (keys.length === 0) {
                      return (
                        <Text variation="secondary" fontStyle="italic">
                          No secrets configured for this tool.
                        </Text>
                      );
                    }

                    return keys.map((key) => {
                      const isEditing = editMode[toolName];
                      const currentValue = isEditing
                        ? (tempValues[toolName]?.[key] || '') // Empty for new input when editing
                        : (secretValues[toolName]?.[key] || ''); // Masked value when viewing
                      const isPlaceholder = currentValue && currentValue.startsWith('PLACEHOLDER_');
                      const fieldKey = `${toolName}-${key}`;

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

                          {editMode[toolName] ? (
                            <Flex alignItems="center" gap="0.5rem">
                              <TextField
                                label=""
                                value={currentValue}
                                onChange={(e) => handleSecretChange(toolName, key, e.target.value)}
                                type={showPasswords[fieldKey] ? "text" : "password"}
                                placeholder={`Enter new ${key} (leave empty to keep current)`}
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
                    });
                  })()}
                </Flex>
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