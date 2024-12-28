# Executing AI Agents in AWS Step Functions

## AI Agent Overview

AI Agents are a combination of LLMs and Tools. Each tool can perform a specific task, and the LLM can use them to perform complex tasks, requested by the user. AI Agents are a powerful tool for automating complex tasks in the cloud, and they are a great way to reduce the cost of building and maintaining complex systems.

## MLOps of AI Agents

There are a few frameworks for MLOps of AI Agents, such as: LangGraph, Crew.ai, Pydanic AI, etc. There are also some cloud platforms that can be used to build and deploy AI Agents, such as Amazon Bedrock, Google Vertex AI, and Azure OpenAI. There are cons and pros for each of these frameworks and platforms. The proposed implementation of AI Agents in AWS Step Functions is solving most of the problems with the existing frameworks and platforms.

## AI Agent Implementation

The AI Agent implementation in AWS Step Functions is based on the following steps:

1. Develop Lambda functions which are the tools for the AI Agent. These functions can be used to perform complex tasks, such as calling APIs, querying databases, etc.
2. Develop Lambda function which calls your preferred LLM for the AI Agent. 
3. Create a Step Function which orchestrate the AI Agent. This Step Function calls the LLM and passes the results to the tools.

This repository contains an example of some tools that are used to build a SQL Agent. Each Lambda function is implemented under the `lambda` directory. The `CDK` stack integrates all the Lambda functions into the Step Function flow to build the AI Agent.

Please note that each Lambda function is implemented in a dedicated directory and has its own requirements.txt file. The requirements.txt file is used to install the required Python packages for the Lambda function, by the `CDK` stack.


## uv Set up

### For MacOS with Apple silicon

```shell
uv python install cpython-3.12.3-macos-aarch64-none
uv venv --python cpython-3.12.3-macos-aarch64-none 
source .venv/bin/activate 
uv pip compile requirements.in --output-file requirements.txt 
uv pip sync requirements.txt
```