use lambda_runtime::{service_fn, Error, LambdaEvent};
use serde_json::Value;
use std::sync::Arc;
use tracing::{error, info};

mod error;
mod models;
mod secrets;
mod service;
mod transformers;

use crate::models::{LLMInvocation, LLMResponse};
use crate::service::UnifiedLLMService;

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .json()
        .with_target(false)
        .with_current_span(false)
        .init();

    info!("Initializing Unified LLM Service");

    // Create service instance
    let service = Arc::new(UnifiedLLMService::new().await?);

    info!("Service initialized, starting Lambda runtime");

    // Run Lambda runtime
    lambda_runtime::run(service_fn(move |event: LambdaEvent<Value>| {
        let service = service.clone();
        async move { handle_request(event, service).await }
    }))
    .await
}

async fn handle_request(
    event: LambdaEvent<Value>,
    service: Arc<UnifiedLLMService>,
) -> Result<LLMResponse, Error> {
    let start = std::time::Instant::now();

    // Parse invocation
    let invocation: LLMInvocation = serde_json::from_value(event.payload)
        .map_err(|e| {
            error!("Failed to parse invocation: {}", e);
            e
        })?;

    info!(
        provider_id = %invocation.provider_config.provider_id,
        model_id = %invocation.provider_config.model_id,
        message_count = invocation.messages.len(),
        has_tools = invocation.tools.is_some(),
        "Processing LLM request"
    );

    // Process request
    let response = service.process(invocation).await.map_err(|e| {
        error!("Failed to process request: {}", e);
        e
    })?;

    let latency = start.elapsed();
    info!(
        latency_ms = latency.as_millis() as u64,
        tokens_input = response.metadata.tokens_used.as_ref().map(|t| t.input_tokens).unwrap_or(0),
        tokens_output = response.metadata.tokens_used.as_ref().map(|t| t.output_tokens).unwrap_or(0),
        "Request completed successfully"
    );

    Ok(response)
}