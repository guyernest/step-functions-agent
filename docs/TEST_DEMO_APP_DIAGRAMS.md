# Test and Demo Application Diagrams

This document shows the dependency structure of test and demo CDK applications created for specific features.

## Test Long Content Agent Stack

Located in `stacks/agents/test_long_content_agent_stack.py`

```mermaid
graph TD
    subgraph "Test Infrastructure"
        A[TestLongContentAgentStack]
        A -->|creates| A1[Test LLM Lambda]
        A -->|creates| A2[Test Tool Lambda]
        A -->|creates| A3[Mock Content Table]
        A -->|creates| A4[Test State Machine]
    end
    
    subgraph "Test Features"
        B[Content Size Testing]
        B -->|small content| B1[Direct Pass-through]
        B -->|large content| B2[DynamoDB Storage]
        
        C[Error Testing]
        C -->|timeout| C1[Lambda Timeout]
        C -->|size limit| C2[Payload Too Large]
        C -->|retry| C3[Exponential Backoff]
    end
    
    A --> B
    A --> C
```

## Test Extended Long Content Agent Stack

Shows mixed resource usage patterns:

```mermaid
graph TD
    subgraph "Mixed Resources Example"
        A[TestExtendedLongContentAgent]
        A -->|imports| B[Existing Agent Registry]
        A -->|imports| C[Existing Web Scraper Tool]
        A -->|creates| D[New SQL Tool with Long Content]
        A -->|imports| E[Existing LLM Function]
        A -->|creates| F[New State Machine]
    end
    
    subgraph "Configuration"
        G[agent_config]
        G --> G1[use_agent_registry: true]
        G --> G2[import_tools: ['web_scraper']]
        G --> G3[create_tools: ['sql_executor']]
        G --> G4[llm_arn: 'arn:aws:lambda:...']
    end
    
    G --> A
```

## Flexible Long Content Demo

Shows all three deployment modes:

```mermaid
graph TB
    subgraph "Standalone Mode Demo"
        A[All Resources Created]
        A --> A1[New Extension Layers]
        A --> A2[New Content Table]
        A --> A3[New LLM Functions]
        A --> A4[New Tool Functions]
        A --> A5[New Registries]
    end
    
    subgraph "Extend Mode Demo"
        B[Minimal New Resources]
        B --> B1[Import Existing Registries]
        B --> B2[Import Existing Tools]
        B --> B3[New Content Table]
        B --> B4[New Long Content LLM]
    end
    
    subgraph "Hybrid Mode Demo"
        C[Mixed Resources]
        C --> C1[Import Some Tools]
        C --> C2[Create New Tools]
        C --> C3[Import Registry]
        C --> C4[New Content Support]
    end
```

## Web Automation Tool Stack (Example)

Shows complete tool deployment pattern:

```mermaid
graph TD
    subgraph "Tool Stack Structure"
        A[WebAutomationToolStack]
        A -->|creates| B[Web Scraper Lambda]
        A -->|creates| C[HTML Parser Lambda]
        A -->|creates| D[Screenshot Lambda]
        A -->|creates| E[Web Scraper Memory Lambda]
    end
    
    subgraph "Tool Registration"
        F[Tool Registry]
        B -->|registers| F
        C -->|registers| F
        D -->|registers| F
        E -->|registers| F
    end
    
    subgraph "Exports"
        B -->|export| G[WebScraperLambdaArn-{env}]
        C -->|export| H[HtmlParserLambdaArn-{env}]
        D -->|export| I[ScreenshotLambdaArn-{env}]
        E -->|export| J[WebScraperMemoryLambdaArn-{env}]
    end
    
    subgraph "Permissions"
        K[Lambda Roles]
        K --> K1[Basic Execution]
        K --> K2[X-Ray Tracing]
        K --> K3[Secrets Access]
        K --> K4[Tool-Specific]
    end
```

## Monitoring Dashboard Stack (Example)

