# Modular Agent and Tool Deployment Design

## Overview

This document describes a configuration-based system for deploying different sets of agents and tools across multiple AWS accounts and environments. The goal is to enable flexible, customer-specific deployments without editing `app.py` directly.

## Problem Statement

Currently, all agents and tools are hardcoded in `app.py`, which means:
- Every customer/environment gets the same set of agents and tools
- Adding customer-specific agents requires editing the main deployment file
- No easy way to enable/disable agents per environment
- Difficult to maintain environment-specific configurations
- Risk of deployment conflicts when different teams work on different agents

## Design Goals

1. **Configuration-Driven**: Deployment manifest defined in YAML/JSON files
2. **Environment-Specific**: Different agent sets per account/environment
3. **Backward Compatible**: Existing deployments continue to work
4. **Simple to Understand**: Clear, declarative configuration format
5. **No Version Complexity**: Changes apply uniformly across all components

## Proposed Solution

### 1. Deployment Configuration Files

Create environment-specific deployment manifests in `config/deployments/`:

```
config/
└── deployments/
    ├── default.yaml          # Default deployment (all agents/tools)
    ├── prod.yaml             # Production environment
    ├── dev.yaml              # Development environment
    ├── customer-acme.yaml    # ACME Corp customer-specific
    └── customer-bt.yaml      # BT Wholesale customer-specific
```

### 2. Configuration Format

**Example: `config/deployments/customer-bt.yaml`**

```yaml
# Deployment Configuration for BT Wholesale Customer
deployment:
  name: customer-bt
  description: BT Wholesale customer deployment with broadband-specific agents
  environment: prod

# Infrastructure components (always deployed)
infrastructure:
  shared:
    - SharedInfrastructureStack
    - SharedLLMStack
    - AgentRegistryStack

  tools:
    - BrowserRemoteToolStack
    - AgentCoreBrowserToolsStack
    - BatchProcessorStack

  optional:
    - E2BToolStack  # Code execution (optional)

# Agents to deploy
agents:
  # Schema-driven agents with templates
  - name: broadband-availability-bt-wholesale
    stack: BroadbandAvailabilityBtWholesaleStack
    enabled: true
    depends_on:
      - SharedLLMStack
      - AgentRegistryStack
      - SharedInfrastructureStack
      - BrowserRemoteToolStack
    tags:
      customer: bt-wholesale
      use_case: broadband-checking
      template: true

  # Batch processing agent
  - name: batch-processor
    stack: BatchProcessorStack
    enabled: true
    depends_on:
      - SharedInfrastructureStack
    tags:
      use_case: batch-processing

# Tools to deploy (in addition to infrastructure tools)
tools:
  - name: sql-query
    stack: SQLToolStack
    enabled: false  # Not needed for this customer

  - name: web-search
    stack: WebSearchToolStack
    enabled: false  # Not needed for this customer
```

**Example: `config/deployments/default.yaml`**

```yaml
# Default Deployment - All Agents and Tools
deployment:
  name: default
  description: Full deployment with all agents and tools
  environment: dev

infrastructure:
  shared:
    - SharedInfrastructureStack
    - SharedLLMStack
    - AgentRegistryStack

  tools:
    - BrowserRemoteToolStack
    - AgentCoreBrowserToolsStack
    - BatchProcessorStack
    - E2BToolStack
    - SQLToolStack
    - WebSearchToolStack

agents:
  # Deploy ALL agents
  - name: web-research
    stack: WebResearchAgentUnifiedLLMStack
    enabled: true

  - name: broadband-agent
    stack: BroadbandAgentUnifiedLLMStack
    enabled: true

  - name: broadband-checker-structured
    stack: BroadbandCheckerStructuredStack
    enabled: true

  - name: broadband-availability-bt-wholesale
    stack: BroadbandAvailabilityBtWholesaleStack
    enabled: true

  # ... all other agents

tools:
  # All tools enabled by default
  - name: sql-query
    stack: SQLToolStack
    enabled: true

  - name: web-search
    stack: WebSearchToolStack
    enabled: true
```

### 3. Implementation Approach

#### Phase 1: Configuration Parser (Week 1)

Create `scripts/deployment_config.py`:

