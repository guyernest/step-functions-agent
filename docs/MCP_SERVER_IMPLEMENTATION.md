# MCP Server Implementation Guide

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [MCP Protocol Specification](#mcp-protocol-specification)
- [Implementation Options](#implementation-options)
- [Python Implementation](#python-implementation)
- [TypeScript Implementation](#typescript-implementation)
- [Deployment Architecture](#deployment-architecture)
- [Testing and Validation](#testing-and-validation)
- [Monitoring and Observability](#monitoring-and-observability)

## Architecture Overview

The MCP (Model Context Protocol) server acts as a bridge between n8n workflows and Step Functions agents, providing a standardized interface for AI agent execution.

### System Components

```
┌──────────────────────────────────────────────────────┐
│                  MCP Server Core                      │
├──────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Request    │  │   Business   │  │  Response  │ │
│  │   Handler    │→ │    Logic     │→ │  Manager   │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
│         ↓                  ↓                ↓         │
│  ┌──────────────────────────────────────────────┐    │
│  │            Service Layer                      │    │
│  ├──────────────────────────────────────────────┤    │
│  │  • Step Functions Client                      │    │
│  │  • DynamoDB Client                           │    │
│  │  • CloudWatch Client                         │    │
│  │  • Secrets Manager Client                    │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

### Data Flow

1. **Request Reception**: MCP server receives tool invocation request
2. **Authentication**: Validates API key or OAuth token
3. **Validation**: Checks request schema and parameters
4. **Execution**: Initiates Step Functions execution
5. **State Management**: Tracks execution in DynamoDB
6. **Response**: Returns execution ID or results

## MCP Protocol Specification

### Tool Definitions

```json
{
  "tools": [
    {
      "name": "start_agent",
      "description": "Start an AI agent execution",
      "inputSchema": {
        "type": "object",
        "properties": {
          "agent_name": {
            "type": "string",
            "description": "Name of the agent to execute"
          },
          "input_message": {
            "type": "string",
            "description": "User query or task"
          },
          "parameters": {
            "type": "object",
            "description": "Optional agent-specific parameters"
          }
        },
        "required": ["agent_name", "input_message"]
      }
    },
    {
      "name": "monitor_agent",
      "description": "Check agent execution status",
      "inputSchema": {
        "type": "object",
        "properties": {
          "execution_id": {
            "type": "string",
            "description": "Execution ID from start_agent"
          }
        },
        "required": ["execution_id"]
      }
    },
    {
      "name": "get_agent_results",
      "description": "Retrieve agent execution results",
      "inputSchema": {
        "type": "object",
        "properties": {
          "execution_id": {
            "type": "string",
            "description": "Execution ID"
          },
          "include_metadata": {
            "type": "boolean",
            "description": "Include execution metadata",
            "default": false
          }
        },
        "required": ["execution_id"]
      }
    }
  ]
}
```

### Resource Definitions

```json
{
  "resources": [
    {
      "uri": "agents://available",
      "name": "available_agents",
      "description": "List of available AI agents",
      "mimeType": "application/json"
    },
    {
      "uri": "agents://executions",
      "name": "agent_executions",
      "description": "Recent agent executions",
      "mimeType": "application/json"
    }
  ]
}
```

## Implementation Options

### Option 1: AWS Lambda (Serverless)

**Pros:**
- Auto-scaling
- Pay-per-use pricing
- Minimal infrastructure management
- Built-in AWS service integration

**Cons:**
- 15-minute execution limit
- Cold start latency
- Limited WebSocket support

### Option 2: ECS/Fargate (Container)

**Pros:**
- Long-running connections
- WebSocket support
- Custom runtime environments
- Better for high-volume

**Cons:**
- Higher baseline cost
- More complex deployment
- Requires container management

### Option 3: API Gateway + Lambda (Hybrid)

**Pros:**
- Built-in authentication
- Request throttling
- API versioning
- CloudFront integration

**Cons:**
- 30-second timeout for synchronous calls
- Additional service layer

## Python Implementation

### Core MCP Server Class

```python
# mcp_server.py
import json
import boto3
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
import hashlib
import hmac

# AWS Clients
sfn_client = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
secrets_manager = boto3.client('secretsmanager')

@dataclass
class ExecutionState:
    execution_id: str
    agent_name: str
    status: str
    started_at: datetime
    updated_at: datetime
    result: Optional[Dict] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class StepFunctionsAgentMCPServer:
    """MCP Server implementation for Step Functions Agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.executions_table = dynamodb.Table(config['executions_table'])
        self.agents_table = dynamodb.Table(config['agents_table'])
        self.api_keys_table = dynamodb.Table(config['api_keys_table'])
        self._cache = {}
        
    async def authenticate(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Authenticate request using API key or OAuth token"""
        api_key = headers.get('x-api-key')
        
        if not api_key:
            raise AuthenticationError("No API key provided")
        
        # Check cache first
        if api_key in self._cache:
            key_data = self._cache[api_key]
            if not self._is_expired(key_data):
                return key_data
        
        # Validate against DynamoDB
        response = self.api_keys_table.get_item(
            Key={'api_key_hash': self._hash_api_key(api_key)}
        )
        
        if 'Item' not in response:
            raise AuthenticationError("Invalid API key")
        
        key_data = response['Item']
        
        # Check expiration
        if self._is_expired(key_data):
            raise AuthenticationError("API key expired")
        
        # Update cache
        self._cache[api_key] = key_data
        
        # Log usage
        await self._log_api_usage(api_key, 'authenticate')
        
        return {
            'user_id': key_data['user_id'],
            'permissions': key_data['permissions'],
            'rate_limit': key_data.get('rate_limit', 60)
        }
    
    async def start_agent(self, params: Dict[str, Any], auth: Dict[str, Any]) -> Dict[str, Any]:
        """Start a Step Functions agent execution"""
        agent_name = params['agent_name']
        input_message = params['input_message']
        parameters = params.get('parameters', {})
        
        # Validate agent exists and user has permission
        agent = await self._get_agent(agent_name)
        if not self._has_permission(auth, 'execute', agent_name):
            raise PermissionError(f"No permission to execute agent: {agent_name}")
        
        # Prepare Step Functions input
        sf_input = {
            'messages': [
                {
                    'role': 'user',
                    'content': input_message
                }
            ],
            'parameters': parameters,
            'metadata': {
                'user_id': auth['user_id'],
                'source': 'mcp_server',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Start execution
        response = sfn_client.start_execution(
            stateMachineArn=agent['state_machine_arn'],
            name=f"mcp-{agent_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            input=json.dumps(sf_input)
        )
        
        execution_id = response['executionArn'].split(':')[-1]
        
        # Store execution state
        execution_state = ExecutionState(
            execution_id=execution_id,
            agent_name=agent_name,
            status='RUNNING',
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata={
                'user_id': auth['user_id'],
                'input_message': input_message,
                'execution_arn': response['executionArn']
            }
        )
        
        await self._save_execution_state(execution_state)
        
        # Log metrics
        await self._log_metrics('agent_execution_started', agent_name)
        
        return {
            'execution_id': execution_id,
            'status': 'started',
            'agent_name': agent_name,
            'estimated_time': agent.get('average_execution_time', 30),
            'poll_interval': 5
        }
    
    async def monitor_agent(self, params: Dict[str, Any], auth: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor agent execution status"""
        execution_id = params['execution_id']
        
        # Get execution state from DynamoDB
        state = await self._get_execution_state(execution_id)
        
        if not state:
            raise ValueError(f"Execution not found: {execution_id}")
        
        # Check permission
        if state.metadata['user_id'] != auth['user_id'] and not self._is_admin(auth):
            raise PermissionError("No permission to monitor this execution")
        
        # Get latest status from Step Functions
        try:
            response = sfn_client.describe_execution(
                executionArn=state.metadata['execution_arn']
            )
            
            sf_status = response['status']
            
            # Map Step Functions status to MCP status
            status_map = {
                'RUNNING': 'running',
                'SUCCEEDED': 'completed',
                'FAILED': 'failed',
                'TIMED_OUT': 'timeout',
                'ABORTED': 'cancelled'
            }
            
            status = status_map.get(sf_status, 'unknown')
            
            # Update state if changed
            if status != state.status:
                state.status = status
                state.updated_at = datetime.now(timezone.utc)
                
                if status == 'completed' and response.get('output'):
                    state.result = json.loads(response['output'])
                elif status in ['failed', 'timeout'] and response.get('cause'):
                    state.error = response['cause']
                
                await self._save_execution_state(state)
            
            # Calculate progress (simplified)
            progress = 100 if status == 'completed' else 50 if status == 'running' else 0
            
            return {
                'execution_id': execution_id,
                'status': status,
                'progress': progress,
                'message': self._get_status_message(state),
                'updated_at': state.updated_at.isoformat()
            }
            
        except Exception as e:
            return {
                'execution_id': execution_id,
                'status': 'error',
                'error': str(e)
            }
    
    async def get_agent_results(self, params: Dict[str, Any], auth: Dict[str, Any]) -> Dict[str, Any]:
        """Get complete agent execution results"""
        execution_id = params['execution_id']
        include_metadata = params.get('include_metadata', False)
        
        # Get execution state
        state = await self._get_execution_state(execution_id)
        
        if not state:
            raise ValueError(f"Execution not found: {execution_id}")
        
        # Check permission
        if state.metadata['user_id'] != auth['user_id'] and not self._is_admin(auth):
            raise PermissionError("No permission to access this execution")
        
        # Ensure execution is complete
        if state.status not in ['completed', 'failed', 'timeout']:
            return {
                'execution_id': execution_id,
                'status': state.status,
                'message': 'Execution not yet complete'
            }
        
        # Get full output from Step Functions
        response = sfn_client.describe_execution(
            executionArn=state.metadata['execution_arn']
        )
        
        result = {
            'execution_id': execution_id,
            'status': state.status,
            'agent_name': state.agent_name,
            'started_at': state.started_at.isoformat(),
            'completed_at': state.updated_at.isoformat(),
            'execution_time_ms': int((state.updated_at - state.started_at).total_seconds() * 1000)
        }
        
        if state.status == 'completed' and response.get('output'):
            output = json.loads(response['output'])
            result.update({
                'result': output.get('result', output),
                'tools_used': output.get('tools_used', []),
                'tokens_used': output.get('tokens', {})
            })
        elif state.error:
            result['error'] = state.error
        
        if include_metadata:
            result['metadata'] = state.metadata
        
        # Log metrics
        await self._log_metrics('agent_results_retrieved', state.agent_name)
        
        return result
    
    async def list_available_agents(self, auth: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List all available agents for the user"""
        # Query agents table
        response = self.agents_table.scan(
            FilterExpression='attribute_exists(agent_name) AND status = :active',
            ExpressionAttributeValues={':active': 'active'}
        )
        
        agents = []
        for item in response.get('Items', []):
            # Check permission
            if self._has_permission(auth, 'view', item['agent_name']):
                agents.append({
                    'name': item['agent_name'],
                    'description': item.get('description', ''),
                    'version': item.get('version', 'latest'),
                    'tools': item.get('tools', []),
                    'llm_provider': item.get('llm_provider', 'anthropic'),
                    'llm_model': item.get('llm_model', 'claude-3-5-sonnet'),
                    'average_execution_time': item.get('average_execution_time', 30),
                    'cost_estimate': item.get('cost_estimate', 0.01)
                })
        
        return agents
    
    # Helper methods
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _is_expired(self, key_data: Dict) -> bool:
        """Check if API key is expired"""
        expiry = datetime.fromisoformat(key_data['expires_at'])
        return datetime.now(timezone.utc) > expiry
    
    def _has_permission(self, auth: Dict, action: str, resource: str) -> bool:
        """Check if user has permission for action on resource"""
        permissions = auth.get('permissions', [])
        return (
            f"{action}:*" in permissions or
            f"{action}:{resource}" in permissions or
            "*:*" in permissions
        )
    
    def _is_admin(self, auth: Dict) -> bool:
        """Check if user has admin permissions"""
        return "*:*" in auth.get('permissions', [])
    
    async def _get_agent(self, agent_name: str) -> Dict[str, Any]:
        """Get agent configuration from DynamoDB"""
        response = self.agents_table.get_item(
            Key={'agent_name': agent_name}
        )
        
        if 'Item' not in response:
            raise ValueError(f"Agent not found: {agent_name}")
        
        return response['Item']
    
    async def _save_execution_state(self, state: ExecutionState):
        """Save execution state to DynamoDB"""
        self.executions_table.put_item(
            Item={
                'execution_id': state.execution_id,
                'agent_name': state.agent_name,
                'status': state.status,
                'started_at': state.started_at.isoformat(),
                'updated_at': state.updated_at.isoformat(),
                'result': state.result,
                'error': state.error,
                'metadata': state.metadata,
                'ttl': int((state.updated_at + timedelta(days=7)).timestamp())
            }
        )
    
    async def _get_execution_state(self, execution_id: str) -> Optional[ExecutionState]:
        """Get execution state from DynamoDB"""
        response = self.executions_table.get_item(
            Key={'execution_id': execution_id}
        )
        
        if 'Item' not in response:
            return None
        
        item = response['Item']
        return ExecutionState(
            execution_id=item['execution_id'],
            agent_name=item['agent_name'],
            status=item['status'],
            started_at=datetime.fromisoformat(item['started_at']),
            updated_at=datetime.fromisoformat(item['updated_at']),
            result=item.get('result'),
            error=item.get('error'),
            metadata=item.get('metadata', {})
        )
    
    def _get_status_message(self, state: ExecutionState) -> str:
        """Generate human-readable status message"""
        messages = {
            'running': f"Agent {state.agent_name} is processing your request...",
            'completed': "Agent execution completed successfully",
            'failed': f"Agent execution failed: {state.error or 'Unknown error'}",
            'timeout': "Agent execution timed out",
            'cancelled': "Agent execution was cancelled"
        }
        return messages.get(state.status, "Unknown status")
    
    async def _log_metrics(self, metric_name: str, agent_name: str = None):
        """Log metrics to CloudWatch"""
        metric_data = [{
            'MetricName': metric_name,
            'Value': 1,
            'Unit': 'Count',
            'Timestamp': datetime.now(timezone.utc)
        }]
        
        if agent_name:
            metric_data[0]['Dimensions'] = [
                {'Name': 'AgentName', 'Value': agent_name}
            ]
        
        cloudwatch.put_metric_data(
            Namespace='MCPServer/Agents',
            MetricData=metric_data
        )
    
    async def _log_api_usage(self, api_key: str, operation: str):
        """Log API usage for billing and monitoring"""
        cloudwatch.put_metric_data(
            Namespace='MCPServer/API',
            MetricData=[{
                'MetricName': 'APIUsage',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'APIKeyHash', 'Value': self._hash_api_key(api_key)[:8]},
                    {'Name': 'Operation', 'Value': operation}
                ],
                'Timestamp': datetime.now(timezone.utc)
            }]
        )

class AuthenticationError(Exception):
    """Authentication failure exception"""
    pass

class PermissionError(Exception):
    """Permission denied exception"""
    pass
```

### Lambda Handler

```python
# lambda_handler.py
import json
import os
from typing import Dict, Any
from mcp_server import StepFunctionsAgentMCPServer, AuthenticationError, PermissionError

# Initialize MCP server
config = {
    'executions_table': os.environ['EXECUTIONS_TABLE'],
    'agents_table': os.environ['AGENTS_TABLE'],
    'api_keys_table': os.environ['API_KEYS_TABLE']
}

mcp_server = StepFunctionsAgentMCPServer(config)

async def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for MCP server"""
    
    try:
        # Extract headers and body
        headers = event.get('headers', {})
        body = json.loads(event.get('body', '{}'))
        
        # Authenticate request
        auth = await mcp_server.authenticate(headers)
        
        # Route to appropriate handler
        tool = body.get('tool')
        params = body.get('params', {})
        
        if tool == 'start_agent':
            result = await mcp_server.start_agent(params, auth)
        elif tool == 'monitor_agent':
            result = await mcp_server.monitor_agent(params, auth)
        elif tool == 'get_agent_results':
            result = await mcp_server.get_agent_results(params, auth)
        elif tool == 'list_available_agents':
            result = await mcp_server.list_available_agents(auth)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown tool: {tool}'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json',
                'X-MCP-Version': '1.0'
            }
        }
        
    except AuthenticationError as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': str(e)})
        }
    
    except PermissionError as e:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': str(e)})
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

## TypeScript Implementation

### Core MCP Server Class

```typescript
// mcp-server.ts
import {
  SFNClient,
  StartExecutionCommand,
  DescribeExecutionCommand
} from '@aws-sdk/client-sfn';
import {
  DynamoDBClient,
  GetItemCommand,
  PutItemCommand
} from '@aws-sdk/client-dynamodb';
import {
  CloudWatchClient,
  PutMetricDataCommand
} from '@aws-sdk/client-cloudwatch';
import crypto from 'crypto';

interface AuthContext {
  userId: string;
  permissions: string[];
  rateLimit: number;
}

interface ExecutionState {
  executionId: string;
  agentName: string;
  status: string;
  startedAt: Date;
  updatedAt: Date;
  result?: any;
  error?: string;
  metadata?: Record<string, any>;
}

export class StepFunctionsAgentMCPServer {
  private sfnClient: SFNClient;
  private dynamoClient: DynamoDBClient;
  private cloudwatchClient: CloudWatchClient;
  private cache: Map<string, any> = new Map();

  constructor(private config: {
    executionsTable: string;
    agentsTable: string;
    apiKeysTable: string;
    region: string;
  }) {
    this.sfnClient = new SFNClient({ region: config.region });
    this.dynamoClient = new DynamoDBClient({ region: config.region });
    this.cloudwatchClient = new CloudWatchClient({ region: config.region });
  }

  async authenticate(headers: Record<string, string>): Promise<AuthContext> {
    const apiKey = headers['x-api-key'];
    
    if (!apiKey) {
      throw new AuthenticationError('No API key provided');
    }

    // Check cache
    if (this.cache.has(apiKey)) {
      const cached = this.cache.get(apiKey);
      if (!this.isExpired(cached)) {
        return cached;
      }
    }

    // Validate against DynamoDB
    const response = await this.dynamoClient.send(
      new GetItemCommand({
        TableName: this.config.apiKeysTable,
        Key: {
          api_key_hash: { S: this.hashApiKey(apiKey) }
        }
      })
    );

    if (!response.Item) {
      throw new AuthenticationError('Invalid API key');
    }

    const keyData = this.unmarshalItem(response.Item);
    
    if (this.isExpired(keyData)) {
      throw new AuthenticationError('API key expired');
    }

    const authContext: AuthContext = {
      userId: keyData.user_id,
      permissions: keyData.permissions,
      rateLimit: keyData.rate_limit || 60
    };

    // Cache for 5 minutes
    this.cache.set(apiKey, authContext);
    setTimeout(() => this.cache.delete(apiKey), 5 * 60 * 1000);

    await this.logApiUsage(apiKey, 'authenticate');

    return authContext;
  }

  async startAgent(
    params: { agentName: string; inputMessage: string; parameters?: any },
    auth: AuthContext
  ): Promise<any> {
    const { agentName, inputMessage, parameters = {} } = params;

    // Validate agent and permissions
    const agent = await this.getAgent(agentName);
    if (!this.hasPermission(auth, 'execute', agentName)) {
      throw new PermissionError(`No permission to execute agent: ${agentName}`);
    }

    // Prepare Step Functions input
    const sfInput = {
      messages: [{
        role: 'user',
        content: inputMessage
      }],
      parameters,
      metadata: {
        userId: auth.userId,
        source: 'mcp_server',
        timestamp: new Date().toISOString()
      }
    };

    // Start execution
    const response = await this.sfnClient.send(
      new StartExecutionCommand({
        stateMachineArn: agent.state_machine_arn,
        name: `mcp-${agentName}-${Date.now()}`,
        input: JSON.stringify(sfInput)
      })
    );

    const executionId = response.executionArn!.split(':').pop()!;

    // Save execution state
    const executionState: ExecutionState = {
      executionId,
      agentName,
      status: 'RUNNING',
      startedAt: new Date(),
      updatedAt: new Date(),
      metadata: {
        userId: auth.userId,
        inputMessage,
        executionArn: response.executionArn
      }
    };

    await this.saveExecutionState(executionState);
    await this.logMetrics('agent_execution_started', agentName);

    return {
      execution_id: executionId,
      status: 'started',
      agent_name: agentName,
      estimated_time: agent.average_execution_time || 30,
      poll_interval: 5
    };
  }

  async monitorAgent(
    params: { executionId: string },
    auth: AuthContext
  ): Promise<any> {
    const { executionId } = params;

    // Get execution state
    const state = await this.getExecutionState(executionId);
    
    if (!state) {
      throw new Error(`Execution not found: ${executionId}`);
    }

    // Check permission
    if (state.metadata?.userId !== auth.userId && !this.isAdmin(auth)) {
      throw new PermissionError('No permission to monitor this execution');
    }

    // Get latest status from Step Functions
    try {
      const response = await this.sfnClient.send(
        new DescribeExecutionCommand({
          executionArn: state.metadata?.executionArn
        })
      );

      const statusMap: Record<string, string> = {
        'RUNNING': 'running',
        'SUCCEEDED': 'completed',
        'FAILED': 'failed',
        'TIMED_OUT': 'timeout',
        'ABORTED': 'cancelled'
      };

      const status = statusMap[response.status!] || 'unknown';
      const progress = status === 'completed' ? 100 : 
                      status === 'running' ? 50 : 0;

      // Update state if changed
      if (status !== state.status) {
        state.status = status;
        state.updatedAt = new Date();
        
        if (status === 'completed' && response.output) {
          state.result = JSON.parse(response.output);
        } else if (['failed', 'timeout'].includes(status) && response.cause) {
          state.error = response.cause;
        }
        
        await this.saveExecutionState(state);
      }

      return {
        execution_id: executionId,
        status,
        progress,
        message: this.getStatusMessage(state),
        updated_at: state.updatedAt.toISOString()
      };

    } catch (error) {
      return {
        execution_id: executionId,
        status: 'error',
        error: (error as Error).message
      };
    }
  }

  async getAgentResults(
    params: { executionId: string; includeMetadata?: boolean },
    auth: AuthContext
  ): Promise<any> {
    const { executionId, includeMetadata = false } = params;

    // Get execution state
    const state = await this.getExecutionState(executionId);
    
    if (!state) {
      throw new Error(`Execution not found: ${executionId}`);
    }

    // Check permission
    if (state.metadata?.userId !== auth.userId && !this.isAdmin(auth)) {
      throw new PermissionError('No permission to access this execution');
    }

    // Ensure execution is complete
    if (!['completed', 'failed', 'timeout'].includes(state.status)) {
      return {
        execution_id: executionId,
        status: state.status,
        message: 'Execution not yet complete'
      };
    }

    // Get full output
    const response = await this.sfnClient.send(
      new DescribeExecutionCommand({
        executionArn: state.metadata?.executionArn
      })
    );

    const result: any = {
      execution_id: executionId,
      status: state.status,
      agent_name: state.agentName,
      started_at: state.startedAt.toISOString(),
      completed_at: state.updatedAt.toISOString(),
      execution_time_ms: state.updatedAt.getTime() - state.startedAt.getTime()
    };

    if (state.status === 'completed' && response.output) {
      const output = JSON.parse(response.output);
      result.result = output.result || output;
      result.tools_used = output.tools_used || [];
      result.tokens_used = output.tokens || {};
    } else if (state.error) {
      result.error = state.error;
    }

    if (includeMetadata) {
      result.metadata = state.metadata;
    }

    await this.logMetrics('agent_results_retrieved', state.agentName);

    return result;
  }

  // Helper methods
  private hashApiKey(apiKey: string): string {
    return crypto.createHash('sha256').update(apiKey).digest('hex');
  }

  private isExpired(keyData: any): boolean {
    const expiry = new Date(keyData.expires_at);
    return new Date() > expiry;
  }

  private hasPermission(auth: AuthContext, action: string, resource: string): boolean {
    return auth.permissions.includes(`${action}:*`) ||
           auth.permissions.includes(`${action}:${resource}`) ||
           auth.permissions.includes('*:*');
  }

  private isAdmin(auth: AuthContext): boolean {
    return auth.permissions.includes('*:*');
  }

  private getStatusMessage(state: ExecutionState): string {
    const messages: Record<string, string> = {
      'running': `Agent ${state.agentName} is processing your request...`,
      'completed': 'Agent execution completed successfully',
      'failed': `Agent execution failed: ${state.error || 'Unknown error'}`,
      'timeout': 'Agent execution timed out',
      'cancelled': 'Agent execution was cancelled'
    };
    return messages[state.status] || 'Unknown status';
  }

  // Database operations
  private async getAgent(agentName: string): Promise<any> {
    const response = await this.dynamoClient.send(
      new GetItemCommand({
        TableName: this.config.agentsTable,
        Key: { agent_name: { S: agentName } }
      })
    );

    if (!response.Item) {
      throw new Error(`Agent not found: ${agentName}`);
    }

    return this.unmarshalItem(response.Item);
  }

  private async saveExecutionState(state: ExecutionState): Promise<void> {
    await this.dynamoClient.send(
      new PutItemCommand({
        TableName: this.config.executionsTable,
        Item: this.marshalItem({
          execution_id: state.executionId,
          agent_name: state.agentName,
          status: state.status,
          started_at: state.startedAt.toISOString(),
          updated_at: state.updatedAt.toISOString(),
          result: state.result,
          error: state.error,
          metadata: state.metadata,
          ttl: Math.floor((state.updatedAt.getTime() + 7 * 24 * 60 * 60 * 1000) / 1000)
        })
      })
    );
  }

  private async getExecutionState(executionId: string): Promise<ExecutionState | null> {
    const response = await this.dynamoClient.send(
      new GetItemCommand({
        TableName: this.config.executionsTable,
        Key: { execution_id: { S: executionId } }
      })
    );

    if (!response.Item) {
      return null;
    }

    const item = this.unmarshalItem(response.Item);
    return {
      executionId: item.execution_id,
      agentName: item.agent_name,
      status: item.status,
      startedAt: new Date(item.started_at),
      updatedAt: new Date(item.updated_at),
      result: item.result,
      error: item.error,
      metadata: item.metadata
    };
  }

  // Monitoring
  private async logMetrics(metricName: string, agentName?: string): Promise<void> {
    const metricData: any = {
      MetricName: metricName,
      Value: 1,
      Unit: 'Count',
      Timestamp: new Date()
    };

    if (agentName) {
      metricData.Dimensions = [
        { Name: 'AgentName', Value: agentName }
      ];
    }

    await this.cloudwatchClient.send(
      new PutMetricDataCommand({
        Namespace: 'MCPServer/Agents',
        MetricData: [metricData]
      })
    );
  }

  private async logApiUsage(apiKey: string, operation: string): Promise<void> {
    await this.cloudwatchClient.send(
      new PutMetricDataCommand({
        Namespace: 'MCPServer/API',
        MetricData: [{
          MetricName: 'APIUsage',
          Value: 1,
          Unit: 'Count',
          Dimensions: [
            { Name: 'APIKeyHash', Value: this.hashApiKey(apiKey).substring(0, 8) },
            { Name: 'Operation', Value: operation }
          ],
          Timestamp: new Date()
        }]
      })
    );
  }

  // Utility methods for DynamoDB marshalling
  private marshalItem(item: any): any {
    const marshalled: any = {};
    for (const [key, value] of Object.entries(item)) {
      if (value === null || value === undefined) continue;
      if (typeof value === 'string') {
        marshalled[key] = { S: value };
      } else if (typeof value === 'number') {
        marshalled[key] = { N: value.toString() };
      } else if (typeof value === 'boolean') {
        marshalled[key] = { BOOL: value };
      } else if (Array.isArray(value)) {
        marshalled[key] = { L: value.map(v => this.marshalValue(v)) };
      } else if (typeof value === 'object') {
        marshalled[key] = { M: this.marshalItem(value) };
      }
    }
    return marshalled;
  }

  private marshalValue(value: any): any {
    if (typeof value === 'string') return { S: value };
    if (typeof value === 'number') return { N: value.toString() };
    if (typeof value === 'boolean') return { BOOL: value };
    if (Array.isArray(value)) return { L: value.map(v => this.marshalValue(v)) };
    if (typeof value === 'object') return { M: this.marshalItem(value) };
    return { NULL: true };
  }

  private unmarshalItem(item: any): any {
    const unmarshalled: any = {};
    for (const [key, value] of Object.entries(item)) {
      unmarshalled[key] = this.unmarshalValue(value);
    }
    return unmarshalled;
  }

  private unmarshalValue(value: any): any {
    if (value.S !== undefined) return value.S;
    if (value.N !== undefined) return parseFloat(value.N);
    if (value.BOOL !== undefined) return value.BOOL;
    if (value.NULL !== undefined) return null;
    if (value.L !== undefined) return value.L.map((v: any) => this.unmarshalValue(v));
    if (value.M !== undefined) return this.unmarshalItem(value.M);
    return null;
  }
}

export class AuthenticationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class PermissionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'PermissionError';
  }
}
```

## Deployment Architecture

### CDK Stack Definition

```typescript
// mcp-server-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';

export class MCPServerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB Tables
    const executionsTable = new dynamodb.Table(this, 'ExecutionsTable', {
      partitionKey: { name: 'execution_id', type: dynamodb.AttributeType.STRING },
      timeToLiveAttribute: 'ttl',
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST
    });

    const apiKeysTable = new dynamodb.Table(this, 'ApiKeysTable', {
      partitionKey: { name: 'api_key_hash', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST
    });

    // Lambda Function
    const mcpServerLambda = new lambda.Function(this, 'MCPServerFunction', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('lambda/mcp-server'),
      handler: 'lambda_handler.handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
      environment: {
        EXECUTIONS_TABLE: executionsTable.tableName,
        AGENTS_TABLE: agentsTable.tableName,
        API_KEYS_TABLE: apiKeysTable.tableName
      }
    });

    // Grant permissions
    executionsTable.grantReadWriteData(mcpServerLambda);
    apiKeysTable.grantReadData(mcpServerLambda);
    
    // API Gateway
    const api = new apigateway.RestApi(this, 'MCPServerAPI', {
      restApiName: 'MCP Server API',
      deployOptions: {
        stageName: 'prod',
        throttlingBurstLimit: 1000,
        throttlingRateLimit: 100
      }
    });

    const integration = new apigateway.LambdaIntegration(mcpServerLambda);
    api.root.addMethod('POST', integration);
  }
}
```

## Testing and Validation

### Unit Tests

```python
# test_mcp_server.py
import pytest
from unittest.mock import Mock, patch
from mcp_server import StepFunctionsAgentMCPServer

@pytest.fixture
def mcp_server():
    config = {
        'executions_table': 'test-executions',
        'agents_table': 'test-agents',
        'api_keys_table': 'test-api-keys'
    }
    return StepFunctionsAgentMCPServer(config)

@pytest.mark.asyncio
async def test_start_agent_success(mcp_server):
    """Test successful agent start"""
    auth = {'user_id': 'user123', 'permissions': ['execute:*']}
    params = {
        'agent_name': 'test-agent',
        'input_message': 'Test query'
    }
    
    with patch.object(mcp_server, '_get_agent') as mock_get_agent:
        mock_get_agent.return_value = {
            'agent_name': 'test-agent',
            'state_machine_arn': 'arn:aws:states:...'
        }
        
        with patch('boto3.client') as mock_client:
            mock_sfn = Mock()
            mock_sfn.start_execution.return_value = {
                'executionArn': 'arn:aws:states:region:account:execution:test-123'
            }
            mock_client.return_value = mock_sfn
            
            result = await mcp_server.start_agent(params, auth)
            
            assert result['status'] == 'started'
            assert 'execution_id' in result
```

### Integration Tests

```bash
# test_integration.sh
#!/bin/bash

# Start local MCP server
python -m mcp_server.local --port 8080 &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Test authentication
curl -X POST http://localhost:8080 \
  -H "x-api-key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_available_agents"}'

# Test agent execution
EXECUTION_ID=$(curl -X POST http://localhost:8080 \
  -H "x-api-key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"tool": "start_agent", "params": {"agent_name": "test-agent", "input_message": "Test"}}' \
  | jq -r '.execution_id')

# Monitor execution
curl -X POST http://localhost:8080 \
  -H "x-api-key: test-key-123" \
  -H "Content-Type: application/json" \
  -d "{\"tool\": \"monitor_agent\", \"params\": {\"execution_id\": \"$EXECUTION_ID\"}}"

# Cleanup
kill $SERVER_PID
```

## Monitoring and Observability

### CloudWatch Dashboard

```json
{
  "dashboardName": "MCP-Server-Monitoring",
  "dashboardBody": {
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["MCPServer/API", "APIUsage", {"stat": "Sum"}],
            ["MCPServer/Agents", "agent_execution_started", {"stat": "Sum"}],
            ["MCPServer/Agents", "agent_results_retrieved", {"stat": "Sum"}]
          ],
          "period": 300,
          "stat": "Sum",
          "region": "us-east-1",
          "title": "API Usage"
        }
      },
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/Lambda", "Duration", {"stat": "Average"}],
            [".", ".", {"stat": "p99"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "Lambda Performance"
        }
      }
    ]
  }
}
```

### Alarms

```yaml
# cloudwatch-alarms.yaml
APIErrorRate:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: MCP-Server-High-Error-Rate
    MetricName: 4XXError
    Namespace: AWS/ApiGateway
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold

HighLatency:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: MCP-Server-High-Latency
    MetricName: Duration
    Namespace: AWS/Lambda
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 5000
    ComparisonOperator: GreaterThanThreshold
```

## Security Considerations

1. **API Key Rotation**: Implement automatic key rotation every 30-90 days
2. **Rate Limiting**: Use API Gateway throttling and Lambda reserved concurrency
3. **Encryption**: Enable encryption at rest for DynamoDB and in transit with TLS
4. **Audit Logging**: Enable CloudTrail for all API calls
5. **Least Privilege**: Use fine-grained IAM policies for Lambda execution role

## Next Steps

1. Deploy the MCP server using provided CDK stack
2. Configure API keys and authentication
3. Set up monitoring dashboards
4. Test with sample n8n workflows
5. Document API endpoints for users