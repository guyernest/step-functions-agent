# Documentation Index

This directory contains comprehensive documentation for the AI Agents Framework with AWS Step Functions.

## 📚 Core Documentation

### Architecture & Design
- **[MODULAR_ARCHITECTURE.md](MODULAR_ARCHITECTURE.md)** - Complete modular architecture design and patterns
- **[RESOURCE_FLOW_DIAGRAM.md](RESOURCE_FLOW_DIAGRAM.md)** - Visual representation of resource dependencies
- **[STACK_DEPENDENCY_DIAGRAMS.md](STACK_DEPENDENCY_DIAGRAMS.md)** - Detailed stack dependency relationships
- **[AGENT_REGISTRY_DESIGN.md](AGENT_REGISTRY_DESIGN.md)** - Dynamic agent configuration system

### Development Guides
- **[ACTIVITY_TESTING_GUIDE.md](ACTIVITY_TESTING_GUIDE.md)** - Testing remote activities and human approval workflows
- **[LAMBDA_LAYER_TROUBLESHOOTING.md](LAMBDA_LAYER_TROUBLESHOOTING.md)** - Resolving Lambda layer issues
- **[DEPENDENCY_QUICK_REFERENCE.md](DEPENDENCY_QUICK_REFERENCE.md)** - Quick reference for dependencies

### Feature Documentation
- **[LONG_CONTENT_FEATURE.md](LONG_CONTENT_FEATURE.md)** - Overview of long content support
- **[LONG_CONTENT_DEVELOPER_GUIDE.md](LONG_CONTENT_DEVELOPER_GUIDE.md)** - Implementing long content in agents
- **[LONG_CONTENT_DEPLOYMENT.md](LONG_CONTENT_DEPLOYMENT.md)** - Deploying long content infrastructure

### LLM & Model Management
- **[MODEL_MANAGEMENT.md](MODEL_MANAGEMENT.md)** - Managing LLM models and providers
- **[BEDROCK_MODEL_REFERENCE.md](BEDROCK_MODEL_REFERENCE.md)** - Amazon Bedrock model specifications
- **[provider-naming-alignment.md](provider-naming-alignment.md)** - Provider naming conventions

### Infrastructure & Operations
- **[TAGGING_STRATEGY.md](TAGGING_STRATEGY.md)** - AWS resource tagging best practices
- **[TAGGING_MIGRATION_EXAMPLE.md](TAGGING_MIGRATION_EXAMPLE.md)** - Example of tag migration
- **[TEST_DEMO_APP_DIAGRAMS.md](TEST_DEMO_APP_DIAGRAMS.md)** - Test and demo application architecture

## 🚀 Quick Start Guides

### For New Users
1. Start with [MODULAR_ARCHITECTURE.md](MODULAR_ARCHITECTURE.md) to understand the system
2. Review [STACK_DEPENDENCY_DIAGRAMS.md](STACK_DEPENDENCY_DIAGRAMS.md) for deployment order
3. Follow the main [README.md](../README.md) for deployment instructions

### For Developers
1. Read [AGENT_REGISTRY_DESIGN.md](AGENT_REGISTRY_DESIGN.md) for dynamic configuration
2. Use [ACTIVITY_TESTING_GUIDE.md](ACTIVITY_TESTING_GUIDE.md) for testing workflows
3. Refer to [LONG_CONTENT_DEVELOPER_GUIDE.md](LONG_CONTENT_DEVELOPER_GUIDE.md) for extended content

### For Operations
1. Review [TAGGING_STRATEGY.md](TAGGING_STRATEGY.md) for resource management
2. Check [MODEL_MANAGEMENT.md](MODEL_MANAGEMENT.md) for LLM configuration
3. Use [LAMBDA_LAYER_TROUBLESHOOTING.md](LAMBDA_LAYER_TROUBLESHOOTING.md) for debugging

## 📖 Documentation Standards

### File Naming Convention
- Use UPPERCASE with underscores for main documentation files
- Use lowercase with hyphens for supplementary files
- Include `.md` extension for all markdown files

### Content Structure
Each documentation file should include:
1. **Title** - Clear, descriptive title
2. **Overview** - Brief summary of the content
3. **Table of Contents** - For longer documents
4. **Main Content** - Well-organized sections
5. **Examples** - Code samples and use cases
6. **References** - Links to related documentation

### Diagrams
- Use Mermaid for architecture diagrams
- Include ASCII art for simple illustrations
- Store images in `../images/` directory

## 🔄 Keeping Documentation Updated

When making changes to the codebase:
1. Update relevant documentation files
2. Add new documentation for new features
3. Update examples to reflect current implementation
4. Review and update diagrams as needed

## 📝 Contributing to Documentation

To contribute to the documentation:
1. Follow the documentation standards above
2. Ensure accuracy and clarity
3. Include practical examples
4. Update the table of contents if adding new files
5. Submit a pull request with your changes

## 📞 Support

For questions about the documentation:
- Open an issue in the GitHub repository
- Join the discussion in GitHub Discussions
- Contact the maintainers

---

Last Updated: 2024