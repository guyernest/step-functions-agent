use crate::error::ServiceError;
use crate::models::{
    LLMInvocation, LLMResponse, ProviderConfig, ResponseMetadata, TransformedRequest,
    TransformedResponse,
};
use crate::secrets::SecretManager;
use crate::transformers::TransformerRegistry;
use reqwest::{Client, Response};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tracing::{debug, error, info, warn};

pub struct UnifiedLLMService {
    secret_manager: Arc<SecretManager>,
    http_client: Client,
    transformer_registry: Arc<TransformerRegistry>,
}

impl UnifiedLLMService {
    pub async fn new() -> Result<Self, ServiceError> {
        info!("Initializing UnifiedLLMService");

        let secret_manager = Arc::new(SecretManager::new().await?);
        
        let http_client = Client::builder()
            .timeout(Duration::from_secs(60))
            .connect_timeout(Duration::from_secs(10))
            .pool_max_idle_per_host(10)
            .build()
            .map_err(|e| ServiceError::HttpError(e))?;

        let transformer_registry = Arc::new(TransformerRegistry::new());

        Ok(Self {
            secret_manager,
            http_client,
            transformer_registry,
        })
    }

    pub async fn process(&self, invocation: LLMInvocation) -> Result<LLMResponse, ServiceError> {
        let start = Instant::now();

        // 1. Get API key from Secrets Manager
        let api_key = self
            .secret_manager
            .get_api_key(
                &invocation.provider_config.secret_path,
                &invocation.provider_config.secret_key_name,
            )
            .await?;

        // 2. Get transformer for request
        let request_transformer = self
            .transformer_registry
            .get(&invocation.provider_config.request_transformer)?;

        // 3. Transform request to provider format
        debug!("Transforming request to provider format");
        let transformed_request = request_transformer.transform_request(&invocation)?;

        // 4. Make HTTP request to provider
        let response = self
            .call_provider(&invocation.provider_config, transformed_request, &api_key)
            .await?;

        // 5. Get transformer for response
        let response_transformer = self
            .transformer_registry
            .get(&invocation.provider_config.response_transformer)?;

        // 6. Transform response to unified format
        debug!("Transforming response to unified format");
        let transformed_response = response_transformer.transform_response(response)?;

        // 7. Build final response with metadata
        let latency_ms = start.elapsed().as_millis() as u64;
        
        Ok(LLMResponse {
            message: transformed_response.message,
            function_calls: transformed_response.function_calls,
            metadata: ResponseMetadata {
                model_id: invocation.provider_config.model_id.clone(),
                provider_id: invocation.provider_config.provider_id.clone(),
                latency_ms,
                tokens_used: transformed_response.usage,
                stop_reason: transformed_response.stop_reason,
            },
        })
    }

    async fn call_provider(
        &self,
        config: &ProviderConfig,
        request: TransformedRequest,
        api_key: &str,
    ) -> Result<Value, ServiceError> {
        info!(
            provider = %config.provider_id,
            endpoint = %config.endpoint,
            "Making HTTP request to provider"
        );

        // Build request
        let mut req = self
            .http_client
            .post(&config.endpoint)
            .timeout(Duration::from_secs(config.timeout))
            .json(&request.body);

        // Add authentication header
        let auth_value = if let Some(prefix) = &config.auth_header_prefix {
            format!("{}{}", prefix, api_key)
        } else {
            api_key.to_string()
        };
        req = req.header(&config.auth_header_name, auth_value);

        // Add custom headers
        if let Some(custom_headers) = &config.custom_headers {
            for (key, value) in custom_headers {
                req = req.header(key, value);
            }
        }

        // Add request headers from transformer
        for (key, value) in request.headers {
            req = req.header(key, value);
        }

        // Send request
        let response = req.send().await.map_err(|e| {
            error!("HTTP request failed: {}", e);
            ServiceError::HttpError(e)
        })?;

        // Check status
        let status = response.status();
        if !status.is_success() {
            let error_body = response.text().await.unwrap_or_else(|_| "No error body".to_string());
            error!(
                provider = %config.provider_id,
                status = %status,
                error = %error_body,
                "Provider API error"
            );
            return Err(ServiceError::ProviderApiError {
                provider: config.provider_id.clone(),
                status: status.as_u16(),
                message: error_body,
            });
        }

        // Parse response
        let response_body = response.json::<Value>().await.map_err(|e| {
            error!("Failed to parse provider response: {}", e);
            ServiceError::HttpError(e)
        })?;

        debug!(
            provider = %config.provider_id,
            "Successfully received response from provider"
        );

        Ok(response_body)
    }
}