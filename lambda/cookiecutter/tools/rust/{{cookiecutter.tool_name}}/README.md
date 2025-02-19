# Rust Tool: {{cookiecutter.tool_name}}

![Rust logo](https://cdn.simpleicons.org/rust/gray?size=48)

This directory contains the implementation of the tools {{cookiecutter.tool_name}} in **Rust**.

## Folder structure

```txt
{{cookiecutter.tool_name}}/
├── src/
│   └── event_handler.rs
│   └── main.rs
├── Cargo.toml
└── README.md
```

## Tool list

The tools are:

* `{{cookiecutter.tool_name}}`: {{cookiecutter.tool_description}}.

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
sam local invoke {{cookiecutter.tool_name}} --event tests/test-event.json
```

## Deployment

The deployment can be done using the AWS CDK or the AWS SAM CLI.

### CDK

The CDK stack is defined with the rest of the AI Agent definition to allow full application deployment. Here is the function and tools definitions in the [CDK Stack](../../step_functions_agent/step_functions_graphql_agent_stack.py).

```python
        ## Function Tools in Rust
        # Rust Lambda
        {{cookiecutter.tool_name}}_lambda_function = _lambda.Function(
            self, 
            "{{cookiecutter.tool_name}}Lambda",
            function_name="{{cookiecutter.tool_name}}Tools",
            description="{{cookiecutter.tool_description}} using Rust.",
            code=_lambda.Code.from_asset("lambda/tools/{{cookiecutter.tool_name}}/target/lambda/{{cookiecutter.tool_name}}"), 
            handler="main",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            role=tool_lambda_role
        )

    # Create graphql tools
    tools = [
        Tool(
            "{{cookiecutter.tool_name}}",
            "{{cookiecutter.tool_description}}.",
            {{cookiecutter.tool_name}}_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "{{cookiecutter.input_param_name}}": {
                        "type": "string",
                        "description": "{{cookiecutter.input_param_description}}."
                    }
                },
                "required": [
                    "{{cookiecutter.input_param_name}}",
                ]
            }
        )
    ]  # type: list[Tool]
```

Then you can add the stack the main CDK stack (`app.py`) that defines the AI Agent application.

```python
from step_functions_agent.step_functions_{{cookiecutter.input_param_name}}_agent_stack import {{cookiecutter.tool_name}}AgentStack
{{cookiecutter.tool_name}}AgentStack = {{cookiecutter.input_param_name}}AgentStack(app, "{{cookiecutter.tool_name}}AgentStack")
```

Finally, you can deploy the stack using the following command:

```bash
cdk deploy {{cookiecutter.tool_name}}AgentStack
```
