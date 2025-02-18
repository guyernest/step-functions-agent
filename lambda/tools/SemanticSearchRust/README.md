# Rust Tool: SemanticSearchRust

![Rust logo](https://cdn.simpleicons.org/rust/gray?size=48)

This directory contains the implementation of the tools SemanticSearchRust in **Rust**.

## Folder structure

```txt
SemanticSearchRust/
├── src/
│   └── event_handler.rs
│   └── main.rs
├── Cargo.toml
└── README.md
```

## Tool list

The tools are:

* `SemanticSearchRust`: Semantic search using vector database (Qdrant) in Rust.

## Prerequisites

* [Rust](https://www.rust-lang.org/tools/install)
* [Cargo Lambda](https://www.cargo-lambda.info/guide/installation.html)

## Building

To build the project for production, run:

```bash
cargo lambda build --arm64 --release
```

Please note that the `--arm64` flag is needed to build for ARM64, as we want to reduce the cost of AWS Lambda functions, and we define the architecture as `arm64` in the Stack. Remove the `--release` flag to build for development.

Read more about building your lambda function in [the Cargo Lambda documentation](https://www.cargo-lambda.info/commands/build.html).

## Testing

### AWS SAM CLI

The AWS Function is defined in the `template.yaml` file. You can test the Lambda function locally using the AWS SAM CLI. The following command will invoke the Lambda function locally using the `tests/event.json` file as the input event:

```bash
sam build
sam local invoke SemanticSearchRust --event tests/test-event.json
```

## Deployment

The deployment can be done using the AWS CDK or the AWS SAM CLI.

### CDK

The CDK stack is defined with the rest of the AI Agent definition to allow full application deployment. Here is the function and tools definitions in the [CDK Stack](../../step_functions_agent/step_functions_graphql_agent_stack.py).

```python
        ## Function Tools in Rust
        # Rust Lambda
        SemanticSearchRust_lambda_function = _lambda.Function(
            self, 
            "SemanticSearchRustLambda",
            function_name="SemanticSearchRustTools",
            description="Semantic search using vector database (Qdrant) in Rust using Rust.",
            code=_lambda.Code.from_asset("lambda/tools/SemanticSearchRust/target/lambda/SemanticSearchRust"), 
            handler="main",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            role=tool_lambda_role
        )

    # Create graphql tools
    tools = [
        Tool(
            "SemanticSearchRust",
            "Semantic search using vector database (Qdrant) in Rust.",
            SemanticSearchRust_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "The search query to the semantic index.."
                    }
                },
                "required": [
                    "search_query",
                ]
            }
        )
    ]  # type: list[Tool]
```

Then you can add the stack the main CDK stack (`app.py`) that defines the AI Agent application.

```python
from step_functions_agent.step_functions_search_query_agent_stack import SemanticSearchRustAgentStack
SemanticSearchRustAgentStack = search_queryAgentStack(app, "SemanticSearchRustAgentStack")
```

Finally, you can deploy the stack using the following command:

```bash
cdk deploy SemanticSearchRustAgentStack
```
