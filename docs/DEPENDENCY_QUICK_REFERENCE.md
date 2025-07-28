# Dependency Quick Reference

## Stack Dependency Order

### Refactored App (`refactored_app.py`)

```txt
1. SharedInfrastructureStack
2. AgentRegistryStack
3. SharedLLMStack
4. Tool Stacks (parallel):
   - GoogleMapsToolStack
   - DBInterfaceToolStack
   - WebAutomationToolStack
   - CodeExecutionToolStack
   - ImageAnalysisToolStack
   - ResearchToolStack
   - FinancialToolStack
5. Agent Stacks (parallel):
   - GoogleMapsAgentStack
   - SqlAgentStack
   - WebScraperAgentStack
   - ImageAnalysisAgentStack
   - ResearchAgentStack
6. MonitoringDashboardStack
```

### Long Content App (`long_content_app.py`)

```txt
Prerequisites: Main infrastructure from refactored_app.py

1. LambdaExtensionLayerStack
2. SharedLongContentInfrastructureStack
3. SharedLLMWithLongContentStack
4. Tool Stacks (parallel):
   - WebScraperLongContentTools
   - SqlLongContentTools
5. Agent Stacks (parallel):
   - WebScraperLongContentAgent
   - SqlLongContentAgent
   - ImageAnalysisLongContentAgent
```

## Key Dependencies

### Agent → Resource Dependencies

| Agent | Depends On | Imports |
|-------|-----------|---------|
| GoogleMapsAgent | AgentRegistry, SharedLLM, GoogleMapsTool | Registry ARN, LLM ARNs, Tool ARNs |
| SqlAgent | AgentRegistry, SharedLLM, DBInterfaceTool | Registry ARN, LLM ARNs, Tool ARN |
| WebScraperAgent | AgentRegistry, SharedLLM, WebAutomationTool | Registry ARN, LLM ARNs, Tool ARNs |
| ImageAnalysisAgent | AgentRegistry, SharedLLM, ImageAnalysisTool | Registry ARN, LLM ARNs, Tool ARNs |
| ResearchAgent | AgentRegistry, SharedLLM, ResearchTool, FinancialTool | Registry ARN, LLM ARNs, Tool ARNs |

### Long Content → Resource Dependencies

| Stack | Depends On | Imports From Main | Creates New |
|-------|-----------|------------------|-------------|
| LambdaExtensionLayer | None | None | Proxy Layers |
| SharedLongContentInfra | LambdaExtensionLayer | None | ContentTable |
| SharedLLMWithLongContent | SharedLongContentInfra | LLM Secrets | LLM Functions |
| WebScraperLongContentTools | SharedLongContentInfra | Tool Registry | Tool Functions |
| SqlLongContentTools | SharedLongContentInfra | Tool Registry | Tool Functions |
| LongContentAgents | LLM, Tools | Agent Registry | State Machines |

## Export/Import Reference

### Commonly Used Exports

```python
# Agent Registry
"SharedTableAgentRegistry-{env}"        # Table name
"SharedTableArnAgentRegistry-{env}"     # Table ARN

# Tool Registry  
"SharedTableToolRegistry-{env}"         # Table name
"SharedTableArnToolRegistry-{env}"      # Table ARN

# LLM Functions
"SharedClaudeLambdaArn-{env}"          # Claude Lambda ARN
"SharedOpenAILambdaArn-{env}"          # OpenAI Lambda ARN
"SharedGeminiLambdaArn-{env}"          # Gemini Lambda ARN

# Tool Functions
"{ToolName}LambdaArn-{env}"            # Tool Lambda ARN

# Long Content
"SharedProxyLayerX86LongContent-{env}"  # x86 Proxy Layer
"SharedProxyLayerArmLongContent-{env}"  # ARM Proxy Layer
"SharedContentTableLongContent-{env}"   # Content Table
```

### Import Methods

```python
# Method 1: CloudFormation Import Value
Fn.import_value("ExportName")

# Method 2: Direct Resource Import
Table.from_table_name(self, "id", "table-name")
Function.from_function_arn(self, "id", "arn")
Secret.from_secret_name_v2(self, "id", "secret-name")
LayerVersion.from_layer_version_arn(self, "id", "arn")
```

## Common Dependency Patterns

### 1. Tool Stack Pattern

```txt
Tool Stack:
├── Creates: Lambda Functions
├── Registers: Tool Registry
├── Exports: Lambda ARNs
└── Depends: None (self-contained)
```

### 2. Agent Stack Pattern

```txt
Agent Stack:
├── Creates: State Machine, IAM Role, Log Group
├── Registers: Agent Registry
├── Imports: LLM ARNs, Tool ARNs, Registry Tables
└── Depends: AgentRegistry, SharedLLM, Tools
```

### 3. Long Content Pattern

```txt
Long Content Stack:
├── Creates: New Resources with Proxy Support
├── Imports: Existing Registries, Secrets
├── Adds: Content Table Access, Proxy Layers
└── Depends: Extension Layers, Infrastructure
```

## Troubleshooting Dependencies

### Common Issues

1. **"No export named X found"**
   - Check if prerequisite stack is deployed
   - Verify export name matches import
   - Ensure environment suffix matches

2. **"Cannot update export X as it is in use"**
   - Don't update stacks with exports in use
   - Delete dependent stacks first if needed
   - Use `--exclusively` flag to skip dependencies

3. **"Resource already exists"**
   - Check for naming conflicts
   - Ensure unique resource names
   - Consider using different environment

4. **"Circular dependency detected"**
   - Review stack dependencies
   - Move shared resources to separate stack
   - Use lazy imports where possible

### Deployment Commands

```bash
# Deploy with dependencies
cdk deploy StackName --profile PROFILE

# Deploy without dependencies  
cdk deploy StackName --exclusively --profile PROFILE

# Deploy multiple stacks
cdk deploy Stack1 Stack2 Stack3 --profile PROFILE

# Deploy all stacks
cdk deploy --all --profile PROFILE
```

### Dependency Verification

```bash
# List all exports
aws cloudformation list-exports --profile PROFILE

# Check stack dependencies
cdk list --app 'python app.py'

# Verify stack status
aws cloudformation describe-stacks --stack-name NAME --profile PROFILE
```
