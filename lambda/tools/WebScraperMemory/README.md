# Rust Tool: WebScraperMemory

![Rust logo](https://cdn.simpleicons.org/rust/gray?size=48)

This directory contains the implementation of the tools WebScraperMemory in **Rust**.

## Purpose

The WebScraperMemory Lambda function tool is part of an AI agent that learns and extracts information from websites. The Memory component is responsible for storing and retrieving data from a DynamoDB table, for the extraction scripts that are performed by the WebScraper tool. The tool read and writes two types of records:

* Site Schema - Describes the site functionality and the set of scripts that are already available to extract information from the site.
* Extraction Script - Describes a script that can be used to extract specific type of information from the site.

The WebScraperMemory tool helps the AI Agent, and its LLM model to quickly learn and adapt to new sites, and to be able to extract information from them, efficiently once a successful script is created.

## Folder structure

```txt
WebScraperMemory/
├── src/
│   └── event_handler.rs
│   └── main.rs
├── Cargo.toml
└── README.md
```

## Tool list

The tools are:

* `get_site_schema`: Get the site schema from the memory. The schema includes the set of scripts that are already available to extract information from the site, as well as information about the site itself.
* `get_extraction_script`: Get the extraction script from the memory. The script is used to extract specific type of information from the site.
* `save_site_schema`: Save the site schema to the memory. The schema includes the set of scripts that are already available to extract information from the site, as well as information about the site itself.
* `save_extraction_script`: Save the extraction script to the memory. The script is used to extract specific type of information from the site.

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
sam local invoke WebScraperMemory --event tests/test-event.json
```

## Deployment

The deployment can be done using the AWS CDK or the AWS SAM CLI.

### CDK

The CDK stack is defined with the rest of the AI Agent definition to allow full application deployment. Here is the function and tools definitions in the [CDK Stack](../../step_functions_agent/step_functions_graphql_agent_stack.py).

```python
        ## Function Tools in Rust
        # Rust Lambda
        WebScraperMemory_lambda_function = _lambda.Function(
            self, 
            "WebScraperMemoryLambda",
            function_name="WebScraperMemoryTools",
            description="Memory of web scraping extractions from various web sites with store and retrieve functionalities. using Rust.",
            code=_lambda.Code.from_asset("lambda/tools/WebScraperMemory/target/lambda/WebScraperMemory"), 
            handler="main",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            role=tool_lambda_role
        )

    # Create graphql tools
    tools = [
        Tool(
            "WebScraperMemory",
            "Memory of web scraping extractions from various web sites with store and retrieve functionalities..",
            WebScraperMemory_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL address of the web site to scrape.."
                    }
                },
                "required": [
                    "url",
                ]
            }
        )
    ]  # type: list[Tool]
```

Then you can add the stack the main CDK stack (`app.py`) that defines the AI Agent application.

```python
from step_functions_agent.step_functions_url_agent_stack import WebScraperMemoryAgentStack
WebScraperMemoryAgentStack = urlAgentStack(app, "WebScraperMemoryAgentStack")
```

Finally, you can deploy the stack using the following command:

```bash
cdk deploy WebScraperMemoryAgentStack
```