```python
"""
Deployment configuration parser and validator
"""
import yaml
from typing import Dict, List, Any
from pathlib import Path

class DeploymentConfig:
    def __init__(self, config_file: str):
        self.config_path = Path(config_file)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _validate_config(self):
        """Validate configuration structure"""
        required = ['deployment', 'infrastructure', 'agents']
        for field in required:
            if field not in self.config:
                raise ValueError(f"Missing required field: {field}")

    def get_enabled_agents(self) -> List[Dict[str, Any]]:
        """Get list of enabled agents"""
        return [
            agent for agent in self.config['agents']
            if agent.get('enabled', True)
        ]

    def get_enabled_tools(self) -> List[Dict[str, Any]]:
        """Get list of enabled tools"""
        return [
            tool for tool in self.config.get('tools', [])
            if tool.get('enabled', True)
        ]

    def get_infrastructure_stacks(self) -> List[str]:
        """Get infrastructure stack names"""
        infra = self.config['infrastructure']
        stacks = []
        stacks.extend(infra.get('shared', []))
        stacks.extend(infra.get('tools', []))
        stacks.extend(infra.get('optional', []))
        return stacks
```

#### Phase 2: Dynamic Stack Instantiation (Week 2)

Modify `app.py` to use configuration:

```python
#!/usr/bin/env python3
import aws_cdk as cdk
from scripts.deployment_config import DeploymentConfig
import importlib
import os

# Load deployment configuration
config_file = os.environ.get('DEPLOYMENT_CONFIG', 'config/deployments/default.yaml')
deployment_config = DeploymentConfig(config_file)

app = cdk.App()
environment = app.node.try_get_context("environment") or "dev"

# Track instantiated stacks for dependencies
instantiated_stacks = {}

# 1. Deploy infrastructure stacks
for stack_name in deployment_config.get_infrastructure_stacks():
    module_path, class_name = STACK_REGISTRY[stack_name]
    module = importlib.import_module(module_path)
    stack_class = getattr(module, class_name)

    stack = stack_class(
        app,
        f"{stack_name}-{environment}",
        env_name=environment,
        env=env
    )
    instantiated_stacks[stack_name] = stack

# 2. Deploy enabled agents
for agent_config in deployment_config.get_enabled_agents():
    stack_name = agent_config['stack']
    agent_name = agent_config['name']

    # Import and instantiate agent stack
    module_path, class_name = STACK_REGISTRY[stack_name]
    module = importlib.import_module(module_path)
    stack_class = getattr(module, class_name)

    agent_stack = stack_class(
        app,
        f"{stack_name}-{environment}",
        env_name=environment,
        env=env,
        description=agent_config.get('description', f"{agent_name} agent")
    )

    # Add dependencies
    for dep_name in agent_config.get('depends_on', []):
        if dep_name in instantiated_stacks:
            agent_stack.add_dependency(instantiated_stacks[dep_name])

    instantiated_stacks[stack_name] = agent_stack

app.synth()
```

#### Phase 3: Stack Registry (Week 2)

Create `config/stack_registry.py`:

```python
"""
Registry mapping stack names to Python modules and classes
"""

STACK_REGISTRY = {
    # Infrastructure
    'SharedInfrastructureStack': ('stacks.shared.shared_infrastructure_stack', 'SharedInfrastructureStack'),
    'SharedLLMStack': ('stacks.shared.shared_llm_stack', 'SharedLLMStack'),
    'AgentRegistryStack': ('stacks.shared.agent_registry_stack', 'AgentRegistryStack'),

    # Tools
    'BrowserRemoteToolStack': ('stacks.tools.browser_remote_tool_stack', 'BrowserRemoteToolStack'),
    'AgentCoreBrowserToolsStack': ('stacks.tools.agentcore_browser_tools_stack', 'AgentCoreBrowserToolsStack'),
    'BatchProcessorStack': ('stacks.tools.batch_processor_stack', 'BatchProcessorStack'),
    'E2BToolStack': ('stacks.tools.e2b_tool_stack', 'E2BToolStack'),
    'SQLToolStack': ('stacks.tools.sql_tool_stack', 'SQLToolStack'),

    # Agents
    'BroadbandAvailabilityBtWholesaleStack': (
        'stacks.agents.broadband_availability_bt_wholesale_stack',
        'BroadbandAvailabilityBtWholesaleStack'
    ),
    'BroadbandCheckerStructuredStack': (
        'stacks.agents.broadband_checker_structured_stack',
        'BroadbandCheckerStructuredStack'
    ),
    'WebResearchAgentUnifiedLLMStack': (
        'stacks.agents.web_research_agent_unified_llm_stack',
        'WebResearchAgentUnifiedLLMStack'
    ),
    # ... all other agents
}
```

