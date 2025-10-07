# Migration Documentation

This directory contains guides for migrating to new versions and architectures of the Step Functions AI Agent Framework.

## Migration Guides

### Agent Core Migration
- **[AGENT_CORE_MIGRATION.md](AGENT_CORE_MIGRATION.md)** - Migrating from legacy agent implementations to the modular architecture

### General Migration Guide
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - General migration guide for upgrading between framework versions

### Amplify Gen 2 Setup
- **[AMPLIFY_GEN2_SETUP_GUIDE.md](AMPLIFY_GEN2_SETUP_GUIDE.md)** - Setting up and migrating to Amplify Gen 2 for the Management UI

## Migration Paths

### From Legacy to Modular Architecture

1. **Assess Current Agents** - Identify agents to migrate
2. **Update Stack Definitions** - Use `ModularBaseAgentUnifiedLLMStack`
3. **Migrate Tools** - Convert to tool registry pattern
4. **Test** - Validate functionality in dev environment
5. **Deploy** - Roll out to production

See [AGENT_CORE_MIGRATION.md](AGENT_CORE_MIGRATION.md) for details.

### To Amplify Gen 2 UI

1. **Deploy Backend** - Set up Amplify Gen 2 backend
2. **Configure Auth** - Set up Cognito authentication
3. **Deploy Frontend** - Deploy React UI
4. **Configure Registries** - Connect to existing DynamoDB registries
5. **Test** - Validate UI functionality

See [AMPLIFY_GEN2_SETUP_GUIDE.md](AMPLIFY_GEN2_SETUP_GUIDE.md) for details.

## Common Migration Scenarios

### Switching LLM Providers

To switch from one LLM provider to another:

1. **Update API Keys** in Secrets Manager
2. **Update Agent Configuration** (via UI or stack)
3. **Test** with new provider
4. **Monitor** for cost/performance differences

### Adding New Tools

1. **Deploy Tool Stack** - `cdk deploy MyToolStack-prod`
2. **Verify Registration** - Check tool appears in registry
3. **Assign to Agents** - Update agent tool configurations
4. **Test** - Validate tool functionality

## Breaking Changes

When migrating, be aware of:
- Changes to agent stack base classes
- Registry schema updates
- LLM service API changes
- UI authentication changes

Always test in dev environment first!

## Related Documentation

- [Architecture](../architecture/)
- [Deployment](../deployment/)
- [Main README](../../README.md)
