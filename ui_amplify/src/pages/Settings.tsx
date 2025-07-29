import React from 'react';
import { 
  Heading, 
  Card, 
  Tabs,
  View,
  Text,
  TextField,
  Button,
  Flex,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Badge,
  Alert
} from '@aws-amplify/ui-react';
import { getCurrentConfig } from '../config/resources';

const Settings: React.FC = () => {
  const config = getCurrentConfig();

  return (
    <View>
      <Heading level={2} marginBottom="2rem">Settings</Heading>
      
      <Tabs defaultValue="resources">
        <Tabs.Item title="Resources" value="resources">
          <Card>
            <Heading level={4} marginBottom="1rem">Resource Configuration</Heading>
            <Alert variation="info" marginBottom="1rem">
              Currently using configuration file. DynamoDB-based configuration coming in Phase 2.
            </Alert>
            
            <Flex direction="column" gap="1rem">
              <TextField
                label="Agent Registry Table"
                value={config.resources.agentRegistryTable}
                isReadOnly
                descriptiveText="DynamoDB table for agent registry"
              />
              
              <TextField
                label="Tool Registry Table"
                value={config.resources.toolRegistryTable}
                isReadOnly
                descriptiveText="DynamoDB table for tool registry"
              />
              
              <TextField
                label="State Machine Prefix"
                value={config.resources.stateMachinePrefix}
                isReadOnly
                descriptiveText="Prefix for Step Functions state machines"
              />
              
              <TextField
                label="S3 Bucket"
                value={config.resources.s3BucketName}
                isReadOnly
                descriptiveText="S3 bucket for file storage"
              />
              
              <TextField
                label="CloudWatch Namespace"
                value={config.resources.cloudWatchNamespace}
                isReadOnly
                descriptiveText="CloudWatch namespace for metrics"
              />
            </Flex>
          </Card>
        </Tabs.Item>
        
        <Tabs.Item title="Secrets" value="secrets">
          <Card>
            <Heading level={4} marginBottom="1rem">Secrets Management</Heading>
            <Alert variation="warning" marginBottom="1rem">
              Only administrators can view and manage secrets. Secret values are masked for security.
            </Alert>
            
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Secret Name</TableCell>
                  <TableCell>Path</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>
                    OpenAI API Key
                    <Badge variation="info" size="small" marginLeft="0.5rem">Required</Badge>
                  </TableCell>
                  <TableCell>
                    <Text fontSize="small">{config.secrets.openAiSecretName}</Text>
                  </TableCell>
                  <TableCell>
                    <Badge variation="success">Active</Badge>
                  </TableCell>
                  <TableCell>
                    <Button size="small" variation="link">View</Button>
                  </TableCell>
                </TableRow>
                
                <TableRow>
                  <TableCell>
                    Anthropic API Key
                    <Badge variation="info" size="small" marginLeft="0.5rem">Required</Badge>
                  </TableCell>
                  <TableCell>
                    <Text fontSize="small">{config.secrets.anthropicSecretName}</Text>
                  </TableCell>
                  <TableCell>
                    <Badge variation="success">Active</Badge>
                  </TableCell>
                  <TableCell>
                    <Button size="small" variation="link">View</Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Card>
        </Tabs.Item>
        
        <Tabs.Item title="Features" value="features">
          <Card>
            <Heading level={4} marginBottom="1rem">Feature Flags</Heading>
            
            <Flex direction="column" gap="1rem">
              <Flex justifyContent="space-between" alignItems="center">
                <View>
                  <Text fontWeight="semibold">Stack Visualization</Text>
                  <Text fontSize="small" color="gray.60">
                    Enable CloudFormation stack visualization
                  </Text>
                </View>
                <Badge variation={config.features.enableStackVisualization ? "success" : undefined}>
                  {config.features.enableStackVisualization ? "Enabled" : "Disabled"}
                </Badge>
              </Flex>
              
              <Flex justifyContent="space-between" alignItems="center">
                <View>
                  <Text fontWeight="semibold">Cost Tracking</Text>
                  <Text fontSize="small" color="gray.60">
                    Track execution costs and display analytics
                  </Text>
                </View>
                <Badge variation={config.features.enableCostTracking ? "success" : undefined}>
                  {config.features.enableCostTracking ? "Enabled" : "Disabled"}
                </Badge>
              </Flex>
              
              <Flex justifyContent="space-between" alignItems="center">
                <View>
                  <Text fontWeight="semibold">Advanced Monitoring</Text>
                  <Text fontSize="small" color="gray.60">
                    Enable detailed CloudWatch metrics and dashboards
                  </Text>
                </View>
                <Badge variation={config.features.enableAdvancedMonitoring ? "success" : undefined}>
                  {config.features.enableAdvancedMonitoring ? "Enabled" : "Disabled"}
                </Badge>
              </Flex>
            </Flex>
          </Card>
        </Tabs.Item>
        
        <Tabs.Item title="History" value="history">
          <Card>
            <Heading level={4}>Configuration History</Heading>
            <Alert variation="info" marginTop="1rem">
              Configuration history will be available when using DynamoDB-based configuration.
            </Alert>
          </Card>
        </Tabs.Item>
      </Tabs>
    </View>
  );
};

export default Settings;