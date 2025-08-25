use lambda_runtime::{service_fn, Error, LambdaEvent};
use serde_json::Value;
use std::sync::Arc;
use tracing::{error, info};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod error;
mod models;
mod secrets;
mod service;
mod telemetry;
mod transformers;

use crate::models::{LLMInvocation, LLMResponse};
use crate::service::UnifiedLLMService;

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize OpenTelemetry and tracing
    // Note: If telemetry fails, we log the error but continue running
    if let Err(e) = telemetry::init_otel(
        "sf-agents",  // Simplified to match OTEL_RESOURCE_ATTRIBUTES
        "/aws/bedrock-agentcore/runtimes/sf-agents"
    ) {
        eprintln!("Warning: Failed to initialize telemetry: {}. Continuing without observability.", e);
        // Initialize basic JSON logging as fallback
        tracing_subscriber::fmt()
            .json()
            .with_env_filter(
                tracing_subscriber::EnvFilter::try_from_default_env()
                    .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
            )
            .with_target(false)
            .with_current_span(false)
            .init();
    }

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
    use tracing::Instrument;
    
    let start = std::time::Instant::now();

    // Parse invocation
    let invocation: LLMInvocation = serde_json::from_value(event.payload)
        .map_err(|e| {
            error!("Failed to parse invocation: {}", e);
            e
        })?;

    // Extract session ID from Lambda request context or generate one
    // For now, we'll use a default session ID
    // In production, you might extract this from Step Functions execution context
    let session_id = "default-session".to_string();
    
    let session_ctx = telemetry::context_with_session(&session_id);
    
    info!(
        provider_id = %invocation.provider_config.provider_id,
        model_id = %invocation.provider_config.model_id,
        message_count = invocation.messages.len(),
        has_tools = invocation.tools.is_some(),
        "Processing LLM request"
    );

    // Create span for LLM call with Gen-AI semantic convention attributes
    let span = tracing::span!(
        tracing::Level::INFO,
        "genai.chat",
        "gen_ai.system" = %invocation.provider_config.provider_id,
        "gen_ai.request.model" = %invocation.provider_config.model_id,
        "gen_ai.usage.input_tokens" = tracing::field::Empty,
        "gen_ai.usage.output_tokens" = tracing::field::Empty,
        "aws.local.operation" = "ProcessLLMRequest",
    );

    // Process request within the span
    let response = async {
        service.process(invocation.clone()).await.map_err(|e| {
            error!("Failed to process request: {}", e);
            e
        })
    }
    .instrument(span.clone())
    .await?;

    // Record token usage on the span
    if let Some(tokens) = &response.metadata.tokens_used {
        span.record("gen_ai.usage.input_tokens", &tokens.input_tokens);
        span.record("gen_ai.usage.output_tokens", &tokens.output_tokens);
        
        // Calculate cost (this would use your actual pricing logic)
        let cost_usd = calculate_cost(
            &invocation.provider_config.provider_id,
            &invocation.provider_config.model_id,
            tokens.input_tokens,
            tokens.output_tokens,
        );
        
        // Record metrics
        telemetry::record_token_metrics(
            &invocation.provider_config.provider_id,
            &invocation.provider_config.model_id,
            tokens.input_tokens as u64,
            tokens.output_tokens as u64,
            cost_usd,
            &session_ctx,
        );
    }

    let latency = start.elapsed();
    info!(
        latency_ms = latency.as_millis() as u64,
        tokens_input = response.metadata.tokens_used.as_ref().map(|t| t.input_tokens).unwrap_or(0),
        tokens_output = response.metadata.tokens_used.as_ref().map(|t| t.output_tokens).unwrap_or(0),
        "Request completed successfully"
    );

    // Flush OpenTelemetry data before Lambda completes
    // Give the ADOT collector time to export metrics
    telemetry::flush_telemetry().await;

    Ok(response)
}

// Simple cost calculation function - you should replace with your actual pricing logic
fn calculate_cost(provider: &str, model: &str, input_tokens: u32, output_tokens: u32) -> f64 {
    // Example pricing - replace with your actual pricing data
    let (input_price, output_price) = match (provider, model) {
        ("openai", "gpt-4o-mini") => (0.00015, 0.0006),  // per 1k tokens
        ("anthropic", "claude-3-5-sonnet-20241022") => (0.003, 0.015),
        ("bedrock", "claude-3-5-sonnet-20241022") => (0.003, 0.015),
        _ => (0.001, 0.002), // default
    };
    
    (input_tokens as f64 / 1000.0) * input_price + (output_tokens as f64 / 1000.0) * output_price
}