### 4. Deployment Workflow

#### Development

```bash
# Deploy with default configuration (all agents/tools)
cdk deploy --all

# Deploy with specific configuration
DEPLOYMENT_CONFIG=config/deployments/customer-bt.yaml cdk deploy --all

# Deploy to specific environment
cdk deploy --all -c environment=prod
```

#### Production

```bash
# Customer-specific deployment
DEPLOYMENT_CONFIG=config/deployments/customer-acme.yaml \
  cdk deploy --all -c environment=prod

# Validate configuration before deploy
python scripts/validate_deployment.py config/deployments/customer-acme.yaml

# Preview changes (dry run)
DEPLOYMENT_CONFIG=config/deployments/customer-acme.yaml \
  cdk diff --all -c environment=prod
```

### 5. Configuration Management

#### Git Repository Structure

```
config/
├── deployments/
│   ├── default.yaml          # Version controlled
│   ├── prod.yaml             # Version controlled
│   ├── dev.yaml              # Version controlled
│   └── customer-*.yaml       # Version controlled (no secrets)
├── secrets/
│   └── .gitignore            # Ignore all secrets
└── stack_registry.py         # Version controlled
```

#### Secret Management

Sensitive configuration (API keys, credentials) stored in:
- AWS Secrets Manager (preferred)
- AWS Systems Manager Parameter Store
- Environment variables (for local development)

**Never in YAML configuration files.**

### 6. Benefits

1. **Flexibility**: Each customer/environment can have different agents
2. **Maintainability**: Clear separation of configuration and code
3. **Auditability**: Configuration changes tracked in version control
4. **Safety**: Validate configuration before deployment
5. **Simplicity**: No code changes needed to add/remove agents per environment

### 7. Migration Path

#### Current State (Hardcoded)
```python
# app.py
bt_wholesale_agent = BroadbandAvailabilityBtWholesaleStack(...)
bt_wholesale_agent.add_dependency(shared_llm_stack)
```

#### Future State (Configuration-Driven)
```yaml
# config/deployments/customer-bt.yaml
agents:
  - name: broadband-availability-bt-wholesale
    stack: BroadbandAvailabilityBtWholesaleStack
    enabled: true
    depends_on:
      - SharedLLMStack
```

#### Backward Compatibility

- Keep current `app.py` as fallback
- If no configuration file specified, use `default.yaml` (all agents)
- Existing deployments continue to work unchanged

### 8. Future Enhancements

#### Configuration Validation

```bash
# Validate before deployment
python scripts/validate_deployment.py config/deployments/customer-bt.yaml

# Check for:
# - Missing dependencies
# - Invalid stack names
# - Circular dependencies
# - Required infrastructure stacks
```

#### UI Integration

Add deployment configuration management to the UI:
- View current deployment configuration
- Enable/disable agents per environment
- Validate changes before applying
- Deploy specific configurations from UI

#### Configuration Templates

```bash
# Generate configuration from existing deployment
python scripts/generate_config.py --from-deployment prod \
  --output config/deployments/new-customer.yaml

# Copy and modify template
cp config/deployments/templates/basic.yaml \
   config/deployments/customer-xyz.yaml
```

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1**: Configuration Parser | 1 week | - YAML parser<br>- Validation logic<br>- Unit tests |
| **Phase 2**: Dynamic Instantiation | 1 week | - Modified app.py<br>- Stack registry<br>- Integration tests |
| **Phase 3**: Testing & Documentation | 1 week | - End-to-end tests<br>- Migration guide<br>- Example configs |
| **Phase 4**: Rollout | 2 weeks | - Pilot with one customer<br>- Full production rollout<br>- Monitoring |

**Total Timeline**: 5 weeks

## Conclusion

This configuration-based deployment system provides flexibility for customer-specific deployments while maintaining simplicity and avoiding version complexity. Changes to schemas, templates, and agents are applied uniformly across all components, keeping the system straightforward to maintain.

## Next Steps

1. **Short-term** (This Week):
   - Add BT Wholesale agent to `app.py` directly (done)
   - Deploy for demo
   - Test template tab visibility

2. **Medium-term** (Next Month):
   - Implement configuration parser (Phase 1)
   - Build stack registry
   - Create example deployment configurations

3. **Long-term** (Next Quarter):
   - Full dynamic deployment system
   - UI integration for configuration management
   - Migration of all customer deployments to configuration-based approach
