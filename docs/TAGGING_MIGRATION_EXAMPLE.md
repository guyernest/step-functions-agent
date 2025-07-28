# Example: Migrating Existing Stacks to Use Consistent Tagging

This document shows how to update existing stacks to use the new tagging strategy.

## Example 1: Updating SharedInfrastructureStack

### Before (No consistent tagging):
```python
from aws_cdk import Stack
from constructs import Construct

class SharedInfrastructureStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name
        # ... rest of implementation
```

### After (With base class and tagging):
```python
from .base_stack import StepFunctionsAgentStack

class SharedInfrastructureStack(StepFunctionsAgentStack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(
            scope, 
            construct_id,
            env_name=env_name,
            component="Infrastructure",  # Required component type
            **kwargs
        )
        # ... rest of implementation remains the same
```

## Example 2: Updating Long Content Stacks

### Before:
```python
from aws_cdk import Stack
from constructs import Construct

class SharedLLMWithLongContentStack(SharedLLMStack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        # ... implementation
```

### After:
```python
from .base_stack import LongContentStack
from .shared_llm_stack import SharedLLMStack

class SharedLLMWithLongContentStack(LongContentStack, SharedLLMStack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        # Initialize with proper tagging
        LongContentStack.__init__(
            self,
            scope, 
            construct_id,
            env_name=env_name,
            component="LLM",  # Component type
            **kwargs
        )
        # ... rest of implementation
```

## Example 3: Updating CDK Apps

### refactored_app.py:
```python
#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, Tags

# Import stacks (now with automatic tagging)
from stacks.shared.shared_infrastructure_stack import SharedInfrastructureStack
from stacks.shared.agent_registry_stack import AgentRegistryStack
from stacks.shared.shared_llm_stack import SharedLLMStack

app = App()

# Get environment
env_name = app.node.try_get_context("env") or os.getenv("CDK_ENV", "prod")

# Apply application-wide tags
Tags.of(app).add("Project", "StepFunctionsAgent")
Tags.of(app).add("Repository", "step-functions-agent")
Tags.of(app).add("ManagedBy", "CDK")

# AWS environment
aws_env = Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION", "eu-west-1")
)

# Deploy stacks - they will automatically get proper tags
shared_infra = SharedInfrastructureStack(
    app, 
    f"SharedInfrastructureStack-{env_name}",
    env_name=env_name,
    env=aws_env
)

agent_registry = AgentRegistryStack(
    app, 
    f"AgentRegistryStack-{env_name}",
    env_name=env_name,
    env=aws_env
)

# ... rest of app
```

### long_content_app.py:
```python
#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, Tags

# Import long content stacks
from stacks.shared.lambda_extension_layer_stack import LambdaExtensionLayerStack
from stacks.shared.shared_long_content_infrastructure_stack import SharedLongContentInfrastructureStack

app = App()

env_name = app.node.try_get_context("env") or os.getenv("CDK_ENV", "prod")

# Apply long content specific tags
Tags.of(app).add("Project", "StepFunctionsAgent")
Tags.of(app).add("Extension", "LongContent")
Tags.of(app).add("ManagedBy", "CDK")

# ... deploy stacks
```

## Testing the Migration

After updating your stacks, test the tagging:

```bash
# Deploy one stack to test
cdk deploy SharedInfrastructureStack-prod --profile CGI-PoC

# Check tags were applied
./tools/tag_based_stack_analyzer.py --app refactored --env prod

# Output should show:
# STACKS BY COMPONENT:
#   Infrastructure:
#     ✅ SharedInfrastructureStack-prod [CREATE_COMPLETE]
#        Tags: {'ManagedBy': 'CDK', 'Project': 'StepFunctionsAgent'}
```

## Gradual Migration Approach

If you don't want to redeploy everything at once:

1. **Phase 1**: Update base infrastructure stacks
   ```bash
   cdk deploy SharedInfrastructureStack-prod AgentRegistryStack-prod SharedLLMStack-prod
   ```

2. **Phase 2**: Update tool stacks
   ```bash
   cdk deploy *ToolStack-prod
   ```

3. **Phase 3**: Update agent stacks
   ```bash
   cdk deploy *AgentStack-prod
   ```

4. **Phase 4**: Deploy long content with proper tags
   ```bash
   cdk deploy --app 'python long_content_app.py' --all
   ```

## Verification Commands

```bash
# List all stacks with new tags
aws cloudformation describe-stacks --profile CGI-PoC --region eu-west-1 \
  --query 'Stacks[?Tags[?Key==`Application` && Value==`StepFunctionsAgent`]].{Name:StackName,Status:StackStatus}' \
  --output table

# Find stacks missing proper tags
./tools/tag_based_stack_analyzer.py --tag ManagedBy=CDK --output json | \
  jq '.stacks_by_component.Unknown[]?.name'
```

## Benefits After Migration

1. **Clean Deployment State Analysis**:
   ```bash
   ./tools/tag_based_stack_analyzer.py --app refactored --env prod
   ```

2. **Easy Cost Tracking**:
   - AWS Cost Explorer can group by Application tag
   - Filter costs by Component (Tool vs Agent vs Infrastructure)

3. **Better IAM Policies**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": "cloudformation:*",
       "Resource": "*",
       "Condition": {
         "StringEquals": {
           "aws:ResourceTag/Application": "StepFunctionsAgent",
           "aws:ResourceTag/Environment": "dev"
         }
       }
     }]
   }
   ```

4. **Automated Discovery**:
   - Tools can find all related stacks
   - No hardcoded stack names needed
   - Support for multiple deployments