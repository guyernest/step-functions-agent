use opentelemetry::{global, KeyValue, Context};
use opentelemetry::baggage::BaggageExt;
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::{Resource};
use opentelemetry_sdk::trace;
use tracing_subscriber::EnvFilter;
use tokio::time::{sleep, Duration};

pub fn init_otel(service_name: &str, agent_log_group: &str) -> Result<(), Box<dyn std::error::Error>> {
    // For now, just keep the existing JSON logging until we resolve the OTel compatibility issues
    // This ensures the service continues to work while we iterate on the observability
    
    // Initialize JSON logging (existing functionality)
    tracing_subscriber::fmt()
        .json()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .with_target(false)
        .with_current_span(false)
        .init();
    
    // Set up OpenTelemetry resources with enriched attributes
    let resource = Resource::new(vec![
        KeyValue::new("service.name", service_name.to_string()),
        KeyValue::new("aws.log.group.names", agent_log_group.to_string()),
        KeyValue::new("aws.local.service", "sf-agents"),
        KeyValue::new("aws.local.environment", "production"),
        KeyValue::new("application", "StepFunctionsAgent"),
        KeyValue::new("component", "llm-service"),
    ]);
    
    // TRACE exporter → local ADOT collector (Lambda extension) on 4318
    // Note: This is prepared but not actively used yet due to compatibility issues
    let _tracer_provider = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_trace_config(trace::config().with_resource(resource.clone()))
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .http()
                .with_endpoint("http://127.0.0.1:4318/v1/traces"))
        .install_batch(opentelemetry_sdk::runtime::Tokio)?;
    
    // METRICS exporter → local collector (forwarded to CloudWatch via EMF)
    let meter_provider = opentelemetry_otlp::new_pipeline()
        .metrics(opentelemetry_sdk::runtime::Tokio)
        .with_resource(resource)
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .http()
                .with_endpoint("http://127.0.0.1:4318/v1/metrics"))
        .build()?;
    
    global::set_meter_provider(meter_provider);
    
    Ok(())
}

pub fn context_with_session(session_id: &str) -> Context {
    let mut ctx = Context::current();
    ctx = ctx.with_baggage(vec![KeyValue::new("session.id", session_id.to_string())]);
    ctx
}

// Helper to record token usage and cost metrics
pub fn record_token_metrics(
    provider: &str,
    model: &str,
    input_tokens: u64,
    output_tokens: u64,
    cost_usd: f64,
    _session_ctx: &Context,
) {
    let meter = global::meter("sf-agents");
    let token_counter = meter.u64_counter("gen_ai.client.token.usage").init();
    let cost_counter = meter.f64_counter("gen_ai.client.cost.usd").init();

    // Record input tokens
    token_counter.add(
        input_tokens,
        &[
            KeyValue::new("kind", "input"),
            KeyValue::new("gen_ai.request.model", model.to_string()),
            KeyValue::new("gen_ai.system", provider.to_string()),
        ],
    );

    // Record output tokens
    token_counter.add(
        output_tokens,
        &[
            KeyValue::new("kind", "output"),
            KeyValue::new("gen_ai.request.model", model.to_string()),
            KeyValue::new("gen_ai.system", provider.to_string()),
        ],
    );

    // Record cost
    cost_counter.add(
        cost_usd,
        &[
            KeyValue::new("gen_ai.request.model", model.to_string()),
            KeyValue::new("gen_ai.system", provider.to_string()),
        ],
    );
}

// Flush telemetry data and wait for ADOT collector to export
pub async fn flush_telemetry() {
    // Give the ADOT collector extension time to process and export the data
    // This is necessary because Lambda may freeze the execution environment
    // before the extension can complete its work
    // 
    // The ADOT collector runs as a separate process and needs time to:
    // 1. Receive the OTLP data from our application
    // 2. Process it through its pipeline
    // 3. Export to CloudWatch/X-Ray
    //
    // Without this delay, Lambda may suspend before the collector finishes
    sleep(Duration::from_millis(500)).await;
}