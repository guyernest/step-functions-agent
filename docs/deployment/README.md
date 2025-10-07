# Deployment Documentation

This directory contains guides and checklists for deploying the Step Functions AI Agent Framework.

## Main Deployment Guide

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete step-by-step deployment guide for all components

## Build Instructions

- **[BUILD.md](BUILD.md)** - Build instructions for the framework, including Rust components and CDK stacks

## Deployment Checklists

### Infrastructure Deployment
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - General deployment checklist for infrastructure and agents

### Observability Setup
- **[OBSERVABILITY_DEPLOYMENT_CHECKLIST.md](OBSERVABILITY_DEPLOYMENT_CHECKLIST.md)** - Checklist for setting up monitoring, logging, and tracing

## Deployment Notes

- **[DEPLOYMENT_NOTES.md](DEPLOYMENT_NOTES.md)** - Additional notes, tips, and troubleshooting for deployments

## Deployment Order

Recommended deployment sequence:

1. **Shared Infrastructure** (once per environment)
   ```bash
   cdk deploy SharedInfrastructureStack-prod
   cdk deploy AgentRegistryStack-prod
   ```

2. **LLM Service** (choose based on needs)
   ```bash
   cdk deploy SharedUnifiedRustLLMStack-prod
   ```

3. **Tools** (deploy as needed)
   ```bash
   cdk deploy DBInterfaceToolStack-prod
   cdk deploy GoogleMapsToolStack-prod
   ```

4. **Agents** (deploy your agents)
   ```bash
   cdk deploy MyAgentStack-prod
   ```

5. **Management UI** (Amplify)
   ```bash
   cd ui_amplify
   npx ampx pipeline-deploy --branch main
   ```

## Environment Strategy

The framework supports multiple environments:
- **dev** - Development environment for testing
- **prod** - Production environment

Set environment before deployment:
```bash
export ENVIRONMENT=prod
```

## Related Documentation

- [Architecture](../architecture/)
- [Migration Guides](../migration/)
- [Main README](../../README.md)
