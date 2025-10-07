# Standards and Conventions

This directory contains coding standards, naming conventions, and best practices for the Step Functions AI Agent Framework.

## Naming Conventions

### Agent Naming
- **[AGENT_NAMING_CONVENTIONS.md](AGENT_NAMING_CONVENTIONS.md)** - Standard naming patterns for agents, including:
  - Agent names (lowercase with hyphens)
  - Stack naming conventions
  - State machine naming
  - CloudFormation export naming

### Tool Directory Standards
- **[TOOL_DIRECTORY_STANDARDS.md](TOOL_DIRECTORY_STANDARDS.md)** - Directory structure and organization standards for tools:
  - Lambda function structure
  - Tool definition format
  - Naming conventions
  - Documentation requirements

## Configuration Standards

### Provider API Keys
- **[PROVIDER_API_KEY_MAPPING.md](PROVIDER_API_KEY_MAPPING.md)** - Standard mapping of LLM provider API keys in Secrets Manager:
  - Anthropic (Claude)
  - OpenAI (GPT)
  - Google (Gemini)
  - Amazon (Bedrock)
  - xAI (Grok)
  - DeepSeek

## Quick Reference

### Agent Naming Pattern
```
agent-name-[environment]
Example: sql-agent-prod, research-agent-dev
```

### Tool Naming Pattern
```
tool-name-tool
Example: db-interface-tool, google-maps-tool
```

### Stack Naming Pattern
```
[ComponentName][Type]Stack-[environment]
Examples:
- SQLAgentUnifiedLLMStack-prod
- DBInterfaceToolStack-prod
- SharedInfrastructureStack-dev
```

### CloudFormation Exports
```
[ResourceType]-[environment]
Examples:
- DBInterfaceToolLambdaArn-prod
- SharedUnifiedRustLLMLambdaArn-dev
```

## Best Practices

### Code Organization
1. Use modular base classes for agents
2. Separate tool logic from infrastructure
3. Keep tool definitions in JSON files
4. Document all public interfaces

### Security
1. Store all API keys in Secrets Manager
2. Use IAM roles, never access keys
3. Apply principle of least privilege
4. Tag all resources for auditing

### Testing
1. Create test fixtures for all tools
2. Test agents in dev before prod
3. Use sandbox for UI testing
4. Monitor executions in CloudWatch

### Documentation
1. Update README when adding features
2. Document breaking changes
3. Include examples in docs
4. Keep architecture diagrams current

## Related Documentation

- [Architecture](../architecture/)
- [Deployment](../deployment/)
- [Tool Development](../../README.md#building-tools)
- [Agent Development](../../README.md#building-your-first-agent)
