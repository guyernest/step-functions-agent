# Legacy Code Archive

This directory contains the original implementation of the AI Agents framework before the modular refactoring.

## ⚠️ Deprecation Notice

**The code in this directory is deprecated and should not be used for new deployments.**

The framework has been completely refactored to provide:
- Modular architecture with shared resources
- Better separation of concerns
- Unified LLM service with multiple providers
- Improved maintainability and scalability

## 📁 Contents

### Original CDK Applications
- `app_old.py` - Original monolithic CDK application
- `long_content_app.py` - Original long content implementation
- `flexible_long_content_app.py` - Flexible long content experiments
- `test_approval_agents.py` - Original approval workflow tests
- `test_shared_llm_app.py` - Early shared LLM experiments

### Original Stack Implementations
- `step_functions_agent/` - Original stack implementations
  - Individual agent stacks (SQL, Financial, Maps, etc.)
  - Original monitoring stack
  - Original UI stack
  - Monolithic tool implementations

## 🔄 Migration Guide

If you have existing deployments using the legacy code:

1. **Export your data**
   - Agent configurations
   - Tool definitions
   - Execution history

2. **Deploy new infrastructure**
   ```bash
   # Deploy shared infrastructure
   cdk deploy SharedInfrastructureStack-prod
   cdk deploy AgentRegistryStack-prod
   
   # Deploy shared LLM
   cdk deploy SharedUnifiedRustLLMStack-prod
   
   # Deploy tools
   cdk deploy [ToolStack]-prod
   
   # Deploy agents
   cdk deploy [AgentStack]-prod
   ```

3. **Migrate data**
   - Import agent configurations to new Agent Registry
   - Update tool references
   - Test with sample executions

4. **Decommission legacy stacks**
   ```bash
   # Remove old stacks
   cdk destroy [OldStackName]
   ```

## 📚 Reference Documentation

For historical reference, the legacy implementation includes:

### Agent Types
- SQL Agent - Database query and analysis
- Financial Agent - Financial data analysis
- Google Maps Agent - Location-based services
- Research Agent - Web research capabilities
- Clustering Agent - Time series clustering
- Analysis Agent - Data analysis
- CloudWatch Agent - AWS metrics and logs
- GraphQL Agent - GraphQL API interactions
- Image Analysis Agent - Image processing
- Earthquake Agent - Seismic data monitoring
- Semantic Search Agent - Vector search capabilities

### Key Differences from New Architecture

| Aspect | Legacy | New (Modular) |
|--------|--------|---------------|
| LLM Management | Per-agent Lambda | Shared LLM service |
| Tool Definition | Hardcoded in stacks | Dynamic Tool Registry |
| Agent Configuration | Static in code | Dynamic Agent Registry |
| Resource Sharing | Duplicated | Shared infrastructure |
| Provider Support | Limited | Multiple providers |
| Deployment | Monolithic | Modular |

## ⚠️ Important Notes

1. **Do not use for new projects** - Always use the new modular architecture
2. **Security updates** - Legacy code may not receive security updates
3. **No support** - Legacy code is not actively maintained
4. **Migration recommended** - Existing deployments should migrate to new architecture

## 📞 Support

For help migrating from legacy to new architecture:
- Review the main [README.md](../README.md)
- Check [docs/MODULAR_ARCHITECTURE.md](../docs/MODULAR_ARCHITECTURE.md)
- Open an issue for migration assistance

---

**Archived**: 2024
**Status**: Deprecated - For reference only