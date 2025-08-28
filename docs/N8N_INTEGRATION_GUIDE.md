# n8n Integration Guide for Step Functions Agent Framework

## Table of Contents
- [Overview](#overview)
- [Integration Architecture](#integration-architecture)
- [Integration Options Comparison](#integration-options-comparison)
- [MCP Server Approach (Recommended)](#mcp-server-approach-recommended)
- [Implementation Roadmap](#implementation-roadmap)
- [Quick Start](#quick-start)
- [Benefits](#benefits)
- [Next Steps](#next-steps)

## Overview

This guide describes the integration between n8n (workflow automation platform) and the Step Functions Agent Framework, enabling users to invoke AI agents from within n8n workflows. The integration allows seamless orchestration of AI agents alongside other automation tasks, combining the visual workflow capabilities of n8n with the power of Step Functions-based AI agents.

### Key Capabilities
- Execute AI agents from n8n workflows
- Monitor agent execution status
- Retrieve and process agent results
- Chain multiple agents in complex workflows
- Integrate agent outputs with other n8n nodes

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        n8n Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Trigger] → [MCP Node] → [Process] → [Output]              │
│                   ↓                                          │
└───────────────────┼──────────────────────────────────────────┘
                    │ HTTPS/WebSocket
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server                               │
├─────────────────────────────────────────────────────────────┤
│  • Authentication Layer (API Key/OAuth)                      │
│  • Request Router                                            │
│  • Agent Discovery                                           │
│  • Execution Management                                      │
│  • Status Monitoring                                         │
└───────────────────┼──────────────────────────────────────────┘
                    │ GraphQL/AWS SDK
                    ↓
┌─────────────────────────────────────────────────────────────┐
│              Step Functions + Lambda                         │
├─────────────────────────────────────────────────────────────┤
│  • Agent State Machines                                      │
│  • Tool Lambda Functions                                     │
│  • DynamoDB Registries                                       │
│  • CloudWatch Monitoring                                     │
└─────────────────────────────────────────────────────────────┘
```

## Integration Options Comparison

| Approach | Complexity | User Experience | Maintenance | Reusability | Time to Deploy |
|----------|-----------|-----------------|-------------|-------------|----------------|
| **Webhook Bridge** | Medium | Complex (multiple nodes) | Per-endpoint updates | n8n only | 1 week |
| **Custom n8n Node** | High | Simple (drag & drop) | Version dependencies | n8n only | 3 weeks |
| **Direct Step Functions** | Low | Technical | Manual | Limited | 2-3 days |
| **MCP Server** ✓ | Medium | Simple | Protocol-based | Universal | 2 weeks |

## MCP Server Approach (Recommended)

The Model Context Protocol (MCP) server approach provides a standardized, reusable interface for AI agent integration.

### Architecture Benefits

1. **Protocol Standardization**
   - Compatible with any MCP client (n8n, Claude Desktop, VSCode, etc.)
   - Self-documenting API with schemas
   - Consistent error handling

2. **Simplified Async Operations**
   - Built-in polling mechanisms
   - Progress updates and partial results
   - Automatic retry logic

3. **Enhanced Security**
   - Single authentication point
   - API key management
   - Rate limiting and quotas

4. **Tool Discovery**
   - Dynamic agent listing
   - Schema validation
   - Capability negotiation

### Core MCP Tools

#### 1. `start_agent`
Initiates an AI agent execution with specified input.

**Parameters:**
- `agent_name` (string): Name of the agent to execute
- `input_message` (string): User query or task description
- `parameters` (object): Optional agent-specific parameters

**Returns:**
- `execution_id` (string): Unique execution identifier
- `status` (string): Initial status ("started")
- `estimated_time` (number): Estimated completion time in seconds

#### 2. `monitor_agent`
Checks the status of a running agent execution.

**Parameters:**
- `execution_id` (string): Execution identifier from start_agent

**Returns:**
- `status` (string): Current status (running/completed/failed)
- `progress` (number): Completion percentage (0-100)
- `message` (string): Current processing step

#### 3. `get_agent_results`
Retrieves the complete results of an agent execution.

**Parameters:**
- `execution_id` (string): Execution identifier

**Returns:**
- `result` (object): Agent output and response
- `tools_used` (array): List of tools invoked
- `execution_time` (number): Total execution time in milliseconds
- `tokens_used` (object): Token usage statistics

#### 4. `list_available_agents`
Returns all available agents with their capabilities.

**Returns:**
- `agents` (array): List of agent configurations
  - `name` (string): Agent identifier
  - `description` (string): Agent purpose
  - `tools` (array): Available tools
  - `llm_model` (string): LLM configuration

### MCP Server Implementation Stack

```
MCP Server (Lambda/ECS)
├── Authentication Layer
│   ├── API Key Validation
│   ├── OAuth Token Handler
│   └── Rate Limiter
├── Request Router
│   ├── Tool Dispatcher
│   ├── Schema Validator
│   └── Error Handler
├── Agent Integration
│   ├── Step Functions Client
│   ├── DynamoDB Client
│   └── CloudWatch Client
└── Response Manager
    ├── Result Formatter
    ├── Status Cache
    └── WebSocket Handler
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Deploy MCP server infrastructure
- [ ] Implement core MCP tools (start, monitor, get results)
- [ ] Set up API key authentication
- [ ] Create DynamoDB state tracking

### Phase 2: n8n Integration (Week 2)
- [ ] Create n8n HTTP request workflow template
- [ ] Implement MCP discovery endpoint
- [ ] Add comprehensive error handling
- [ ] Test with existing agents

### Phase 3: Enhanced Features (Week 3)
- [ ] Add WebSocket support for real-time updates
- [ ] Implement tool-level access (bypass agents)
- [ ] Add usage analytics and cost tracking
- [ ] Create monitoring dashboard

### Phase 4: Production Readiness (Week 4)
- [ ] Security hardening and penetration testing
- [ ] Performance optimization
- [ ] Documentation and training materials
- [ ] Deployment automation

## Quick Start

### Prerequisites
1. AWS Account with Step Functions agents deployed
2. n8n instance (self-hosted or cloud)
3. API key for authentication

### Step 1: Deploy MCP Server
```bash
# Clone the repository
git clone <repository-url>

# Deploy MCP server stack
cdk deploy MCPServerStack-prod

# Note the MCP endpoint URL
# Example: https://mcp-api.example.com
```

### Step 2: Configure n8n
1. Open n8n workflow editor
2. Add HTTP Request node
3. Configure authentication:
   - Type: Header Auth
   - Header Name: `x-api-key`
   - Header Value: Your API key

### Step 3: Create Agent Workflow
```json
{
  "nodes": [
    {
      "name": "Start Agent",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://mcp-api.example.com/tools/start_agent",
        "method": "POST",
        "body": {
          "agent_name": "sql-agent",
          "input_message": "{{ $json.query }}"
        }
      }
    },
    {
      "name": "Wait for Completion",
      "type": "n8n-nodes-base.wait",
      "parameters": {
        "unit": "seconds",
        "amount": 5
      }
    },
    {
      "name": "Get Results",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://mcp-api.example.com/tools/get_agent_results",
        "method": "POST",
        "body": {
          "execution_id": "{{ $node['Start Agent'].json.execution_id }}"
        }
      }
    }
  ]
}
```

## Benefits

### For Developers
- **Single Integration Point**: One MCP server works with multiple clients
- **Protocol Stability**: Changes don't break existing integrations
- **Reduced Complexity**: No need to understand Step Functions internals

### For Users
- **Visual Workflows**: Drag-and-drop agent integration
- **Error Recovery**: Automatic retries and fallbacks
- **Progress Monitoring**: Real-time execution status

### For Operations
- **Centralized Monitoring**: All agent calls through one service
- **Security Control**: Single point for authentication and authorization
- **Cost Management**: Usage tracking and optimization

## Next Steps

1. Review the [MCP Server Implementation Guide](./MCP_SERVER_IMPLEMENTATION.md) for technical details
2. Follow the [n8n Configuration Guide](./N8N_CONFIGURATION_GUIDE.md) for setup instructions
3. Understand the [Authentication Architecture](./AUTHENTICATION_ARCHITECTURE.md) for security setup
4. Deploy the MCP server using provided CloudFormation/CDK templates
5. Test with sample workflows in the examples directory

## Support and Resources

- **Documentation**: See additional guides in this directory
- **Examples**: Check `/examples/n8n-workflows/` for templates
- **Issues**: Report bugs via GitHub Issues
- **Community**: Join our Discord for discussions

## Appendix

### Glossary
- **MCP**: Model Context Protocol - Anthropic's standard for AI tool integration
- **n8n**: Open-source workflow automation platform
- **Step Functions**: AWS service for orchestrating distributed applications
- **Agent**: AI-powered workflow that uses LLMs and tools
- **Tool**: Specific capability available to agents (database, web search, etc.)

### Related Documentation
- [Step Functions Agent Framework README](../README.md)
- [Tool Development Guide](../docs/TOOL_DEVELOPMENT.md)
- [Agent Creation Guide](../docs/AGENT_CREATION.md)
- [AWS Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)