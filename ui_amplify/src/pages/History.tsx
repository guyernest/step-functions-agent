import React, { useState } from 'react';
import { 
  Heading, 
  Card, 
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Badge,
  SearchField,
  SelectField,
  Flex,
  View,
  Text,
  Button,
  Loader,
  Alert
} from '@aws-amplify/ui-react';
import { useExecutions } from '../hooks/useExecutions';

interface StepFunctionExecution {
  executionArn: string;
  name: string;
  stateMachineArn: string;
  status: string;
  startDate: string;
  stopDate?: string;
  input?: any;
  output?: any;
  error?: string;
  agentName?: string; // Added by Lambda for convenience
}

const History: React.FC = () => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Fetch executions from DynamoDB
  const { data: executions, isLoading, error } = useExecutions();

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCEEDED':
        return <Badge variation="success">{status}</Badge>;
      case 'FAILED':
        return <Badge variation="error">{status}</Badge>;
      case 'RUNNING':
        return <Badge variation="info">{status}</Badge>;
      case 'PENDING_APPROVAL':
        return <Badge variation="warning">PENDING APPROVAL</Badge>;
      case 'ABORTED':
        return <Badge variation="error">ABORTED</Badge>;
      case 'TIMED_OUT':
        return <Badge variation="error">TIMED OUT</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const calculateDuration = (start: string, end?: string) => {
    if (!end) return 'In Progress';
    const duration = new Date(end).getTime() - new Date(start).getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const filteredExecutions = executions?.filter((exec: StepFunctionExecution) => 
    (statusFilter === 'all' || exec.status === statusFilter) &&
    (exec.name.includes(search) || (exec.agentName || '').toLowerCase().includes(search.toLowerCase()))
  ) || [];

  return (
    <View>
      <Heading level={2} marginBottom="2rem">Execution History</Heading>
      
      <Card marginBottom="2rem">
        <Flex gap="1rem">
          <SearchField
            label="Search executions"
            placeholder="Search by ID or agent name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onClear={() => setSearch('')}
          />
          
          <SelectField
            label="Status Filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="SUCCEEDED">Succeeded</option>
            <option value="FAILED">Failed</option>
            <option value="RUNNING">Running</option>
            <option value="PENDING_APPROVAL">Pending Approval</option>
            <option value="ABORTED">Aborted</option>
            <option value="TIMED_OUT">Timed Out</option>
          </SelectField>
        </Flex>
      </Card>
      
      {error && (
        <Alert variation="error" marginBottom="1rem">
          Error loading executions: {error.message}
        </Alert>
      )}
      
      <Card>
        {isLoading ? (
          <Flex justifyContent="center" padding="2rem">
            <Loader size="large" />
          </Flex>
        ) : filteredExecutions.length === 0 ? (
          <Text textAlign="center" padding="2rem" color="gray.60">
            No executions found matching your criteria
          </Text>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Execution ID</TableCell>
                <TableCell>Agent</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Start Time</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Cost</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredExecutions.map((execution: StepFunctionExecution) => (
                <TableRow key={execution.executionArn}>
                  <TableCell>
                    <Text fontWeight="semibold">{execution.name}</Text>
                  </TableCell>
                  <TableCell>{execution.agentName || 'Unknown'}</TableCell>
                  <TableCell>{getStatusBadge(execution.status)}</TableCell>
                  <TableCell>
                    <Text fontSize="small">
                      {new Date(execution.startDate).toLocaleString()}
                    </Text>
                  </TableCell>
                  <TableCell>
                    {calculateDuration(execution.startDate, execution.stopDate)}
                  </TableCell>
                  <TableCell>
                    {/* Cost calculation would need to be implemented separately */}
                    -
                  </TableCell>
                  <TableCell>
                    <Button size="small" variation="link">
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </View>
  );
};

export default History;