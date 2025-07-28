# Resource Flow and Integration Patterns

This document details how resources flow between stacks and the integration patterns used in the Step Functions Agent project.

## Resource Flow Overview

```mermaid
graph LR
    subgraph "Resource Types"
        RT1[DynamoDB Tables]
        RT2[Lambda Functions]
        RT3[Lambda Layers]
        RT4[Secrets Manager]
        RT5[IAM Roles]
        RT6[CloudWatch Logs]
        RT7[Step Functions]
    end
```

## Main Infrastructure Resource Flow

```mermaid
flowchart TB
    subgraph "Shared Resources Creation"
        A[SharedInfrastructureStack] -->|creates| A1[SharedLLMTable]
        B[AgentRegistryStack] -->|creates| B1[AgentRegistry Table]
        C[SharedLLMStack] -->|creates| C1[LLM Lambda Functions]
        C -->|creates| C2[LLM Secrets]
        C -->|creates| C3[LLM Layer]
        C -->|creates| C4[Log Group]
    end
    
    subgraph "Resource Exports"
        A1 -->|export TableName| EA1[SharedTableSharedLLMTable-{env}]
        A1 -->|export TableArn| EA2[SharedTableArnSharedLLMTable-{env}]
        B1 -->|export TableName| EB1[SharedTableAgentRegistry-{env}]
        B1 -->|export TableArn| EB2[SharedTableArnAgentRegistry-{env}]
        C1 -->|export ARNs| EC1[Shared{Provider}LambdaArn-{env}]
        C2 -->|export ARN| EC2[SharedLLMSecretArn-{env}]
        C3 -->|export ARN| EC3[SharedLLMLayerArn-{env}]
    end
    
    subgraph "Resource Consumers"
        D[Tool Stacks] -->|import| EA1
        D -->|import| EA2
        E[Agent Stacks] -->|import| EB1
        E -->|import| EB2
        E -->|import| EC1
        F[All Lambda Functions] -->|use| EC2
        F -->|use| EC3
    end
```

## Long Content Infrastructure Resource Flow

```mermaid
flowchart TB
    subgraph "Extension Layer Creation"
        A[LambdaExtensionLayerStack]
        A -->|builds with Makefile| A1[Rust Extension x86_64]
        A -->|builds with Makefile| A2[Rust Extension ARM64]
        A -->|creates| A3[Lambda Layer x86_64]
        A -->|creates| A4[Lambda Layer ARM64]
    end
    
    subgraph "Infrastructure Re-export"
        B[SharedLongContentInfrastructure]
        A3 -->|import| B
        A4 -->|import| B
        B -->|re-export| B1[SharedProxyLayerX86LongContent-{env}]
        B -->|re-export| B2[SharedProxyLayerArmLongContent-{env}]
        B -->|creates| B3[DynamoDB ContentTable]
        B3 -->|export| B4[SharedContentTableLongContent-{env}]
    end
    
    subgraph "Long Content Resources"
        C[LLM Functions]
        D[Tool Functions]
        B1 -->|layer added to| C
        B2 -->|layer added to| C
        B1 -->|layer added to| D
        B2 -->|layer added to| D
        B4 -->|permissions granted| C
        B4 -->|permissions granted| D
    end
    
    subgraph "Environment Variables"
        E[Lambda Environment]
        E -->|AWS_LAMBDA_EXEC_WRAPPER| E1[/opt/extensions/lrap-wrapper/wrapper]
        E -->|AGENT_CONTEXT_TABLE| B3
        E -->|MAX_CONTENT_SIZE| E2[Configurable Threshold]
    end
```

## Registry Integration Pattern

```mermaid
flowchart LR
    subgraph "Agent Registration Flow"
        A[Agent Stack] -->|registers| B[Agent Registry]
        A -->|provides| A1[agent_name]
        A -->|provides| A2[system_prompt]
        A -->|provides| A3[tool_configs]
        A -->|provides| A4[llm_config]
    end
    
    subgraph "Tool Registration Flow"
        C[Tool Stack] -->|registers| D[Tool Registry]
        C -->|provides| C1[tool_name]
        C -->|provides| C2[input_schema]
        C -->|provides| C3[output_schema]
        C -->|provides| C4[lambda_arn]
    end
    
    subgraph "Runtime Discovery"
        E[Step Functions] -->|queries| B
        E -->|queries| D
        E -->|resolves| F[Tool Lambda ARNs]
        E -->|resolves| G[LLM Lambda ARN]
    end
```

