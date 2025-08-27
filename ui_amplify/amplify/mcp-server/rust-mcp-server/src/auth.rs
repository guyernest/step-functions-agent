//! API Key Authentication for Step Functions Agents MCP Server

use aws_sdk_dynamodb::{Client as DynamoDbClient, types::AttributeValue};
use anyhow::{Result, anyhow};
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use hex;
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use tracing::{info, warn};

/// API Key authentication client
pub struct ApiKeyAuth {
    dynamodb: DynamoDbClient,
    table_name: String,
}

/// Authentication result containing client information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthResult {
    pub client_id: String,
    pub client_name: String,
    pub permissions: Vec<String>,
    pub expires_at: DateTime<Utc>,
    pub usage_count: i64,
}

/// API Key record structure matching DynamoDB schema
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiKeyRecord {
    pub api_key_hash: String,
    pub client_id: String,
    pub client_name: String,
    pub created_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub last_used: Option<DateTime<Utc>>,
    pub is_active: bool,
    pub permissions: Vec<String>,
    pub usage_count: i64,
    pub created_by: String,
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

impl ApiKeyAuth {
    /// Create a new API key authentication client
    pub async fn new(aws_config: &aws_config::SdkConfig) -> Self {
        let dynamodb = DynamoDbClient::new(aws_config);
        let table_name = std::env::var("API_KEY_TABLE_NAME")
            .unwrap_or_else(|_| "step-functions-agents-prod-api-keys".to_string());
        
        info!("Initializing API key auth with table: {}", table_name);
        
        Self {
            dynamodb,
            table_name,
        }
    }
    
    /// Validate an API key and return authentication result
    pub async fn validate_api_key(&self, api_key: &str) -> Result<AuthResult> {
        // Hash the API key for secure lookup
        let api_key_hash = self.hash_api_key(api_key);
        
        info!("Validating API key hash: {}...", &api_key_hash[..8]);
        
        // Query DynamoDB for the API key
        let result = self.dynamodb
            .get_item()
            .table_name(&self.table_name)
            .key("api_key_hash", AttributeValue::S(api_key_hash.clone()))
            .send()
            .await
            .map_err(|e| anyhow!("Failed to query DynamoDB: {}", e))?;
        
        let item = result.item
            .ok_or_else(|| anyhow!("API key not found"))?;
        
        // Parse the record
        let record = self.parse_api_key_record(item)?;
        
        // Validate the API key
        self.validate_record(&record)?;
        
        // Update usage statistics (fire and forget)
        let _ = self.update_usage_stats(&api_key_hash).await;
        
        Ok(AuthResult {
            client_id: record.client_id,
            client_name: record.client_name,
            permissions: record.permissions,
            expires_at: record.expires_at,
            usage_count: record.usage_count,
        })
    }
    
    /// Hash an API key using SHA-256
    fn hash_api_key(&self, api_key: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(api_key.as_bytes());
        hex::encode(hasher.finalize())
    }
    
    /// Parse DynamoDB item into ApiKeyRecord
    fn parse_api_key_record(&self, item: HashMap<String, AttributeValue>) -> Result<ApiKeyRecord> {
        let api_key_hash = item.get("api_key_hash")
            .and_then(|v| v.as_s().ok())
            .ok_or_else(|| anyhow!("Missing api_key_hash"))?
            .clone();
            
        let client_id = item.get("client_id")
            .and_then(|v| v.as_s().ok())
            .ok_or_else(|| anyhow!("Missing client_id"))?
            .clone();
            
        let client_name = item.get("client_name")
            .and_then(|v| v.as_s().ok())
            .ok_or_else(|| anyhow!("Missing client_name"))?
            .clone();
            
        let created_at = item.get("created_at")
            .and_then(|v| v.as_s().ok())
            .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
            .map(|dt| dt.with_timezone(&Utc))
            .ok_or_else(|| anyhow!("Invalid created_at"))?;
            
        let expires_at = item.get("expires_at")
            .and_then(|v| v.as_s().ok())
            .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
            .map(|dt| dt.with_timezone(&Utc))
            .ok_or_else(|| anyhow!("Invalid expires_at"))?;
            
        let last_used = item.get("last_used")
            .and_then(|v| v.as_s().ok())
            .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
            .map(|dt| dt.with_timezone(&Utc));
            
        let is_active = item.get("is_active")
            .and_then(|v| v.as_bool().ok())
            .copied()
            .unwrap_or(false);
            
        let permissions = item.get("permissions")
            .and_then(|v| v.as_ss().ok())
            .map(|ss| ss.iter().cloned().collect())
            .unwrap_or_default();
            
        let usage_count = item.get("usage_count")
            .and_then(|v| v.as_n().ok())
            .and_then(|n| n.parse().ok())
            .unwrap_or(0);
            
        let created_by = item.get("created_by")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string())
            .unwrap_or_else(|| "unknown".to_string());
            
        // Parse metadata if present
        let metadata = item.get("metadata")
            .and_then(|v| v.as_m().ok())
            .map(|m| {
                let mut metadata = HashMap::new();
                for (key, value) in m {
                    if let Ok(json_value) = self.attribute_value_to_json(value) {
                        metadata.insert(key.clone(), json_value);
                    }
                }
                metadata
            });
            
        Ok(ApiKeyRecord {
            api_key_hash,
            client_id,
            client_name,
            created_at,
            expires_at,
            last_used,
            is_active,
            permissions,
            usage_count,
            created_by,
            metadata,
        })
    }
    
    /// Convert AttributeValue to serde_json::Value
    fn attribute_value_to_json(&self, value: &AttributeValue) -> Result<serde_json::Value> {
        match value {
            AttributeValue::S(s) => Ok(serde_json::Value::String(s.clone())),
            AttributeValue::N(n) => {
                if let Ok(int_val) = n.parse::<i64>() {
                    Ok(serde_json::Value::Number(serde_json::Number::from(int_val)))
                } else if let Ok(float_val) = n.parse::<f64>() {
                    Ok(serde_json::Value::Number(serde_json::Number::from_f64(float_val).unwrap_or(serde_json::Number::from(0))))
                } else {
                    Ok(serde_json::Value::String(n.clone()))
                }
            }
            AttributeValue::Bool(b) => Ok(serde_json::Value::Bool(*b)),
            AttributeValue::Null(_) => Ok(serde_json::Value::Null),
            _ => Ok(serde_json::Value::String(format!("{:?}", value))),
        }
    }
    
    /// Validate API key record
    fn validate_record(&self, record: &ApiKeyRecord) -> Result<()> {
        if !record.is_active {
            return Err(anyhow!("API key is inactive"));
        }
        
        if record.expires_at < Utc::now() {
            return Err(anyhow!("API key has expired"));
        }
        
        // Check if the key has required permissions for MCP operations
        let required_permissions = vec!["start_agent", "list_agents", "get_execution"];
        let has_all_permissions = record.permissions.iter().any(|p| p == "*") ||
            required_permissions.iter().all(|req| record.permissions.contains(&req.to_string()));
            
        if !has_all_permissions {
            warn!("API key {} has insufficient permissions: {:?}", record.client_id, record.permissions);
            return Err(anyhow!("Insufficient permissions"));
        }
        
        info!("API key validated for client: {} (permissions: {:?})", record.client_id, record.permissions);
        Ok(())
    }
    
    /// Update usage statistics for an API key
    async fn update_usage_stats(&self, api_key_hash: &str) -> Result<()> {
        let update_result = self.dynamodb
            .update_item()
            .table_name(&self.table_name)
            .key("api_key_hash", AttributeValue::S(api_key_hash.to_string()))
            .update_expression("SET last_used = :now, usage_count = usage_count + :inc")
            .expression_attribute_values(":now", AttributeValue::S(Utc::now().to_rfc3339()))
            .expression_attribute_values(":inc", AttributeValue::N("1".to_string()))
            .send()
            .await;
            
        if let Err(e) = update_result {
            warn!("Failed to update usage statistics for API key: {}", e);
        }
        
        Ok(())
    }
}