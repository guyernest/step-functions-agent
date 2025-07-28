# CDK Tagging Strategy for Step Functions Agent

This document defines a consistent tagging strategy for all CDK stacks in the Step Functions Agent project.

## Tag Schema

### Required Tags

Every stack MUST have these tags:

| Tag Key | Description | Example Values |
|---------|-------------|----------------|
| `Application` | The application name | `AIAgents`, `AIAgentsLongContent`, `AIAgentsFlexible` |
| `Environment` | Deployment environment | `dev`, `prod`, `staging` |
| `Component` | Stack component type | `Infrastructure`, `Tool`, `Agent`, `Monitoring`, `Extension`, `LLM` |

### Optional Tags

Additional tags for better organization:

| Tag Key | Description | Example Values |
|---------|-------------|----------------|
| `Owner` | Team or person responsible | `platform-team`, `john.doe` |
| `CostCenter` | Cost allocation | `engineering`, `research` |
| `DeploymentMode` | For flexible stacks | `Standalone`, `Extended`, `Hybrid` |
| `Version` | Application version | `1.0.0`, `2.1.0` |
| `ManagedBy` | Deployment method | `CDK`, `Manual` |

## Implementation in CDK

### 1. Base Stack Class with Tags

Create a base stack class that automatically applies tags:

```python
# stacks/shared/base_stack.py
from aws_cdk import Stack, Tags
from constructs import Construct

class BaseStack(Stack):
    """Base stack class with automatic tagging"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        application: str,
        component: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Apply required tags
        Tags.of(self).add("Application", application)
        Tags.of(self).add("Environment", env_name)
        Tags.of(self).add("Component", component)
        Tags.of(self).add("ManagedBy", "CDK")
        
        # Store for reference
        self.env_name = env_name
        self.application = application
        self.component = component
```

### 2. Update Existing Stacks

Update all stacks to inherit from BaseStack:

```python
# Example: stacks/shared/shared_infrastructure_stack.py
from .base_stack import BaseStack

class SharedInfrastructureStack(BaseStack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(
            scope, 
            construct_id,
            env_name=env_name,
            application="StepFunctionsAgent",
            component="Infrastructure",
            **kwargs
        )
        
        # Rest of the stack implementation...
```

### 3. Application-Level Tagging

In the CDK apps, add application-wide tags:

```python
# refactored_app.py
from aws_cdk import App, Tags

app = App()

# Apply app-wide tags
Tags.of(app).add("Project", "StepFunctionsAgent")
Tags.of(app).add("Repository", "step-functions-agent")

# Deploy stacks with consistent tags
env_name = app.node.try_get_context("env") or "prod"

# Infrastructure stacks
shared_infra = SharedInfrastructureStack(
    app, 
    f"SharedInfrastructureStack-{env_name}",
    env_name=env_name
)
```

### 4. Long Content App with Extended Tags

For extended architectures, use specific application names:

```python
# long_content_app.py
from aws_cdk import App, Tags

app = App()

# Different application tag for long content
Tags.of(app).add("Application", "StepFunctionsAgentLongContent")
Tags.of(app).add("ExtendedFrom", "StepFunctionsAgent")

# Stacks will inherit these tags
extension_layer = LambdaExtensionLayerStack(
    app,
    f"LambdaExtensionLayer-{env_name}",
    env_name=env_name,
    application="StepFunctionsAgentLongContent",
    component="Extension"
)
```

## Tag Naming Conventions

### Application Names

- **Main Application**: `AIAgents`
- **Long Content Extension**: `AIAgentsLongContent`
- **Flexible Deployment**: `AIAgentsFlexible`
- **Test/Demo Apps**: `AIAgentsTest`

### Component Types

- **Infrastructure**: Shared resources (DynamoDB, Secrets)
- **Tool**: Tool Lambda functions
- **Agent**: Step Functions state machines
- **Monitoring**: Dashboards and alarms
- **Extension**: Lambda layers and extensions
- **LLM**: LLM-specific functions

## Using Tags for Analysis

### Find All Stacks for an Application

```bash
# Find all main application stacks
./tag_based_stack_analyzer.py --app main --env prod

# Find all long content stacks
./tag_based_stack_analyzer.py --app long-content --env prod

# Find legacy stacks (before tagging)
./tag_based_stack_analyzer.py --app legacy

# Custom tag search
./tag_based_stack_analyzer.py --tag Application=AIAgents --tag Environment=prod
```

### Find Stacks by Component

```bash
# Find all tool stacks
./tag_based_stack_analyzer.py --tag Component=Tool

# Find all agent stacks in prod
./tag_based_stack_analyzer.py --tag Component=Agent --tag Environment=prod
```

## Migration Strategy

If you need to update existing stacks with proper tags:

### Option 1: Update in Place

1. Add tagging code to existing stacks
2. Run `cdk deploy` to update tags
3. Verify with the analyzer tool

### Option 2: Clean Redeploy

1. Export any critical data
2. Delete existing stacks: `cdk destroy --all`
3. Deploy with new tagging: `cdk deploy --all`

### Option 3: Gradual Migration

1. Tag new stacks properly
2. Update existing stacks during regular maintenance
3. Use both tag-based and name-based discovery during transition

## Benefits of This Approach

1. **Consistent Discovery**: Find all related stacks regardless of naming
2. **Multi-App Support**: Handle extended architectures cleanly
3. **Cost Tracking**: Use tags for AWS Cost Explorer
4. **Access Control**: IAM policies based on tags
5. **Automation**: Tools can discover stacks programmatically

## Example Tag Sets

### Main Infrastructure Stack
```
Application: StepFunctionsAgent
Environment: prod
Component: Infrastructure
ManagedBy: CDK
```

### Long Content Agent Stack
```
Application: StepFunctionsAgentLongContent
Environment: prod
Component: Agent
ExtendedFrom: StepFunctionsAgent
ManagedBy: CDK
```

### Flexible Deployment Stack
```
Application: StepFunctionsAgentFlexible
Environment: dev
Component: Tool
DeploymentMode: Hybrid
ManagedBy: CDK
```

## Enforcement

Consider adding a pre-deployment check:

```python
# tools/verify_tags.py
def verify_stack_tags(stack):
    """Verify stack has required tags before deployment"""
    required_tags = ["Application", "Environment", "Component"]
    
    for tag in required_tags:
        if not Tags.of(stack).tags.get(tag):
            raise ValueError(f"Stack {stack.node.id} missing required tag: {tag}")
```