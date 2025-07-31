import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Heading,
  Card,
  Badge,
  Button,
  Flex,
  View,
  Text,
  Loader,
  Alert,
  Divider,
  Tabs,
  ScrollView
} from '@aws-amplify/ui-react';
import { useExecutionDetail } from '../hooks/useExecutionDetail';
import type { ExecutionDetail as ExecutionDetailType } from '../hooks/useExecutionDetail';

interface Message {
  role: 'user' | 'assistant';
  content: string | Array<{
    type: string;
    text?: string;
    name?: string;
    input?: any;
    content?: string;
    tool_use_id?: string;
    id?: string;
  }>;
}

const ExecutionDetail: React.FC = () => {
  const { executionArn: encodedArn } = useParams<{ executionArn: string }>();
  const navigate = useNavigate();
  
  // Decode the URL-encoded executionArn
  const executionArn = encodedArn ? decodeURIComponent(encodedArn) : '';
  
  const { data: execution, isLoading, error } = useExecutionDetail(executionArn);
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    // Parse messages from execution output when available
    if (execution && execution.output) {
      try {
        const output = typeof execution.output === 'string' 
          ? JSON.parse(execution.output) 
          : execution.output;
        
        if (output && output.messages && Array.isArray(output.messages)) {
          setMessages(output.messages);
        }
      } catch (error) {
        console.error('Failed to parse execution output:', error);
      }
    }
  }, [execution]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCEEDED':
        return <Badge variation="success">{status}</Badge>;
      case 'FAILED':
        return <Badge variation="error">{status}</Badge>;
      case 'RUNNING':
        return <Badge variation="info">{status}</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const formatDuration = (start: string, end?: string) => {
    if (!end) return 'In Progress';
    const duration = new Date(end).getTime() - new Date(start).getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatToolResult = (content: string) => {
    try {
      const result = JSON.parse(content);
      if (result.answer) {
        return (
          <View className="bg-blue-50 p-3 rounded my-2">
            {result.answer.split('\n').map((line: string, idx: number) => 
              line.trim() && <Text key={idx} marginBottom="0.5rem">{line}</Text>
            )}
          </View>
        );
      }
      return (
        <View className="bg-blue-50 p-3 rounded">
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </View>
      );
    } catch {
      return <Text>{content}</Text>;
    }
  };

  const renderMessageContent = (content: Message['content']) => {
    if (typeof content === 'string') {
      return <Text>{content}</Text>;
    }

    return content.map((item, index) => {
      if (item.type === 'text') {
        return <Text key={index} marginBottom="0.5rem">{item.text}</Text>;
      }
      
      if (item.type === 'tool_use') {
        return (
          <Card key={index} backgroundColor="gray.90" color="white" marginBottom="1rem">
            <Text fontWeight="bold">🔧 Using tool: {item.name}</Text>
            <View marginTop="0.5rem">
              <pre style={{ fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(item.input, null, 2)}
              </pre>
            </View>
          </Card>
        );
      }
      
      if (item.type === 'tool_result') {
        return (
          <View key={index} marginBottom="1rem">
            <Text fontWeight="bold" marginBottom="0.5rem">📊 Tool Result:</Text>
            {formatToolResult(item.content || '')}
          </View>
        );
      }
      
      return null;
    });
  };

  const ChatMessage = ({ msg }: { msg: Message }) => {
    const isUser = msg.role === 'user';
    const bgColor = isUser ? 'blue.60' : 'gray.10';
    const textColor = isUser ? 'white' : 'black';
    const alignment = isUser ? 'flex-end' : 'flex-start';

    // Special handling for user tool results
    if (isUser && Array.isArray(msg.content) && 
        msg.content.every(item => item.type === 'tool_result')) {
      return (
        <Flex justifyContent={alignment} marginBottom="1rem">
          <Card 
            maxWidth="80%" 
            backgroundColor={bgColor} 
            color={textColor}
            padding="1rem"
          >
            <Text fontWeight="bold" marginBottom="0.5rem">User Tool Result</Text>
            {renderMessageContent(msg.content)}
          </Card>
        </Flex>
      );
    }

    return (
      <Flex justifyContent={alignment} marginBottom="1rem">
        <Card 
          maxWidth="80%" 
          backgroundColor={bgColor} 
          color={textColor}
          padding="1rem"
        >
          <Text fontWeight="bold" marginBottom="0.5rem">
            {msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}
          </Text>
          {renderMessageContent(msg.content)}
        </Card>
      </Flex>
    );
  };

  if (isLoading) {
    return (
      <Flex justifyContent="center" alignItems="center" height="400px">
        <Loader size="large" />
      </Flex>
    );
  }

  if (error) {
    return (
      <Alert variation="error">
        Error loading execution details: {error.message}
      </Alert>
    );
  }

  if (!execution) {
    return (
      <Alert variation="warning">
        Execution not found
      </Alert>
    );
  }

  return (
    <View>
      <Flex justifyContent="space-between" alignItems="center" marginBottom="2rem">
        <Heading level={2}>Execution Details</Heading>
        <Button onClick={() => navigate('/history')}>
          ← Back to History
        </Button>
      </Flex>

      {/* Execution Summary */}
      <Card marginBottom="2rem">
        <Heading level={4}>Summary</Heading>
        <Divider marginTop="1rem" marginBottom="1rem" />
        
        <Flex direction="column" gap="0.75rem">
          <Flex gap="1rem">
            <Text fontWeight="bold">Execution ID:</Text>
            <Text>{execution.name}</Text>
          </Flex>
          
          <Flex gap="1rem">
            <Text fontWeight="bold">Agent:</Text>
            <Text>{execution.agentName || 'Unknown'}</Text>
          </Flex>
          
          <Flex gap="1rem">
            <Text fontWeight="bold">Status:</Text>
            {getStatusBadge(execution.status)}
          </Flex>
          
          <Flex gap="1rem">
            <Text fontWeight="bold">Started:</Text>
            <Text>{new Date(execution.startDate).toLocaleString()}</Text>
          </Flex>
          
          {execution.stopDate && (
            <Flex gap="1rem">
              <Text fontWeight="bold">Completed:</Text>
              <Text>{new Date(execution.stopDate).toLocaleString()}</Text>
            </Flex>
          )}
          
          <Flex gap="1rem">
            <Text fontWeight="bold">Duration:</Text>
            <Text>{formatDuration(execution.startDate, execution.stopDate)}</Text>
          </Flex>
        </Flex>
      </Card>

      {/* Input/Output Details */}
      <Card marginTop="2rem">
        <Tabs
          spacing="equal"
          items={[
            {
              label: 'Input Parameters',
              value: '1',
              content: (
                <View padding="1rem">
                  <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {JSON.stringify(execution.input, null, 2)}
                  </pre>
                </View>
              )
            },
            ...(execution.output ? [{
              label: 'Raw Output',
              value: '2',
              content: (
                <View padding="1rem">
                  <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {JSON.stringify(execution.output, null, 2)}
                  </pre>
                </View>
              )
            }] : []),
            ...(execution.error ? [{
              label: 'Error Details',
              value: '3',
              content: (
                <Alert variation="error" margin="1rem">
                  {execution.error}
                </Alert>
              )
            }] : [])
          ]}
        />
      </Card>

      {/* Message Flow Visualization */}
      {messages.length > 0 && (
        <Card marginTop="2rem">
          <Heading level={4} marginBottom="1rem">Agent Conversation</Heading>
          <Divider marginBottom="1rem" />
          
          <ScrollView maxHeight="600px">
            <View padding="1rem">
              {messages.map((msg, index) => (
                <ChatMessage key={index} msg={msg} />
              ))}
            </View>
          </ScrollView>
        </Card>
      )}
    </View>
  );
};

export default ExecutionDetail;