# AWS Step Functions Agent Framework - Refactoring Design

## Overview

This document outlines the comprehensive refactoring plan for the AWS Step Functions Agent Framework to achieve better modularity, reusability, and maintainability. The refactoring addresses the current issues of code duplication, poor resource sharing, and complex IAM management while preserving the framework's strength in multi-language support.

## Implementation Status (Updated: 2025-07-18)

✅ **Completed**:
- Three-module architecture implemented (Tools, LLMs, Agents)
- DynamoDB tool registry with dynamic loading
- Shared LLM stack with centralized secrets management
- Dynamic SQL agent using JSON templates with JSONata
- Fixed Lambda layer compatibility issues (boto3/botocore versions, ARM64 support)
- API key loading from .env file in CDK deployment

🚧 **In Progress**:
- Migration of remaining agents to dynamic loading pattern
- Multi-language tool examples beyond Python

📋 **TODO**:
- Tool versioning and lifecycle management
- Advanced agent patterns (multi-step reasoning, tool chaining)
- Monitoring and observability improvements

## Current Architecture Issues

### Problems Identified
- **Code Duplication**: Each agent stack recreates similar IAM roles, log groups, and LLM functions
- **Poor Resource Sharing**: Limited reuse of LLM caller Lambda functions across agents
- **Complex IAM Management**: Inconsistent role creation and permission management
- **Static Tool Configuration**: Tool specifications are hardcoded in Step Functions at deployment time
- **Scattered Secrets**: Inconsistent secret management across different components

### Current Strengths to Preserve
- **Multi-Language Support**: Excellent support for Python, TypeScript, Rust, Java, Go with room for expansion (.NET, etc.)
- **Cookiecutter Templates**: Comprehensive scaffolding for new tool development
- **Native Build Systems**: Language-specific build, test, and deployment mechanisms
- **Flexible Architecture**: Ability to develop tools in enterprise-preferred languages

## Refactored Architecture

### Three-Module Design

#### 1. **Tools Module** (Lambda Functions)
- **Purpose**: Individual business logic functions in various languages
- **Deployment**: Independent stacks per tool or tool groups
- **Registry**: DynamoDB-based tool specifications for runtime discovery
- **Languages**: Python, TypeScript, Rust, Java, Go, .NET (future)
- **Secrets**: Tool-specific secrets using AWS SDK/Lambda Powertools per language

#### 2. **LLMs Module** (Lambda Functions)
- **Purpose**: Centralized LLM provider integrations (OpenAI, Anthropic, Gemini, etc.)
- **Deployment**: Shared LLM stack deployed once, referenced by all agents
- **Languages**: Primarily Python leveraging Lambda Powertools
- **Secrets**: Centralized LLM API keys using Lambda Powertools Parameters/Secrets
- **Reuse**: Single LLM Lambda per provider, shared across all agents

#### 3. **Agents Module** (Step Functions)
- **Purpose**: Orchestration workflows that coordinate LLMs and Tools
- **Deployment**: Lightweight agent stacks focused on Step Functions definitions
- **Dynamic Loading**: Load tool specifications from DynamoDB at runtime
- **Reuse**: Reference shared LLM Lambdas and discover available tools dynamically

## Detailed Design

### 1. DynamoDB Tool Registry

#### Primary Table: ToolRegistry
```json
{
  "tool_name": "web_scraper",           // Partition Key
  "version": "1.0.0",                  // Sort Key
  "description": "Scrapes web content and extracts information",
  "input_schema": {                    // JSON Schema for validation
    "type": "object",
    "properties": {
      "url": {"type": "string", "description": "URL to scrape"},
      "selector": {"type": "string", "description": "CSS selector"}
    },
    "required": ["url"]
  },
  "lambda_function_name": "tool-web-scraper-prod",  // Consistent naming
  "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:tool-web-scraper-prod",
  "language": "python",
  "tags": ["web", "scraping", "html"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "status": "active",                  // active, deprecated, disabled
  "author": "team@company.com",
  "human_approval_required": false
}
```

#### Global Secondary Indexes
- **ToolsByLanguage**: `language` (PK), `tool_name` (SK)
- **ToolsByTag**: `tags` (PK), `tool_name` (SK)
- **ActiveTools**: `status` (PK), `updated_at` (SK)