Shows cross-stack monitoring integration:

```mermaid
graph TD
    subgraph "Monitoring Sources"
        A[Agent Stacks]
        B[Tool Stacks]
        C[LLM Stack]
        D[Infrastructure]
    end
    
    subgraph "MonitoringDashboardStack"
        E[CloudWatch Dashboard]
        F[Metric Filters]
        G[Alarms]
        H[Log Insights]
    end
    
    subgraph "Metrics"
        I[Lambda Metrics]
        I --> I1[Invocations]
        I --> I2[Errors]
        I --> I3[Duration]
        I --> I4[Throttles]
        
        J[Step Functions Metrics]
        J --> J1[Executions]
        J --> J2[Failed]
        J --> J3[Succeeded]
        J --> J4[Duration]
        
        K[DynamoDB Metrics]
        K --> K1[Read/Write Units]
        K --> K2[Throttles]
        K --> K3[Errors]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> I
    E --> J
    E --> K
```

## Activity Support Demo

Shows human approval and remote execution patterns:

```mermaid
graph TD
    subgraph "Activity Types"
        A[Human Approval Activity]
        A --> A1[Create Activity]
        A --> A2[Wait for Token]
        A --> A3[Send Success/Failure]
        
        B[Remote Execution Activity]
        B --> B1[Create Activity]
        B --> B2[Get Activity Task]
        B --> B3[Execute Remotely]
        B --> B4[Send Heartbeat]
        B --> B5[Complete Task]
    end
    
    subgraph "Step Functions Integration"
        C[State Machine]
        C --> D{Tool Requires Activity?}
        D -->|Yes| E[Activity State]
        D -->|No| F[Lambda State]
        
        E --> G[Wait for External Input]
        F --> H[Direct Execution]
    end
    
    subgraph "Implementation"
        I[SQL Query Tool]
        I -->|requires_approval| A
        
        J[Remote GPU Tool]
        J -->|remote_execution| B
    end
```

## Development Workflow Examples

### 1. Adding a New Tool
```mermaid
flowchart LR
    A[Create Tool Lambda] --> B[Define Tool Schema]
    B --> C[Create Tool Stack]
    C --> D[Export Lambda ARN]
    D --> E[Register in Tool Registry]
    E --> F[Update Agent Config]
    F --> G[Deploy & Test]
```

### 2. Adding Long Content Support
```mermaid
flowchart LR
    A[Identify Large Output Tools] --> B[Create Long Content Variant]
    B --> C[Add Proxy Extension Layer]
    C --> D[Configure Environment Vars]
    D --> E[Grant Content Table Access]
    E --> F[Test Size Thresholds]
    F --> G[Deploy to Production]
```

### 3. Creating Hybrid Deployment
```mermaid
flowchart LR
    A[Identify Shared Resources] --> B[Configure Imports]
    B --> C[Create New Resources]
    C --> D[Wire Dependencies]
    D --> E[Test Integration]
    E --> F[Document Configuration]
```

## Common Patterns

### Tool Factory Pattern
```python
# Base pattern for creating multiple similar tools
class ToolFactory:
    def create_tool(tool_name, schema) -> Lambda:
        return Lambda(
            function_name=f"tool-{tool_name}-{env}",
            handler="index.handler",
            runtime=PYTHON_3_11,
            environment={"TOOL_NAME": tool_name}
        )
```

### Agent Builder Pattern
```python
# Pattern for building agents with configurable tools
class AgentBuilder:
    def with_tools(tool_arns) -> Agent:
        return Agent(
            tool_configs=[
                {"tool_name": name, "lambda_arn": arn}
                for name, arn in tool_arns.items()
            ]
        )
```

### Resource Import Pattern
```python
# Pattern for conditional resource import/create
class ResourceManager:
    def get_resource(config):
        if config.get("import_from"):
            return import_resource(config["import_from"])
        else:
            return create_resource(config)
```