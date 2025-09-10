# Agent Core Migration Notice

## Overview
The Agent Core runtime implementations (using Amazon Nova Act) have been moved to a separate dedicated project for better organization and maintainability.

## What Has Been Moved

### Moved to `~/projects/nova-act`:
- **Agent Core agent implementations** (`agent_core/` directory):
  - `broadband_checker_agent.py` - UK broadband availability checker
  - `shopping_agent.py` - E-commerce product search
  - `web_search_agent.py` - General web search
  - Agent deployment scripts and configurations

- **Agent Core deployment scripts** (`scripts/agent_core/` directory):
  - Deployment utilities
  - Configuration files
  - Test scripts

- **Makefile targets** for Agent Core deployment:
  - `deploy-agent-core`
  - `agentcore-*` targets (except `deploy-agentcore-tool`)
  - Agent testing and management targets

## What Remains in This Project

### Lambda Tools (Still Here):
- **`lambda/tools/agentcore_browser/`** - Lambda function that calls Agent Core runtime
  - This is the driver/router that connects to deployed Agent Core agents
  - Handles tool invocations from Step Functions agents
  - Routes to appropriate Agent Core agent based on tool name

- **`lambda/tools/nova_act_browser/`** - Direct Nova Act browser tool (if not using Agent Core)

### CDK Stacks (Still Here):
- **`stacks/tools/agentcore_browser_tool_stack.py`** - Deploys the Lambda tool
- **`stacks/tools/nova_act_browser_tool_stack.py`** - Alternative browser tool stack
- **Agent stacks** that use these tools (e.g., `BroadbandAgentUnifiedLLMStack`)

### Makefile Target (Still Here):
- **`make deploy-agentcore-tool`** - Deploys the Lambda tool stack

## Architecture

```
This Project (step-functions-agent)
├── Lambda Tools (drivers)
│   └── agentcore_browser → Calls Agent Core Runtime
├── CDK Stacks
│   └── Tool & Agent Stacks
└── Step Functions Agents

        ↓ API Calls

~/projects/nova-act
├── Agent Core Implementations
│   ├── broadband_checker_agent
│   ├── shopping_agent
│   └── web_search_agent
└── Deployed to Agent Core Runtime
```

## How It Works

1. **Step Functions agents** in this project use tools like `browser_broadband`
2. **Lambda tool** (`agentcore_browser`) receives the tool invocation
3. Lambda **routes** the request to the appropriate Agent Core agent
4. **Agent Core runtime** (deployed from `~/projects/nova-act`) executes the browser automation
5. Results are returned through the Lambda back to the Step Functions agent

## Migration Impact

- No functional changes - the tools work exactly the same way
- Better separation of concerns:
  - This project: Tool interfaces and Step Functions agents
  - nova-act project: Agent Core runtime implementations
- Easier maintenance and deployment of Agent Core agents
- Cleaner codebase organization

## For Developers

- To modify Lambda tools that call Agent Core: Work in this project
- To modify Agent Core agent implementations: Work in `~/projects/nova-act`
- To deploy the Lambda tool: `make deploy-agentcore-tool`
- To deploy Agent Core agents: Use the nova-act project's deployment tools