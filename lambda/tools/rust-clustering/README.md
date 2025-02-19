# Rust Example: Clustering Tools

![Rust logo](https://cdn.simpleicons.org/rust/gray?size=48)

This directory contains the implementation of the tools for Time Series Clustering AI Agent in **Rust**.

## Folder structure

```txt
rust-clustering/
├── src/
│   └── event_handler.rs
│   └── main.rs
├── Cargo.toml
└── README.md
```

## Tool list

The tools are:

* `calculate_hdbscan_clusters`: Calculate clusters using hdbscan algorithm.

## Input and output

The Lambda function for the tools receive the input as a JSON object, and return the output as a JSON object.

```rust
#[derive(Deserialize, Debug)]
pub struct ToolUsePayload {
    pub id: String,
    pub name: String,
    pub input: Value,
}

#[derive(Serialize, Debug)]
pub struct ToolUseResponse {
    pub tool_use_id: String,
    pub name: String,
    #[serde(rename = "type")]
    pub response_type: String,
    pub content: String,
}

pub(crate) async fn function_handler(event: LambdaEvent<Value>) -> Result<ToolUseResponse, Error> {
    let payload: ToolUsePayload = match serde_json::from_value(event.payload.clone()) {
        Ok(payload) => payload,
        Err(e) => {
            println!("Failed to parse payload: {}", e);
            ToolUsePayload::default()
        }
    };
    tracing::info!("Payload: {:?}", payload);

    let result: String;

    match payload.name.as_str() {
        "calculate_hdbscan_clusters" => {
            tracing::info!("Calculating clusters using HDBSCAN");
            result = calculate_hdbscan_clusters(payload.input).await;
        }
        ...
        _ => {
            tracing::error!("Unknown tool_name: {}", payload.name);
            result = serde_json::to_string(&serde_json::json!({
                "error": "Unknown tool_name",
            }))?;
        }
    }
    ...
}
```

The tools return the output as a JSON object, with the result in the `content` field as a string.

```rust
    ...
    Ok(ToolUseResponse {
        tool_use_id: payload.id,
        name: payload.name,
        response_type: "tool_result".to_string(),
        content: result,
    })
}
```

## API Key

Tools often need to make requests to external APIs, such as Google Maps API. This requires an API key. Although it is possible to use environment variables to store the API key, it is recommended to use a Secrets Manager to store the API key. The secrets are stored from the main CDK stack that reads the local various API keys from an .env file.

The following code snippet shows how to initialize the API key.

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

## Setup

To set up the project, run:

```bash
cargo lambda new rust-clustering 
# When prompted, choose No for the HTTP question
# ? Is this function an HTTP function? (y/N)
# and then choose `serde_json::Value` for the event type
# ? Event type that this function receives

# Install dependencies
cargo add serde
cargo add aws_config 
cargo add aws_sdk_s3
```

## Building

To build the project for production, run:

```bash
cargo lambda build --arm64 --release
```

Please note that the `--arm64` flag is needed to build for ARM64, as we want to reduce the cost of AWS Lambda functions, and we define the architecture as `arm64` in the Stack. Remove the `--release` flag to build for development.

Read more about building your lambda function in [the Cargo Lambda documentation](https://www.cargo-lambda.info/commands/build.html).

## Testing

You can run regular Rust unit tests with `cargo test`.

If you want to run integration tests locally, you can use the `cargo lambda watch` and `cargo lambda invoke` commands to do it.

First, run `cargo lambda watch` to start a local server. When you make changes to the code, the server will automatically restart.

For generic events, where you define the event data structure, you can create a JSON file with the data you want to test with. For example:

```json
{
    "id": "calculate_hdbscan_clusters_unique_id",
    "name": "calculate_hdbscan_clusters",
    "input": {
        "bucket": "<BUCKET-NAME>",
        "key": "stock_vectors/stock_data_20250107_214201.csv"
    }
}
```

Then, run

```bash
cargo lambda invoke --data-file ./data.json
```

to invoke the function with the data in `data.json`.

## Deployment

The deployment is done using a CDK stack, which is implemented in the [step_functions_clustering_agent_stack.py](../../../step_functions_sql_agent/step_functions_clustering_agent_stack.py) file.

```python
## Forecasting Tools in Rust
# Rust Lambda
clustering_lambda = _lambda.Function(
    self, 
    "ClusteringLambda",
    function_name="ClusteringTools",
    code=_lambda.Code.from_asset("lambda/tools/rust-clustering/target/lambda/rust-clustering"), 
    handler="main",
    runtime=_lambda.Runtime.PROVIDED_AL2023,
    architecture=_lambda.Architecture.ARM_64,
    role=clustering_lambda_role
)
```
