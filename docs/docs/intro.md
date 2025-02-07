---
sidebar_position: 1
---

# Executing AI Agents in AWS Step Functions

> 📦 **Enterprise AI Agent Framework**
>
> Extreme flexibility and scalability for enterprise grade AI Agents. Supporting all LLMs and tools in any programming language. Including human approval and observability. All in a single framework.

## Introduction

AI Agents are a combination of LLMs and Tools. Each tool is used to perform a specific task, and the LLM orchestrates them to perform complex tasks requested by the user. While AI Agents are powerful tools for automating complex tasks in the cloud and reducing the cost of building and maintaining complex systems, their deployment and operation can be challenging.

This framework provides a robust implementation of AI Agents in AWS Step Functions, a serverless computing platform for building and deploying serverless applications. It includes implementations of several AI Agents:

- SQL AI Agent - Analyzes SQL databases and answers business questions with visualization and reporting (Python)
- Financial AI Agent - Analyzes financial datasets using YFinance library (Python)
- Google Maps AI Agent - Analyzes Google Maps data (TypeScript)
- Time Series Clustering AI Agent - Performs time series clustering analysis (Rust)
- Time Series Analysis AI Agent - Analyzes large sets of time series data (Java)
- Web Research AI Agent - Uses Perplexity to analyze web pages and answer business questions (Go)

Key benefits of this framework include:

- High scalability limited only by AWS account resources
- Support for tools in any programming language
- Flexibility to integrate with any LLM provider through Lambda functions
- Built-in observability through Step Functions state tracking and CloudWatch/X-Ray integration
- Cost efficiency through serverless Lambda and Step Functions
- Human approval workflow capabilities
- Enterprise-grade security through IAM roles and AWS Secrets Manager

The implementation serves as a template for building custom AI Agents for specific use cases while providing production-ready features like monitoring, security, and scalability out of the box.
