# Buildspec Templates (Reference)

**Note:** These templates are provided as reference material. The actual build process uses the router in `buildspec.yml` at the root of the repository with the `BUILD_TYPE` environment variable to select the appropriate build process.

This directory contains reference buildspec templates for the various components of the step-functions-agent project. They can be used to:

1. Understand the build requirements for different component types
2. Provide guidance when adding a new component type to the main buildspec.yml router
3. Serve as standalone buildspec if needed for specialized workflows

The templates are organized by component type and programming language.

## CDK Stack Templates

Templates for synthesizing CDK stacks to CloudFormation:

- `cdk/buildspec-template.yml`: Generic template for any CDK stack
- `cdk/buildspec-sql-stack.yml`: Example for SQLAgentStack

## Lambda Function Templates by Language

Templates for building Lambda functions in different languages:

- `lambda/buildspec-python-lambda.yml`: Template for Python Lambda functions
- `lambda/buildspec-typescript-lambda.yml`: Template for TypeScript Lambda functions
- `lambda/buildspec-rust-lambda.yml`: Template for Rust Lambda functions
- `lambda/buildspec-go-lambda.yml`: Template for Go Lambda functions
- `lambda/buildspec-java-lambda.yml`: Template for Java Lambda functions
- `lambda/buildspec-lambda-extension.yml`: Special template for the Rust-based Lambda extension

## Example Files

The `examples/` directory contains concrete examples showing how to use the templates:

- `examples/typescript-lambda-example.yml`: Example for a specific TypeScript Lambda function (web-scraper)

## Relationship to Main Build Process

The main build process in `buildspec.yml` at the root of the repository consolidates functionality from these templates into a single router buildspec that selects the appropriate build process based on the `BUILD_TYPE` environment variable.

When adding a new component type to the main buildspec.yml, you can:

1. Reference these templates for guidance on the required build steps
2. Copy the relevant sections to the appropriate phases in the main buildspec
3. Add a new condition based on the component's BUILD_TYPE

## Generator Script (For Reference)

The `generate_buildspec.py` script can help you generate standalone buildspecs if needed:

```bash
# List available templates
./generate_buildspec.py list

# Generate a CDK stack buildspec
./generate_buildspec.py cdk SQLAgentStack --output buildspec-custom.yml

# Generate a Lambda function buildspec
./generate_buildspec.py lambda python lambda/tools/db-interface db-interface
```

## Code Build Environment

The build is performed in a CodeBuild project that can be cloned from the main project, and differ only in the BUILD_TYPE environment variable.

## Next Steps

The project is quite complex and requires some rearchitecting of the build process. The next steps are:

- How to handle the deployment of the API secrets from the .env file, without pushing them to the public GitHub repository.
- How to build the various lambda functions that are built now locally with the CDK or SAM CLI.
- How to build the CDK stack in a more flexible way, so that it can be used in a CI/CD pipeline.
- How to reuse functions such as the call_llm functions across the stacks.
- Add the CodeBuild project to a CDK stack, including the permissions needed to build the project, such as the S3 bucket for the artifacts.
- Point the CDK stacks to use the artifacts from the CodeBuild project.
- Add the CodeBuild project to a CodePipeline, so that the build is triggered by a commit to the repository.