#### Dynamic Loading Mechanism
- **Step Functions Integration**: Use built-in DynamoDB GetItem actions
- **No Additional Lambdas**: Leverage Step Functions native DynamoDB integration
- **Map State**: Load tool specifications in parallel using Map state
- **JSONata Processing**: Transform DynamoDB response to Step Functions format

### 2. Consistent Tool Lambda Naming Convention

#### Naming Standard
```
Pattern: tool-{tool_id}-{environment}
Examples:
- tool-web-scraper-prod
- tool-html-parser-prod  
- tool-url-validator-prod
```

#### Benefits
- **Predictable ARNs**: IAM policies can be generated at deployment time
- **Environment Support**: Different environments have different function names
- **Validation**: Tool IDs can be validated against naming conventions
- **No Runtime Queries**: No need to query DynamoDB for Lambda ARNs during IAM policy creation

### 3. Agent Stack Architecture

#### Simplified Agent Definition
```python
class WebScraperAgentStack(Stack):
    def __init__(self, scope, construct_id, shared_llm_stack, environment="prod", **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Simple tool configuration - just IDs from registry
        self.agent_tools = [
            "web_scraper",
            "html_parser", 
            "url_validator"
        ]
        
        # Generate IAM policies for tool Lambda functions
        self._create_tool_execution_policies(self.agent_tools, environment)
        
        # Create agent workflow
        self.agent_definition = self._create_agent_workflow(
            shared_llm_stack.claude_lambda.function_arn,
            self.agent_tools
        )
```

#### Step Functions Workflow
```json
{
  "Comment": "Dynamic Agent Workflow",
  "StartAt": "LoadToolSpecs",
  "States": {
    "LoadToolSpecs": {
      "Type": "Map",
      "ItemsPath": "$.tool_ids",
      "Iterator": {
        "StartAt": "GetToolSpec",
        "States": {
          "GetToolSpec": {
            "Type": "Task",
            "Resource": "arn:aws:states:::dynamodb:getItem",
            "Parameters": {
              "TableName": "ToolRegistry",
              "Key": {
                "tool_name": {"S.$": "$.tool_id"},
                "version": {"S": "latest"}
              }
            },
            "ResultSelector": {
              "name.$": "$.Item.tool_name.S",
              "description.$": "$.Item.description.S", 
              "input_schema.$": "States.StringToJson($.Item.input_schema.S)",
              "lambda_arn.$": "$.Item.lambda_arn.S"
            },
            "End": true
          }
        }
      },
      "ResultPath": "$.tools",
      "Next": "CallLLM"
    },
    "CallLLM": {
      "Type": "Task",
      "Resource": "${LLMLambdaArn}",
      "Parameters": {
        "model": "claude-3-5-sonnet-20241022",
        "messages.$": "$.messages",
        "tools.$": "$.tools"
      },
      "Next": "ProcessLLMResponse"
    }
  }
}
```

### 4. LLM Module Architecture

#### Shared LLM Stack
```python
class SharedLLMStack(Stack):
    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Centralized LLM secret
        self.llm_secret = secretsmanager.Secret(
            self, "LLMSecrets",
            secret_name="/ai-agent/llm-secrets/prod",
            description="Centralized LLM API keys"
        )
        
        # LLM Lambda functions
        self.claude_lambda = self._create_llm_lambda("claude")
        self.openai_lambda = self._create_llm_lambda("openai")
        self.gemini_lambda = self._create_llm_lambda("gemini")
        
        # Export Lambda ARNs for agent stacks
        CfnOutput(self, "ClaudeLambdaArn", value=self.claude_lambda.function_arn)
        CfnOutput(self, "OpenAILambdaArn", value=self.openai_lambda.function_arn)
```

#### LLM Lambda Implementation
```python
from aws_lambda_powertools.utilities.parameters import get_secret

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def claude_handler(event, context):
    # Get LLM secrets using Powertools
    api_keys = get_secret("/ai-agent/llm-secrets/prod", transform="json")
    
    claude_client = anthropic.Anthropic(
        api_key=api_keys["anthropic_api_key"]
    )
    
    # Process LLM request with dynamic tools from registry
    response = claude_client.messages.create(
        model=event["model"],
        messages=event["messages"],
        tools=event["tools"]  # Dynamic tools from registry
    )
    
    return response
```