## Import/Export Patterns

### 1. Standard CloudFormation Export Pattern
```python
# Creating Export
CfnOutput(
    self,
    "AgentRegistryTableName",
    value=self.agent_registry_table.table_name,
    export_name=NamingConventions.stack_export_name(
        "Table", "AgentRegistry", self.env_name
    )
)

# Importing Export
self.agent_registry_table_name = Fn.import_value(
    NamingConventions.stack_export_name("Table", "AgentRegistry", self.env_name)
)
```

### 2. Direct Resource Import Pattern
```python
# Import by Table Name
self.agent_registry_table = dynamodb.Table.from_table_name(
    self,
    "ImportedAgentRegistry",
    "AgentRegistry-prod"
)

# Import by Lambda ARN
self.llm_function = lambda_.Function.from_function_arn(
    self,
    "ImportedLLM",
    "arn:aws:lambda:us-east-1:123456789:function:claude-llm-prod"
)

# Import by Secret Name
self.llm_secret = secretsmanager.Secret.from_secret_name_v2(
    self,
    "ImportedLLMSecrets",
    "/ai-agent/llm-secrets/prod"
)
```

### 3. Layer Import Pattern
```python
# Import Layer by ARN
proxy_extension_layer = lambda_.LayerVersion.from_layer_version_arn(
    self,
    "ProxyExtensionLayer",
    layer_version_arn=proxy_layer_arn
)

# Add to Lambda Function
lambda_function = lambda_.Function(
    self,
    "FunctionWithProxy",
    layers=[base_layer, proxy_extension_layer],
    environment={
        "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
        "AGENT_CONTEXT_TABLE": content_table_name
    }
)
```

## Permission Flow

```mermaid
flowchart TB
    subgraph "Agent Role Permissions"
        A[Agent IAM Role]
        A -->|invoke| B[LLM Lambda Functions]
        A -->|invoke| C[Tool Lambda Functions]
        A -->|read/write| D[Agent Registry]
        A -->|write| E[CloudWatch Logs]
        A -->|publish| F[X-Ray Traces]
    end
    
    subgraph "Tool Role Permissions"
        G[Tool IAM Role]
        G -->|read| H[Tool Registry]
        G -->|read| I[Secrets Manager]
        G -->|write| J[CloudWatch Logs]
        G -->|specific| K[Tool-Specific Resources]
    end
    
    subgraph "Long Content Permissions"
        L[Long Content Role]
        L -->|read/write| M[Content Table]
        L -->|all base permissions| N[Original Permissions]
    end
```

## Configuration Flow

```mermaid
flowchart LR
    subgraph "Configuration Sources"
        A[Environment Variables]
        B[CDK Context]
        C[Agent Config Dict]
        D[Tool Config Dict]
    end
    
    subgraph "Configuration Targets"
        E[Stack Parameters]
        F[Lambda Environment]
        G[Step Functions Definition]
        H[IAM Policies]
    end
    
    A --> E
    B --> E
    C --> G
    D --> G
    E --> F
    E --> H
```

## Error Handling and Rollback

```mermaid
stateDiagram-v2
    [*] --> Deploy
    Deploy --> Validate
    Validate --> Create
    Create --> Success
    Create --> Failed
    Failed --> Rollback
    Rollback --> [*]
    Success --> [*]
    
    note right of Failed
        Common Failures:
        - Export in use
        - Resource exists
        - Missing dependency
        - Permission denied
    end note
    
    note right of Rollback
        Rollback Actions:
        - Delete created resources
        - Restore previous state
        - Clean up exports
    end note
```

## Best Practices

1. **Export Naming**: Use `NamingConventions.stack_export_name()` for consistency
2. **Import Safety**: Check if resource exists before importing
3. **Dependency Order**: Always declare explicit dependencies
4. **Resource Cleanup**: Use `RemovalPolicy.DESTROY` for development
5. **Permission Scope**: Grant minimal required permissions
6. **Error Messages**: Provide clear guidance for common errors