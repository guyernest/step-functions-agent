# Architecture Documentation

This directory contains architectural design documents and technical analyses for the Step Functions AI Agent Framework.

## LLM Architecture

### Unified LLM Service
- **[LLM_UNIFIED_RUST_ARCHITECTURE.md](LLM_UNIFIED_RUST_ARCHITECTURE.md)** - Core Rust-based unified LLM service architecture
- **[UNIFIED_LLM_RUST_AMPLIFY_ARCHITECTURE.md](UNIFIED_LLM_RUST_AMPLIFY_ARCHITECTURE.md)** - Integration with Amplify UI
- **[LLM_UNIFIED_ARCHITECTURE_ANALYSIS.md](LLM_UNIFIED_ARCHITECTURE_ANALYSIS.md)** - Analysis and design decisions

### Provider Analysis
- **[LLM_PROVIDER_ANALYSIS.md](LLM_PROVIDER_ANALYSIS.md)** - Comparison of LLM providers (Anthropic, OpenAI, Google, Amazon, xAI, DeepSeek)

## System Architecture

### Refactored Design
- **[REFACTORED_ARCHITECTURE.md](REFACTORED_ARCHITECTURE.md)** - Current modular architecture design with shared infrastructure and tool/agent stacks

## Overview

The framework uses a modular, serverless architecture built on AWS Step Functions with:

1. **Unified LLM Service** - High-performance Rust-based service supporting multiple LLM providers
2. **Modular Stack Design** - Shared infrastructure, reusable tools, independent agents
3. **Registry Pattern** - DynamoDB-based registries for agents, tools, and models
4. **Event-Driven** - EventBridge for execution tracking and monitoring
5. **Management UI** - Amplify-based admin interface for operations

## Related Documentation

- [Deployment Guide](../deployment/DEPLOYMENT_GUIDE.md)
- [Migration Guide](../migration/MIGRATION_GUIDE.md)
- [Standards](../standards/)
