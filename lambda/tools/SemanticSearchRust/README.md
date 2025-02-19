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

## Semantic Indexing

We will use Qdrant as the vector database. Qdrant is a vector database that is used to store and search vectors. Vectors are mathematical representations of data. In our case, we will use vectors to represent the semantic meaning of text. Qdrant is fast as it is implemented also in Rust.
Qdrant is available as a managed service on [Qdrant Cloud](https://qdrant.tech/cloud/), which also includes a free tier. Once you launch a cluster, you can access the API key and the endpoint from the Qdrant Cloud console.

## Populate the Semantic Index

To populate the semantic index, we will use the notebooks [here](notebooks/pupulate_database.ipynb). The example takes a set of session descriptions from Re:Invent 2024 about AI. You can modify the notebook to use your own data.

## API Key

Tools often need to make requests to external APIs. This requires an API key. Although it is possible to use environment variables to store the API key, it is recommended to use a Secrets Manager to store the API key. The secrets are stored from the main CDK stack that reads the local various API keys from an .env file.

The following code snippet shows how to retrieve the API key from the Secrets Manager.

```rust
    // Handle Secrets
    let region_provider = RegionProviderChain::default_provider().or_else("us-west-2");
    let shared_config = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .region(region_provider)
        .load()
        .await;
    let secrets_client = aws_sdk_secretsmanager::Client::new(&shared_config);
    let name: &str = "/ai-agent/TOOL_NAME";
    let resp = secrets_client
        .get_secret_value()
        .secret_id(name)
        .send()
        .await?;
    let secret_json: serde_json::Value =
        serde_json::from_str(&resp.secret_string().unwrap_or_default())
            .expect("Failed to parse JSON");
    let api_key_value: String = secret_json["TOOL_API_KEY"]
        .as_str()
        .unwrap_or("No value!")
        .to_string();
```

Please note that for Qdrant Cloud you have to modify the port to 6334, as the default port 6333 is not working for the Rust client. For example modify the following line:

```text
QDRANT_URL="QDRANT_URL="https://XXXXXXXXXXXXXX.aws.cloud.qdrant.io:6333"
```

to:

```text
QDRANT_URL="QDRANT_URL="https://XXXXXXXXXXXXXX.aws.cloud.qdrant.io:6334"
```

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

Alternatively, you can use the SAM CLI to build the project:

```bash
sam build
```

## Testing

### Cargo test or nextest

You can run the tests using `cargo test` or `nextest` for faster test execution:

```bash
cargo test run
```

or

```bash
cargo nextest run
```

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
