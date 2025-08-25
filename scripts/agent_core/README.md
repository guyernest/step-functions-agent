# Agent Core Integration

This directory contains scripts and configurations for deploying agents to AWS Bedrock Agent Core service and wrapping them in Step Functions state machines for integration with the hybrid agent framework.

## Overview

Agent Core provides a managed runtime for AI agents with built-in:
- Foundation model integration
- Tool calling through action groups
- Knowledge base connections
- Session management
- Observability and tracing

Our integration wraps Agent Core agents in Step Functions state machines, allowing them to be invoked using the `.sync:2` pattern alongside Lambda-based tools.

## Directory Structure

```
scripts/agent_core/
├── deploy_agent.py           # Python script for Agent Core deployment
├── configs/                  # Agent configuration files
│   └── web_search_agent.yaml # Example web search agent config
└── README.md                 # This file
```

## Prerequisites

1. **Deploy Nova Act Browser tool** (required for web search agent):
```bash
make deploy-stack STACK=NovaActBrowserToolStack-prod
```

2. **Install Python dependencies**:
```bash
pip install boto3 pyyaml
```

3. **AWS Profile Configuration**:
   - Run `assume default` before running Agent Core commands if needed
   - The Makefile uses environment variables or the profile you specify:
     - `AWS_PROFILE`: AWS profile to use (default: uses current credentials)
     - `AWS_REGION`: AWS region (default: us-west-2)
   - Example: `AWS_PROFILE=default AWS_REGION=us-west-2 make deploy-agent-core CONFIG=web_search_agent.yaml`

4. **Required AWS permissions**:
   - Bedrock Agent operations
   - IAM role creation  
   - CloudFormation stack operations
   - Step Functions state machine creation

## Usage

### Full Deployment (Recommended)

Deploy both Agent Core agent and Step Functions wrapper:

```bash
make deploy-agent-full CONFIG=web_search_agent.yaml
```

This command:
1. Deploys the agent to Agent Core service
2. Creates IAM roles automatically
3. Deploys a Step Functions wrapper state machine
4. Outputs integration details for the hybrid supervisor

### Step-by-Step Deployment

1. **Deploy agent to Agent Core**:
```bash
make deploy-agent-core CONFIG=web_search_agent.yaml
```

2. **Deploy Step Functions wrapper**:
```bash
make deploy-agent-wrapper AGENT=web-search-agent
```

### Other Commands

**List deployed agents**:
```bash
make list-agent-core
```

**Test an agent**:
```bash
make test-agent-core AGENT=web-search-agent
```

**Delete an agent**:
```bash
make delete-agent-core AGENT_ID=<agent-id>
```

## Configuration Format

Agent configurations are YAML files in the `configs/` directory:

```yaml
agent_name: my-agent
description: Agent description
foundation_model: anthropic.claude-3-5-sonnet-20241022-v2:0
instruction: |
  System prompt for the agent
  
idle_timeout: 600  # seconds

action_groups:
  - name: my-tool
    description: Tool description
    lambda_arn: ${TOOL_LAMBDA_ARN}  # Replaced at deployment
    api_schema:
      openapi: "3.0.0"
      # ... OpenAPI schema
      
# Optional sections:
knowledge_bases:
  - id: kb-12345
    description: Knowledge base description
    
guardrail_id: gr-12345
guardrail_version: DRAFT

prompt_override:
  # Custom prompt configuration
```

## Integration with Hybrid Supervisor

After deployment, the wrapper state machine can be added to your hybrid supervisor configuration:

```python
agents = {
    "web_search": {
        "arn": "<wrapper-state-machine-arn>",
        "description": "Agent Core web search agent"
    }
}
```

In Step Functions ASL:

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::states:startExecution.sync:2",
  "Parameters": {
    "StateMachineArn": "<wrapper-state-machine-arn>",
    "Input": {
      "session_id.$": "$$.Execution.Name",
      "agent_config": {
        "input_text.$": "$.query"
      }
    }
  }
}
```

## Deployment Outputs

Each deployment creates several files:

- `agent-core-output-<agent-name>.json` - Agent Core deployment details
- `agent-integration-<agent-name>.json` - Complete integration information

These files contain:
- Agent ID and ARN
- Alias ID
- Wrapper state machine ARN
- Integration configuration

## Troubleshooting

1. **NovaActBrowserToolStack not found**: Deploy the tool stack first:
   ```bash
   make deploy-stack STACK=NovaActBrowserToolStack-prod
   ```

2. **Agent already exists**: The deployment script will update existing agents automatically

3. **IAM role issues**: Ensure your AWS credentials have permissions to create IAM roles

4. **State machine deployment fails**: Check CloudFormation stack events:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name AgentCoreWrapper-<agent-name>-prod
   ```

## Environment Variables

- `AWS_PROFILE`: AWS profile to use (default: CGI-PoC)
- `AWS_REGION`: AWS region (default: us-west-2)
- `ENV_NAME`: Environment name (default: prod)

## Adding New Agents

1. Create a configuration file in `configs/`:
   ```bash
   cp configs/web_search_agent.yaml configs/my_agent.yaml
   ```

2. Edit the configuration with your agent details

3. Deploy:
   ```bash
   make deploy-agent-full CONFIG=my_agent.yaml
   ```

## Architecture

```
┌─────────────────────┐
│  Hybrid Supervisor  │
│  (Step Functions)   │
└──────────┬──────────┘
           │ .sync:2
           ▼
┌─────────────────────┐
│   Wrapper State     │
│     Machine         │
└──────────┬──────────┘
           │ InvokeAgent
           ▼
┌─────────────────────┐
│   Agent Core        │
│     Agent           │
└──────────┬──────────┘
           │ Action Group
           ▼
┌─────────────────────┐
│   Lambda Tool       │
│  (Nova Act Browser) │
└─────────────────────┘
```

## Best Practices

1. **Test locally first**: Use `make test-agent-core` before integrating
2. **Version control configs**: Keep agent configurations in git
3. **Use descriptive names**: Agent names should indicate their purpose
4. **Monitor costs**: Agent Core has per-request pricing
5. **Enable tracing**: All wrappers have X-Ray tracing enabled

## Limitations

- Agent Core is not yet available in CDK (using boto3 API directly)
- Some regions may not have Agent Core available
- Action groups require Lambda functions (no inline code)

## Future Enhancements

- CDK native support when available
- Automatic knowledge base creation
- Guardrail configuration management
- Multi-region deployment support