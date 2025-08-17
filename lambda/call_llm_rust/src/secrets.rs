use crate::error::ServiceError;
use aws_sdk_secretsmanager::Client as SecretsClient;
use dashmap::DashMap;
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tracing::{debug, info, warn};

const CACHE_TTL: Duration = Duration::from_secs(300); // 5 minutes

#[derive(Clone)]
struct CachedSecret {
    value: HashMap<String, String>,
    expires_at: Instant,
}

pub struct SecretManager {
    client: Arc<SecretsClient>,
    cache: Arc<DashMap<String, CachedSecret>>,
}

impl SecretManager {
    pub async fn new() -> Result<Self, ServiceError> {
        let config = aws_config::load_from_env().await;
        let client = SecretsClient::new(&config);

        Ok(Self {
            client: Arc::new(client),
            cache: Arc::new(DashMap::new()),
        })
    }

    pub async fn get_api_key(
        &self,
        secret_path: &str,
        key_name: &str,
    ) -> Result<String, ServiceError> {
        debug!(
            secret_path = %secret_path,
            key_name = %key_name,
            "Retrieving API key"
        );

        // For testing: check environment variable first
        #[cfg(test)]
        {
            if let Ok(value) = std::env::var(key_name) {
                debug!("Using API key from environment variable for testing");
                return Ok(value);
            }
        }

        // Check cache first
        if let Some(cached) = self.cache.get(secret_path) {
            if cached.expires_at > Instant::now() {
                debug!("Using cached secret");
                if let Some(api_key) = cached.value.get(key_name) {
                    return Ok(api_key.clone());
                }
                return Err(ServiceError::SecretKeyNotFound(
                    key_name.to_string(),
                    secret_path.to_string(),
                ));
            } else {
                debug!("Cache expired, removing entry");
                drop(cached); // Release the lock before removing
                self.cache.remove(secret_path);
            }
        }

        // Fetch from Secrets Manager
        info!(secret_path = %secret_path, "Fetching secret from AWS Secrets Manager");
        
        let response = self
            .client
            .get_secret_value()
            .secret_id(secret_path)
            .send()
            .await
            .map_err(|e| {
                warn!("Failed to fetch secret: {}", e);
                ServiceError::AwsSdkError(e.into())
            })?;

        let secret_string = response
            .secret_string()
            .ok_or_else(|| ServiceError::SecretNotFound(secret_path.to_string()))?;

        // Parse JSON structure
        let secret_json: Value = serde_json::from_str(secret_string)
            .map_err(|e| {
                warn!("Failed to parse secret JSON: {}", e);
                ServiceError::JsonError(e)
            })?;

        // Convert to HashMap
        let secret_map: HashMap<String, String> = if let Value::Object(map) = secret_json {
            map.into_iter()
                .filter_map(|(k, v)| {
                    if let Value::String(s) = v {
                        Some((k, s))
                    } else {
                        warn!("Skipping non-string value for key: {}", k);
                        None
                    }
                })
                .collect()
        } else {
            return Err(ServiceError::InvalidConfiguration(
                "Secret is not a JSON object".to_string(),
            ));
        };

        // Extract the specific key
        let api_key = secret_map
            .get(key_name)
            .ok_or_else(|| {
                ServiceError::SecretKeyNotFound(key_name.to_string(), secret_path.to_string())
            })?
            .clone();

        // Cache for future use
        let cached = CachedSecret {
            value: secret_map,
            expires_at: Instant::now() + CACHE_TTL,
        };
        self.cache.insert(secret_path.to_string(), cached);

        info!(
            secret_path = %secret_path,
            key_name = %key_name,
            "Successfully retrieved and cached API key"
        );

        Ok(api_key)
    }

    pub fn clear_cache(&self) {
        info!("Clearing secret cache");
        self.cache.clear();
    }
}