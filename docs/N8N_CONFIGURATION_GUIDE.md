# n8n Configuration Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [n8n Installation](#n8n-installation)
- [Webhook Configuration](#webhook-configuration)
- [Authentication Setup](#authentication-setup)
- [Workflow Templates](#workflow-templates)
- [Visual Workflow Examples](#visual-workflow-examples)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Prerequisites

### Required Components
1. **n8n Instance**: Version 1.0+ (self-hosted or cloud)
2. **MCP Server**: Deployed and accessible
3. **API Key**: Generated from Step Functions Agent UI
4. **Network Access**: n8n must be able to reach MCP server endpoint

### Optional Components
- SSL Certificate for HTTPS
- Reverse proxy (nginx/Apache)
- Database for n8n persistence (PostgreSQL/MySQL)

## n8n Installation

### Option 1: Docker (Recommended)

```bash
# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - N8N_PAYLOAD_SIZE_MAX=16
    volumes:
      - n8n_data:/home/node/.n8n
      - ./custom-nodes:/home/node/.n8n/custom

volumes:
  n8n_data:
EOF

# Start n8n
docker-compose up -d

# Access n8n at http://localhost:5678
```

### Option 2: npm Global Install

```bash
# Install n8n globally
npm install n8n -g

# Start n8n
n8n start

# Or with tunnel for webhook testing
n8n start --tunnel
```

### Option 3: Cloud Instance

1. Sign up at [n8n.cloud](https://n8n.cloud)
2. Create new workflow
3. Note your webhook URLs

## Webhook Configuration

### Understanding n8n Webhooks

In n8n, webhooks appear as trigger nodes in the visual workflow:

```
[Webhook Trigger]
       ↓
   Receives: {
     "headers": {},
     "params": {},
     "query": {},
     "body": {
       "agent": "sql-agent",
       "query": "Show sales data"
     }
   }
       ↓
[Process with Agent]
```

### Setting Up Webhook Node

1. **Add Webhook Node**
   - Drag "Webhook" from Core Nodes
   - Place as first node in workflow

2. **Configure Webhook**
   ```
   Parameters:
   - HTTP Method: POST
   - Path: agent-trigger
   - Response Mode: Using 'Respond to Webhook' Node
   - Response Data: All Entries
   - Response Code: 200
   ```

3. **Get Webhook URLs**
   - Test URL: `https://n8n.example.com/webhook-test/agent-trigger`
   - Production URL: `https://n8n.example.com/webhook/agent-trigger`

## Authentication Setup

### Method 1: API Key Authentication (Recommended)

#### Step 1: Create Credentials in n8n

1. Go to **Credentials** → **Create New**
2. Select **Header Auth**
3. Configure:
   ```
   Name: Step Functions Agent API
   Header Auth:
     Name: x-api-key
     Value: your-api-key-here
   ```

#### Step 2: Use in HTTP Request Node

```json
{
  "authentication": "headerAuth",
  "credentials": {
    "headerAuth": "Step Functions Agent API"
  }
}
```

### Method 2: OAuth 2.0 with Cognito

#### Step 1: Configure OAuth Credentials

1. Create new **OAuth2 API** credential
2. Configure for AWS Cognito:
   ```
   Grant Type: Client Credentials
   Authorization URL: https://your-domain.auth.region.amazoncognito.com/oauth2/authorize
   Access Token URL: https://your-domain.auth.region.amazoncognito.com/oauth2/token
   Client ID: your-client-id
   Client Secret: your-client-secret
   Scope: agents/execute
   Authentication: Header
   ```

#### Step 3: Configure Redirect URL

Add n8n OAuth redirect URL to Cognito:
```
https://n8n.example.com/rest/oauth2-credential/callback
```

### Method 3: Custom Headers

For testing or simple setups:

{% raw %}
```json
{
  "headers": {
    "x-api-key": "={{$credentials.apiKey}}",
    "Content-Type": "application/json"
  }
}
```
{% endraw %}

## Workflow Templates

### Basic Agent Execution Workflow

{% raw %}
```json
{
  "name": "Basic Agent Execution",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "agent-execute",
        "responseMode": "responseNode",
        "options": {}
      },
      "id": "webhook-trigger",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "https://mcp-api.example.com/tools/start_agent",
        "authentication": "genericCredentialType",
        "genericAuthType": "headerAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "tool",
              "value": "start_agent"
            },
            {
              "name": "params",
              "value": "={{ JSON.stringify({agent_name: $json.agent, input_message: $json.query}) }}"
            }
          ]
        },
        "options": {}
      },
      "id": "start-agent",
      "name": "Start Agent",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [450, 300],
      "credentials": {
        "httpHeaderAuth": {
          "id": "1",
          "name": "Step Functions Agent API"
        }
      }
    },
    {
      "parameters": {
        "unit": "seconds",
        "amount": 5
      },
      "id": "wait",
      "name": "Wait",
      "type": "n8n-nodes-base.wait",
      "typeVersion": 1,
      "position": [650, 300]
    },
    {
      "parameters": {
        "url": "https://mcp-api.example.com/tools/get_agent_results",
        "authentication": "genericCredentialType",
        "genericAuthType": "headerAuth",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "tool",
              "value": "get_agent_results"
            },
            {
              "name": "params",
              "value": "={{ JSON.stringify({execution_id: $node['Start Agent'].json.execution_id}) }}"
            }
          ]
        }
      },
      "id": "get-results",
      "name": "Get Results",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [850, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ $json }}",
        "options": {}
      },
      "id": "respond",
      "name": "Respond to Webhook",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [1050, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "Start Agent", "type": "main", "index": 0}]]
    },
    "Start Agent": {
      "main": [[{"node": "Wait", "type": "main", "index": 0}]]
    },
    "Wait": {
      "main": [[{"node": "Get Results", "type": "main", "index": 0}]]
    },
    "Get Results": {
      "main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]
    }
  }
}
```
{% endraw %}

### Advanced Polling Workflow

{% raw %}
```json
{
  "name": "Agent Execution with Polling",
  "nodes": [
    {
      "id": "trigger",
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [250, 300]
    },
    {
      "id": "start-agent",
      "name": "Start Agent",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://mcp-api.example.com/tools/start_agent",
        "method": "POST",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "tool",
              "value": "start_agent"
            },
            {
              "name": "params",
              "value": {
                "agent_name": "sql-agent",
                "input_message": "Analyze sales data"
              }
            }
          ]
        }
      },
      "position": [450, 300]
    },
    {
      "id": "set-execution-id",
      "name": "Set Execution ID",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {
          "string": [
            {
              "name": "execution_id",
              "value": "={{ $node['Start Agent'].json.execution_id }}"
            },
            {
              "name": "status",
              "value": "running"
            }
          ]
        }
      },
      "position": [650, 300]
    },
    {
      "id": "loop",
      "name": "Loop",
      "type": "n8n-nodes-base.splitInBatches",
      "parameters": {
        "batchSize": 1,
        "options": {
          "reset": false
        }
      },
      "position": [850, 300]
    },
    {
      "id": "check-status",
      "name": "Check Status",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://mcp-api.example.com/tools/monitor_agent",
        "method": "POST",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "tool",
              "value": "monitor_agent"
            },
            {
              "name": "params",
              "value": "={{ JSON.stringify({execution_id: $json.execution_id}) }}"
            }
          ]
        }
      },
      "position": [1050, 300]
    },
    {
      "id": "if-complete",
      "name": "If Complete",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.status }}",
              "operation": "equals",
              "value2": "completed"
            }
          ]
        }
      },
      "position": [1250, 300]
    },
    {
      "id": "wait-and-retry",
      "name": "Wait 5s",
      "type": "n8n-nodes-base.wait",
      "parameters": {
        "amount": 5,
        "unit": "seconds"
      },
      "position": [1250, 500]
    },
    {
      "id": "get-final-results",
      "name": "Get Final Results",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://mcp-api.example.com/tools/get_agent_results",
        "method": "POST",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "tool",
              "value": "get_agent_results"
            },
            {
              "name": "params",
              "value": "={{ JSON.stringify({execution_id: $json.execution_id, include_metadata: true}) }}"
            }
          ]
        }
      },
      "position": [1450, 300]
    }
  ],
  "connections": {
    "Manual Trigger": {
      "main": [[{"node": "Start Agent"}]]
    },
    "Start Agent": {
      "main": [[{"node": "Set Execution ID"}]]
    },
    "Set Execution ID": {
      "main": [[{"node": "Loop"}]]
    },
    "Loop": {
      "main": [[{"node": "Check Status"}]]
    },
    "Check Status": {
      "main": [[{"node": "If Complete"}]]
    },
    "If Complete": {
      "main": [
        [{"node": "Get Final Results"}],
        [{"node": "Wait 5s"}]
      ]
    },
    "Wait 5s": {
      "main": [[{"node": "Loop"}]]
    }
  }
}
```
{% endraw %}

## Visual Workflow Examples

### Simple Agent Call
```
[Webhook] → [Start Agent] → [Wait 10s] → [Get Results] → [Respond]
```

### With Error Handling
```
[Webhook] → [Start Agent] → [IF: Success?]
                                ├─Yes→ [Get Results] → [Format] → [Respond]
                                └─No→ [Error Handler] → [Notify] → [Respond Error]
```

### Multi-Agent Chain
```
[Trigger] → [SQL Agent] → [Parse Data] → [Research Agent] → [Combine Results] → [Email]
```

### Parallel Agents
```
[Webhook] ─┬→ [Agent 1] ─┐
           ├→ [Agent 2] ─┼→ [Merge Results] → [Respond]
           └→ [Agent 3] ─┘
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Webhook Not Receiving Data
**Problem**: Webhook URL not accessible
**Solution**: 
- Check firewall rules
- Use n8n tunnel for testing: `n8n start --tunnel`
- Verify webhook URL in logs

#### 2. Authentication Failures
**Problem**: 401 Unauthorized errors
**Solution**:
```javascript
// Check headers in Function node
console.log($input.all()[0].json.headers);

// Verify API key
if (!$input.all()[0].json.headers['x-api-key']) {
  throw new Error('API key missing');
}
```

#### 3. Timeout Issues
**Problem**: Agent execution takes longer than 30 seconds
**Solution**:
- Implement polling pattern (see Advanced Polling Workflow)
- Increase wait intervals
- Check agent performance

#### 4. JSON Parsing Errors
**Problem**: Invalid JSON in responses
**Solution**:
```javascript
// Use Function node to safely parse
try {
  const result = JSON.parse($input.first().json.body);
  return { json: result };
} catch (e) {
  return { json: { error: 'Invalid JSON', raw: $input.first().json.body } };
}
```

#### 5. Rate Limiting
**Problem**: 429 Too Many Requests
**Solution**:
- Add delay between requests
- Implement exponential backoff
- Use SplitInBatches node for bulk processing

### Debug Mode

Enable debug logging in n8n:

```bash
# Docker
docker run -it --rm \
  -p 5678:5678 \
  -e N8N_LOG_LEVEL=debug \
  -e N8N_LOG_OUTPUT=console \
  n8nio/n8n

# npm
N8N_LOG_LEVEL=debug n8n start
```

### Testing Webhooks

Use curl to test webhook endpoints:

```bash
# Test webhook trigger
curl -X POST https://n8n.example.com/webhook-test/agent-trigger \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "sql-agent",
    "query": "Show me sales data"
  }'

# Test with authentication
curl -X POST https://mcp-api.example.com/tools/list_available_agents \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_available_agents"}'
```

## Best Practices

### 1. Error Handling
Always include error handling nodes:
```javascript
// Error Handler Function node
if ($input.first().json.error) {
  throw new Error($input.first().json.error);
}
return $input.all();
```

### 2. Timeout Management
Set reasonable timeouts for agent execution:
- Simple queries: 30 seconds
- Complex analysis: 2-5 minutes
- Use polling for long-running tasks

### 3. Data Validation
Validate input before sending to agents:
```javascript
// Validation Function node
const required = ['agent_name', 'query'];
const input = $input.first().json;

for (const field of required) {
  if (!input[field]) {
    throw new Error(`Missing required field: ${field}`);
  }
}

return $input.all();
```

### 4. Logging and Monitoring
Add logging nodes for debugging:
```javascript
// Logger Function node
console.log('Agent execution started:', {
  timestamp: new Date().toISOString(),
  agent: $input.first().json.agent_name,
  execution_id: $input.first().json.execution_id
});

return $input.all();
```

### 5. Credential Security
- Never hardcode API keys
- Use n8n credential manager
- Rotate keys regularly
- Limit key permissions

### 6. Workflow Organization
- Use sticky notes for documentation
- Group related nodes
- Use consistent naming
- Add descriptions to nodes

### 7. Performance Optimization
- Cache agent results when possible
- Use conditional nodes to skip unnecessary steps
- Batch similar requests
- Implement circuit breakers for failing services

## Advanced Features

### Custom MCP Node (Future)

```javascript
// Custom n8n node for MCP
export class MCPAgent implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'MCP Agent',
    name: 'mcpAgent',
    group: ['transform'],
    version: 1,
    description: 'Execute Step Functions agents via MCP',
    defaults: {
      name: 'MCP Agent',
    },
    inputs: ['main'],
    outputs: ['main'],
    credentials: [{
      name: 'mcpApi',
      required: true,
    }],
    properties: [
      {
        displayName: 'Agent',
        name: 'agent',
        type: 'options',
        typeOptions: {
          loadOptionsMethod: 'getAgents',
        },
        required: true,
      },
      {
        displayName: 'Query',
        name: 'query',
        type: 'string',
        required: true,
      },
      {
        displayName: 'Wait for Completion',
        name: 'waitForCompletion',
        type: 'boolean',
        default: true,
      }
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    // Implementation
  }
}
```

### Webhook Security

Add webhook validation:
```javascript
// Webhook Validation Function
const signature = $input.first().headers['x-webhook-signature'];
const body = JSON.stringify($input.first().json.body);
const expectedSignature = crypto
  .createHmac('sha256', 'webhook-secret')
  .update(body)
  .digest('hex');

if (signature !== expectedSignature) {
  throw new Error('Invalid webhook signature');
}
```

## Next Steps

1. Install n8n using preferred method
2. Import workflow templates
3. Configure API credentials
4. Test with sample agent execution
5. Customize workflows for your use case
6. Set up monitoring and alerts
7. Document your workflows

## Additional Resources

- [n8n Documentation](https://docs.n8n.io)
- [n8n Community Forum](https://community.n8n.io)
- [Workflow Templates](https://n8n.io/workflows)
- [MCP Server Documentation](./MCP_SERVER_IMPLEMENTATION.md)
- [Authentication Guide](./AUTHENTICATION_ARCHITECTURE.md)