### 5. Multi-Language Support Architecture

#### Language-Specific Constructs
- **Base Language Construct**: Abstract CDK construct with common patterns
- **Python Construct**: Lambda Powertools integration
- **TypeScript Construct**: Node.js Lambda with TypeScript build
- **Rust Construct**: cargo-lambda with ARM64 support
- **Java Construct**: Maven build with dependency management
- **Go Construct**: Native Go build with cross-compilation

#### Enhanced Cookiecutter Templates
- **Complete Coverage**: Templates for all supported languages
- **Registry Integration**: Automatic tool registration in DynamoDB
- **Consistent Patterns**: Standardized project structure across languages
- **Build System Integration**: Language-specific build, test, and deployment

#### Shared Layer Strategy
- **Language-Specific Base Layers**: Common AWS dependencies per language
- **No Cross-Language Layers**: Maintain native language patterns
- **Dependency Optimization**: Shared dependencies within language families

### 6. Layered Secrets Management

#### Three-Tier Architecture

##### Tier 1: LLM Secrets (Centralized)
```
/ai-agent/llm-secrets/{environment}
{
  "openai_api_key": "...",
  "anthropic_api_key": "...",
  "gemini_api_key": "..."
}
```

##### Tier 2: Tool-Specific Secrets
```
/ai-agent/tools/{tool_name}/{environment}
{
  "google_maps_api_key": "...",
  "database_connection_string": "..."
}
```

##### Tier 3: Infrastructure Secrets
```
/ai-agent/infrastructure/{environment}
{
  "database_master_password": "...",
  "service_account_keys": "..."
}
```

#### Implementation by Language

##### Python (LLMs & Tools)
```python
from aws_lambda_powertools.utilities.parameters import get_secret

# For LLM functions
llm_secrets = get_secret("/ai-agent/llm-secrets/prod", transform="json")

# For tool functions  
tool_secrets = get_secret("/ai-agent/tools/web-scraper/prod", transform="json")
```

##### TypeScript (Tools)
```typescript
import { getSecret } from '@aws-lambda-powertools/parameters/secrets';

const toolSecrets = await getSecret('/ai-agent/tools/web-scraper/prod', {
  transform: 'json'
});
```

##### Other Languages (Native AWS SDK)
- **Rust**: `aws-sdk-secretsmanager` crate
- **Java**: `software.amazon.awssdk.services.secretsmanager`
- **Go**: `github.com/aws/aws-sdk-go-v2/service/secretsmanager`

### 7. Project Structure

```
step-functions-agent/
├── stacks/
│   ├── shared/
│   │   ├── shared_llm_stack.py          # Centralized LLM functions
│   │   ├── shared_infrastructure_stack.py # DynamoDB, IAM, secrets
│   │   └── naming_conventions.py         # Consistent naming utilities
│   ├── tools/
│   │   ├── tool_deployment_stack.py      # Individual tool deployment
│   │   └── tool_constructs/              # Language-specific constructs
│   │       ├── python_tool_construct.py
│   │       ├── typescript_tool_construct.py
│   │       ├── rust_tool_construct.py
│   │       ├── java_tool_construct.py
│   │       └── go_tool_construct.py
│   └── agents/
│       ├── base_agent_stack.py           # Common agent patterns
│       ├── web_scraper_agent_stack.py    # Individual agent stacks
│       └── sql_agent_stack.py
├── lambda/
│   ├── llm_handlers/                     # Centralized LLM functions
│   │   ├── claude_handler.py
│   │   ├── openai_handler.py
│   │   └── gemini_handler.py
│   ├── tools/                            # Individual tool implementations
│   │   ├── web_scraper/
│   │   ├── html_parser/
│   │   └── url_validator/
│   └── cookiecutter/                     # Enhanced templates
│       ├── python_tool/
│       ├── typescript_tool/
│       ├── rust_tool/
│       ├── java_tool/
│       └── go_tool/
├── step-functions/
│   ├── templates/
│   │   ├── dynamic_agent_template.json   # New dynamic template
│   │   └── legacy_agent_template.json    # Backward compatibility
│   └── utilities/
│       └── template_processor.py         # Template customization
└── docs/
    ├── REFACTORING_DESIGN.md             # This document
    ├── MIGRATION_GUIDE.md                # Migration instructions
    └── DEVELOPMENT_GUIDE.md              # Developer onboarding
```

