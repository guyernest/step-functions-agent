---
sidebar_position: 2
---

# Building a Tool in Rust

![Rust logo](https://cdn.simpleicons.org/rust/gray?size=48)

This tutorial will guide you through creating a tool in Rust that can be deployed as an AWS Lambda function. We'll create a simple clustering tool that accepts data and returns clustering results.

## Prerequisites

Before starting, ensure you have:

- [Rust](https://www.rust-lang.org/tools/install) installed
- [Cargo Lambda](https://www.cargo-lambda.info/guide/installation.html) installed
- AWS CLI configured with appropriate credentials

## Project Setup

1. Create a new Rust Lambda project:

    ```bash
    cargo lambda new my-clustering-tool
    cd my-clustering-tool
    ```

2. Add necessary dependencies to `Cargo.toml`:

    ```toml
    [package]
    name = "my-clustering-tool"
    version = "0.1.0"
    edition = "2021"

    [dependencies]
    lambda_runtime = "0.8"
    serde = { version = "1.0", features = ["derive"] }
    serde_json = "1.0"
    tokio = { version = "1", features = ["full"] }
    tracing = { version = "0.1" }
    tracing-subscriber = { version = "0.3" }
    ```

## Basic Structure

Create the following structure for your tool:

```txt
my-clustering-tool/
├── src/
│   ├── main.rs
│   └── clustering.rs
├── Cargo.toml
└── README.md
```

## Implementing the Tool

1. First, let's create our data structures in `main.rs`:

    ```rust
    use lambda_runtime::{service_fn, LambdaEvent, Error};
    use serde::{Deserialize, Serialize};
    use serde_json::Value;

    #[derive(Deserialize, Debug)]
    struct ToolUsePayload {
        id: String,
        name: String,
        input: Value,
    }

    #[derive(Serialize, Debug)]
    struct ToolUseResponse {
        tool_use_id: String,
        name: String,
        #[serde(rename = "type")]
        response_type: String,
        content: String,
    }

    async fn function_handler(event: LambdaEvent<Value>) -> Result<ToolUseResponse, Error> {
        // We'll implement this next
    }

    #[tokio::main]
    async fn main() -> Result<(), Error> {
        tracing_subscriber::fmt()
            .with_ansi(false)
            .without_time()
            .with_max_level(tracing::Level::INFO)
            .init();

        let func = service_fn(function_handler);
        lambda_runtime::run(func).await?;
        Ok(())
    }
    ```

2. Implement the handler function:

    ```rust
    async fn function_handler(event: LambdaEvent<Value>) -> Result<ToolUseResponse, Error> {
        let payload: ToolUsePayload = serde_json::from_value(event.payload)?;
        
        let result = match payload.name.as_str() {
            "calculate_clusters" => {
                // Call your clustering implementation
                handle_clustering(payload.input).await?
            }
            _ => {
                serde_json::to_string(&serde_json::json!({
                    "error": "Unknown tool name"
                }))?
            }
        };

        Ok(ToolUseResponse {
            tool_use_id: payload.id,
            name: payload.name,
            response_type: "tool_result".to_string(),
            content: result,
        })
    }
    ```

3. Create a clustering implementation in `clustering.rs`:

    ```rust
    use serde_json::Value;
    use std::error::Error;

    pub async fn handle_clustering(input: Value) -> Result<String, Box<dyn Error>> {
        // Your clustering logic here
        // This is a simple example that just returns the input
        Ok(serde_json::to_string(&input)?)
    }
    ```

## Building and Testing

1. Build your function:

    ```bash
    cargo lambda build --release
    ```

2. Create a test event file `test-event.json`:

    ```json
    {
        "id": "test-1",
        "name": "calculate_clusters",
        "input": {
            "data": [1, 2, 3, 4, 5]
        }
    }
    ```

3. Test locally:

    ```bash
    cargo lambda invoke --data-file test-event.json
    ```

## Error Handling

Add proper error handling to your tool:

```rust
#[derive(Debug)]
enum ToolError {
    InvalidInput(String),
    ProcessingError(String),
}

impl std::error::Error for ToolError {}

impl std::fmt::Display for ToolError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ToolError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            ToolError::ProcessingError(msg) => write!(f, "Processing error: {}", msg),
        }
    }
}
```

## Working with AWS Services

If your tool needs to interact with AWS services, add the relevant SDK:

```toml
[dependencies]
aws-config = "0.55"
aws-sdk-s3 = "0.55"
```

Example S3 interaction:

```rust
use aws_sdk_s3::Client;

async fn read_from_s3(bucket: &str, key: &str) -> Result<Vec<u8>, Error> {
    let config = aws_config::load_from_env().await;
    let client = Client::new(&config);
    
    let resp = client
        .get_object()
        .bucket(bucket)
        .key(key)
        .send()
        .await?;
        
    Ok(resp.body.collect().await?.into_bytes().to_vec())
}
```

## Deployment

1. Build for production:

    ```bash
    cargo lambda build --release --arm64
    ```

2. The function can be deployed using AWS CDK:

    ```typescript
    import * as lambda from 'aws-cdk-lib/aws-lambda';

    const clusteringLambda = new lambda.Function(this, 'ClusteringLambda', {
        functionName: 'ClusteringTool',
        code: lambda.Code.fromAsset('target/lambda/my-clustering-tool'),
        handler: 'main',
        runtime: lambda.Runtime.PROVIDED_AL2023,
        architecture: lambda.Architecture.ARM_64,
        timeout: cdk.Duration.seconds(30),
        memorySize: 128
    });
    ```

## Best Practices

1. **Logging**: Use the `tracing` crate for structured logging:

    ```rust
    tracing::info!("Processing input: {:?}", input);
    ```

2. **Configuration**: Use environment variables for configuration:

    ```rust
    let config_value = std::env::var("CONFIG_NAME").unwrap_or_default();
    ```

3. **Testing**: Add unit tests:

    ```rust
    #[cfg(test)]
    mod tests {
        use super::*;

        #[tokio::test]
        async fn test_clustering() {
            let input = serde_json::json!({
                "data": [1, 2, 3]
            });
            let result = handle_clustering(input).await;
            assert!(result.is_ok());
        }
    }
    ```

## Common Issues and Solutions

1. **Cold Start**: Minimize dependencies and use `lazy_static` for initialization:

    ```rust
    use lazy_static::lazy_static;

    lazy_static! {
        static ref CLIENT: Client = Client::new();
    }
    ```

2. **Memory Usage**: Profile your application:

    ```bash
    cargo install flamegraph
    cargo flamegraph
    ```

3. **Timeouts**: Implement proper timeout handling:

    ```rust
    use tokio::time::timeout;
    use std::time::Duration;

    let result = timeout(
        Duration::from_secs(25),
        your_long_running_function()
    ).await??;
    ```