## Implementation Plan

### Phase 1: Core Infrastructure (Weeks 1-2)
1. **Shared Infrastructure Stack**
   - Create DynamoDB ToolRegistry table
   - Implement naming conventions utility
   - Set up layered secrets management

2. **Shared LLM Stack**
   - Centralize LLM Lambda functions
   - Implement Lambda Powertools integration
   - Create stack exports for agent reuse

3. **Tool Registry Integration**
   - Implement DynamoDB schema
   - Create tool registration mechanisms
   - Add validation and versioning

### Phase 2: Tool Module Enhancement (Weeks 3-4)
1. **Language-Specific Constructs**
   - Create base tool construct
   - Implement Python, TypeScript, Rust, Java, Go constructs
   - Add automatic registry registration

2. **Enhanced Cookiecutter Templates**
   - Complete missing templates (Go, Java)
   - Add registry integration to all templates
   - Implement consistent project structure

3. **Tool Deployment Stacks**
   - Create individual tool deployment pattern
   - Implement consistent naming convention
   - Add IAM policy generation

### Phase 3: Agent Module Refactoring (Weeks 5-6)
1. **Dynamic Step Functions Template**
   - Create new template with DynamoDB integration
   - Implement Map state for tool loading
   - Add JSONata for dynamic tool selection

2. **Agent Stack Simplification**
   - Refactor existing agent stacks
   - Implement tool ID-based configuration
   - Add automatic IAM policy generation

3. **Backward Compatibility**
   - Maintain support for existing patterns
   - Create migration utilities
   - Add feature flags for gradual rollout

### Phase 4: Migration and Testing (Weeks 7-8)
1. **Comprehensive Testing**
   - Test all language constructs
   - Validate dynamic tool loading
   - Performance testing and optimization

2. **Documentation and Training**
   - Complete developer guides
   - Create migration documentation
   - Conduct team training sessions

3. **Production Rollout**
   - Gradual migration of existing agents
   - Monitor performance and reliability
   - Gather feedback and iterate

## Benefits of Refactored Architecture

### Technical Benefits
- **Reduced Duplication**: Shared LLM functions and infrastructure
- **Better Maintainability**: Clear separation of concerns
- **Dynamic Tool Management**: Runtime tool discovery and execution
- **Consistent Security**: Standardized IAM policies and secret management
- **Multi-Language Excellence**: Enhanced support for all programming languages

### Operational Benefits
- **Independent Deployment**: Tools, LLMs, and agents deploy separately
- **Faster Development**: New agents focus on business logic
- **Better Monitoring**: Centralized logging and metrics
- **Cost Optimization**: Shared resources reduce AWS costs
- **Easier Debugging**: Clear component boundaries and observability

### Developer Experience Benefits
- **Simplified Onboarding**: Comprehensive templates and documentation
- **Language Freedom**: Use preferred programming languages
- **Consistent Patterns**: Standardized approaches across all components
- **Better Testing**: Independent testing of each module
- **Enhanced Productivity**: Focus on business logic rather than infrastructure

## Migration Strategy

### Backward Compatibility
- **Dual Mode Support**: Support both static and dynamic tool definitions
- **Gradual Migration**: Migrate agents one at a time
- **Feature Flags**: Control rollout of new features
- **Legacy Support**: Maintain existing patterns during transition

### Risk Mitigation
- **Incremental Rollout**: Test each component independently
- **Comprehensive Testing**: Validate all integration points
- **Monitoring**: Enhanced observability during migration
- **Rollback Plan**: Ability to revert to previous patterns if needed

## Success Metrics

### Technical Metrics
- **Code Duplication Reduction**: Measure reduction in repeated code
- **Deployment Time**: Faster deployment of new agents and tools
- **Resource Utilization**: Improved AWS resource efficiency
- **Error Rate**: Reduced errors from configuration inconsistencies

### Developer Metrics
- **Time to Market**: Faster development of new agents
- **Developer Satisfaction**: Improved development experience
- **Learning Curve**: Reduced onboarding time for new developers
- **Code Quality**: Improved maintainability and consistency

This refactoring design provides a comprehensive plan for transforming the AWS Step Functions Agent Framework into a more modular, maintainable, and developer-friendly architecture while preserving its core strengths in multi-language support and flexibility.