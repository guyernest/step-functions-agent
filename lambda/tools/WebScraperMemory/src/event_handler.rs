use anyhow::{anyhow, Context as AnyhowContext, Result};
use aws_sdk_dynamodb::{types::AttributeValue, Client};
use lambda_runtime::{tracing, Error, LambdaEvent};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use url::Url;

#[derive(Deserialize, Debug)]
pub struct ToolUsePayload {
    pub id: String,
    pub name: String,
    pub input: Value,
}

impl Default for ToolUsePayload {
    fn default() -> Self {
        ToolUsePayload {
            id: String::from(""),
            name: String::from(""),
            input: Value::Null,
        }
    }
}

#[derive(Serialize, Debug)]
pub struct ToolUseResponse {
    pub tool_use_id: String,
    pub name: String,
    #[serde(rename = "type")]
    pub response_type: String,
    pub content: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SiteSchema {
    site_url: String,
    info_types: HashSet<String>,
    site_metadata: Option<Value>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ExtractionScript {
    site_url: String,
    info_type: String,
    script: Value,
}

// Helper function to normalize URLs for consistent storage
fn normalize_url(url_str: &str) -> Result<String> {
    // Ensure URL has a scheme, add https:// if missing
    let url_with_scheme = if !url_str.contains("://") {
        format!("https://{}", url_str)
    } else {
        url_str.to_string()
    };
    
    let url = Url::parse(&url_with_scheme)
        .map_err(|e| anyhow!("Invalid URL: {}", e))?;
    
    // Get hostname without www. prefix
    let mut hostname = url.host_str()
        .ok_or_else(|| anyhow!("URL has no hostname"))?
        .to_string();
    
    if hostname.starts_with("www.") {
        hostname = hostname[4..].to_string();
    }
    
    Ok(hostname)
}

#[cfg(test)]
mod normalize_url_tests {
    use super::*;

    #[test]
    fn test_normalize_url_with_www() {
        let result = normalize_url("https://www.example.com").unwrap();
        assert_eq!(result, "example.com");
    }

    #[test]
    fn test_normalize_url_without_www() {
        let result = normalize_url("https://example.com").unwrap();
        assert_eq!(result, "example.com");
    }
    
    #[test]
    fn test_normalize_url_with_path_and_query() {
        let result = normalize_url("https://example.com/path/to/resource?query=value").unwrap();
        assert_eq!(result, "example.com");
    }
    
    #[test]
    fn test_normalize_url_with_subdomain() {
        let result = normalize_url("https://subdomain.example.com").unwrap();
        assert_eq!(result, "subdomain.example.com");
    }
    
    #[test]
    fn test_normalize_url_with_port() {
        let result = normalize_url("https://example.com:8080").unwrap();
        assert_eq!(result, "example.com");
    }
    
    #[test]
    fn test_normalize_url_without_scheme() {
        let result = normalize_url("example.com").unwrap();
        assert_eq!(result, "example.com");
    }
    
    #[test]
    fn test_normalize_url_weather_gov() {
        let result = normalize_url("https://www.weather.gov").unwrap();
        assert_eq!(result, "weather.gov");
    }
}

async fn get_dynamodb_client() -> Result<Client> {
    // Initialize AWS SDK
    let aws_config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
    let client = Client::new(&aws_config);

    Ok(client)
}

// Common error handling function for creating error responses
fn handle_error<T: ToString>(error: T) -> Result<String, Error> {
    let error_msg = error.to_string();
    tracing::error!("{}", error_msg);
    Ok(serde_json::to_string(&json!({
        "error": error_msg,
    }))?)
}

// Extract required string parameter from input JSON
fn extract_string_param<'a>(input: &'a Value, param_name: &str) -> Result<&'a str, String> {
    match input.get(param_name) {
        Some(value) if value.is_string() => Ok(value.as_str().unwrap()),
        _ => Err(format!("{} is required", param_name)),
    }
}

// Get the table names from environment variables
fn get_schemas_table_name() -> String {
    std::env::var("SCHEMAS_TABLE_NAME").unwrap_or_else(|_| "WebScraperSchemas".to_string())
}

fn get_scripts_table_name() -> String {
    std::env::var("SCRIPTS_TABLE_NAME").unwrap_or_else(|_| "WebScraperScripts".to_string())
}

// Get site schema implementation
async fn get_site_schema_fn(client: &Client, url: &str) -> Result<SiteSchema> {
    let table_name = get_schemas_table_name();
    let normalized_url = normalize_url(url)?;

    tracing::info!("Getting schema for site URL: {}", normalized_url);

    let response = client
        .get_item()
        .table_name(table_name)
        .key("site_url", AttributeValue::S(normalized_url.clone()))
        .send()
        .await
        .context("Failed to get schema from DynamoDB")?;

    if let Some(item) = response.item {
        // Extract info_types
        let info_types = if let Some(AttributeValue::Ss(types)) = item.get("info_types") {
            types.iter().cloned().collect()
        } else {
            HashSet::new()
        };

        // Extract site_metadata if it exists
        let site_metadata =
            if let Some(AttributeValue::S(metadata_json)) = item.get("site_metadata") {
                match serde_json::from_str(metadata_json) {
                    Ok(parsed) => Some(parsed),
                    Err(e) => {
                        tracing::warn!("Failed to parse site_metadata JSON: {}", e);
                        None
                    }
                }
            } else {
                None
            };

        let schema = SiteSchema {
            site_url: normalized_url,
            info_types,
            site_metadata,
        };

        tracing::info!("Found schema with {} info types", schema.info_types.len());
        return Ok(schema);
    }

    // Return empty schema if not found
    tracing::info!("No schema found, returning empty schema");
    Ok(SiteSchema {
        site_url: normalized_url,
        info_types: HashSet::new(),
        site_metadata: None,
    })
}

// Get extraction script implementation
async fn get_extraction_script_fn(
    client: &Client,
    url: &str,
    info_type: &str,
) -> Result<Option<ExtractionScript>> {
    let table_name = get_scripts_table_name();
    let normalized_url = normalize_url(url)?;

    tracing::info!(
        "Getting extraction script for site URL: {} and info_type: {}",
        normalized_url,
        info_type
    );

    let response = client
        .get_item()
        .table_name(table_name)
        .key("site_url", AttributeValue::S(normalized_url.clone()))
        .key("info_type", AttributeValue::S(info_type.to_string()))
        .send()
        .await
        .context("Failed to get extraction script from DynamoDB")?;

    if let Some(item) = response.item {
        if let Some(AttributeValue::S(script_json)) = item.get("script") {
            let script: Value =
                serde_json::from_str(script_json).context("Failed to parse script JSON")?;

            let extraction_script = ExtractionScript {
                site_url: normalized_url.clone(),
                info_type: info_type.to_string(),
                script,
            };

            tracing::info!(
                "Found extraction script for {}/{}",
                normalized_url,
                info_type
            );
            return Ok(Some(extraction_script));
        }
    }

    tracing::info!(
        "No extraction script found for {}/{}",
        normalized_url,
        info_type
    );
    Ok(None)
}

// Save site schema implementation
async fn save_site_schema_fn(
    client: &Client,
    url: &str,
    info_types: HashSet<String>,
    site_metadata: Option<Value>,
) -> Result<SiteSchema> {
    let table_name = get_schemas_table_name();
    let normalized_url = normalize_url(url)?;

    tracing::info!(
        "Saving schema for site URL: {} with {} info types",
        normalized_url,
        info_types.len()
    );

    // Prepare the item
    let mut item = HashMap::new();
    item.insert(
        "site_url".to_string(),
        AttributeValue::S(normalized_url.clone()),
    );

    // Convert HashSet to Vec for storage
    let info_types_vec: Vec<String> = info_types.iter().cloned().collect();
    item.insert("info_types".to_string(), AttributeValue::Ss(info_types_vec));

    // Add site_metadata if present
    if let Some(metadata) = &site_metadata {
        item.insert(
            "site_metadata".to_string(),
            AttributeValue::S(metadata.to_string()),
        );
    }

    // Save to DynamoDB
    client
        .put_item()
        .table_name(table_name)
        .set_item(Some(item))
        .send()
        .await
        .context("Failed to save site schema to DynamoDB")?;

    // Return the saved schema
    let schema = SiteSchema {
        site_url: normalized_url,
        info_types,
        site_metadata,
    };

    tracing::info!("Successfully saved schema");
    Ok(schema)
}

// Save extraction script implementation
async fn save_extraction_script_fn(
    client: &Client,
    url: &str,
    info_type: &str,
    script: Value,
) -> Result<ExtractionScript> {
    let scripts_table = get_scripts_table_name();
    let normalized_url = normalize_url(url)?;

    tracing::info!(
        "Saving extraction script for site URL: {} and info_type: {}",
        normalized_url,
        info_type
    );

    // Store the script
    client
        .put_item()
        .table_name(scripts_table)
        .item("site_url", AttributeValue::S(normalized_url.clone()))
        .item("info_type", AttributeValue::S(info_type.to_string()))
        .item("script", AttributeValue::S(script.to_string()))
        .send()
        .await
        .context("Failed to store script in DynamoDB")?;

    // Get current schema to update with the new info_type
    let mut schema = get_site_schema_fn(client, &normalized_url).await?;
    schema.info_types.insert(info_type.to_string());

    // Save the updated schema
    save_site_schema_fn(
        client,
        &normalized_url,
        schema.info_types,
        schema.site_metadata,
    )
    .await?;

    // Return the saved extraction script
    let extraction_script = ExtractionScript {
        site_url: normalized_url,
        info_type: info_type.to_string(),
        script,
    };

    tracing::info!("Successfully saved extraction script");
    Ok(extraction_script)
}

// Handle the get_site_schema API call
async fn handle_get_site_schema(payload: &ToolUsePayload) -> Result<String, Error> {
    // Extract URL from input
    let url = match extract_string_param(&payload.input, "url") {
        Ok(url) => url,
        Err(e) => return handle_error(e),
    };

    // Get DynamoDB client
    let client = match get_dynamodb_client().await {
        Ok(c) => c,
        Err(e) => return handle_error(format!("Failed to initialize DynamoDB client: {}", e)),
    };

    // Get site schema
    match get_site_schema_fn(&client, url).await {
        Ok(schema) => Ok(serde_json::to_string(&json!({
            "site_url": schema.site_url,
            "info_types": schema.info_types,
            "site_metadata": schema.site_metadata,
        }))?),
        Err(e) => handle_error(format!("Error getting site schema: {}", e)),
    }
}

// Handle the get_extraction_script API call
async fn handle_get_extraction_script(payload: &ToolUsePayload) -> Result<String, Error> {
    // Extract URL and info_type from input
    let url = match extract_string_param(&payload.input, "url") {
        Ok(url) => url,
        Err(e) => return handle_error(e),
    };

    let info_type = match extract_string_param(&payload.input, "info_type") {
        Ok(info_type) => info_type,
        Err(e) => return handle_error(e),
    };

    // Get DynamoDB client
    let client = match get_dynamodb_client().await {
        Ok(c) => c,
        Err(e) => return handle_error(format!("Failed to initialize DynamoDB client: {}", e)),
    };

    // Get extraction script
    match get_extraction_script_fn(&client, url, info_type).await {
        Ok(Some(script)) => Ok(serde_json::to_string(&json!({
            "site_url": script.site_url,
            "info_type": script.info_type,
            "script": script.script,
        }))?),
        Ok(None) => {
            let normalized_url = match normalize_url(url) {
                Ok(url) => url,
                Err(e) => return handle_error(e),
            };

            Ok(serde_json::to_string(&json!({
                "site_url": normalized_url,
                "info_type": info_type,
                "message": "No extraction script found for this site and info_type",
                "script": null
            }))?)
        }
        Err(e) => handle_error(format!("Error getting extraction script: {}", e)),
    }
}

// Handle the save_site_schema API call
async fn handle_save_site_schema(payload: &ToolUsePayload) -> Result<String, Error> {
    // Extract URL, info_types, and site_metadata from input
    let url = match extract_string_param(&payload.input, "url") {
        Ok(url) => url,
        Err(e) => return handle_error(e),
    };

    // info_types as array of strings
    let info_types = match payload.input.get("info_types") {
        Some(types_value) if types_value.is_array() => {
            let mut types_set = HashSet::new();
            for item in types_value.as_array().unwrap() {
                if let Some(s) = item.as_str() {
                    types_set.insert(s.to_string());
                }
            }
            types_set
        }
        _ => HashSet::new(),
    };

    // site_metadata as JSON object (optional)
    let site_metadata = payload.input.get("site_metadata").cloned();

    // Get DynamoDB client
    let client = match get_dynamodb_client().await {
        Ok(c) => c,
        Err(e) => return handle_error(format!("Failed to initialize DynamoDB client: {}", e)),
    };

    // Save site schema
    match save_site_schema_fn(&client, url, info_types, site_metadata).await {
        Ok(schema) => Ok(serde_json::to_string(&json!({
            "site_url": schema.site_url,
            "info_types": schema.info_types,
            "site_metadata": schema.site_metadata,
            "message": "Site schema saved successfully",
        }))?),
        Err(e) => handle_error(format!("Error saving site schema: {}", e)),
    }
}

// Handle the save_extraction_script API call
async fn handle_save_extraction_script(payload: &ToolUsePayload) -> Result<String, Error> {
    // Extract URL, info_type, and script from input
    let url = match extract_string_param(&payload.input, "url") {
        Ok(url) => url,
        Err(e) => return handle_error(e),
    };

    let info_type = match extract_string_param(&payload.input, "info_type") {
        Ok(info_type) => info_type,
        Err(e) => return handle_error(e),
    };

    let script = match payload.input.get("script") {
        Some(script_value) => script_value.clone(),
        _ => return handle_error("script is required for save_extraction_script"),
    };

    // Get DynamoDB client
    let client = match get_dynamodb_client().await {
        Ok(c) => c,
        Err(e) => return handle_error(format!("Failed to initialize DynamoDB client: {}", e)),
    };

    // Save extraction script
    match save_extraction_script_fn(&client, url, info_type, script).await {
        Ok(script) => Ok(serde_json::to_string(&json!({
            "site_url": script.site_url,
            "info_type": script.info_type,
            "message": "Extraction script saved successfully",
        }))?),
        Err(e) => handle_error(format!("Error saving extraction script: {}", e)),
    }
}

pub(crate) async fn function_handler(event: LambdaEvent<Value>) -> Result<ToolUseResponse, Error> {
    let payload: ToolUsePayload = match serde_json::from_value(event.payload.clone()) {
        Ok(payload) => payload,
        Err(e) => {
            tracing::error!("Failed to parse payload: {}", e);
            return Err(Box::new(e));
        }
    };
    tracing::info!("Received payload for tool: {}", payload.name);

    let result = match payload.name.as_str() {
        "get_site_schema" => {
            tracing::info!("Getting site schema");
            handle_get_site_schema(&payload).await?
        }
        "get_extraction_script" => {
            tracing::info!("Getting extraction script");
            handle_get_extraction_script(&payload).await?
        }
        "save_site_schema" => {
            tracing::info!("Saving site schema");
            handle_save_site_schema(&payload).await?
        }
        "save_extraction_script" => {
            tracing::info!("Saving extraction script");
            handle_save_extraction_script(&payload).await?
        }
        _ => {
            tracing::error!("Unknown tool_name: {}", payload.name);
            serde_json::to_string(&json!({
                "error": format!("Unknown tool_name: {}", payload.name),
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

#[cfg(test)]
mod tests {
    use super::*;
    use lambda_runtime::{Context, LambdaEvent};
    use serde_json::json;

    #[tokio::test]
    async fn test_get_site_schema() {
        let payload = json!({
            "id": "tool_use_unique_id",
            "name": "get_site_schema",
            "input": {
                "url": "https://example.com"
            }
        });
        let event = LambdaEvent::new(payload, Context::default());
        let response = function_handler(event).await.unwrap();

        println!("Response: {:?}", serde_json::to_string(&response).unwrap());
        assert_eq!(response.tool_use_id, "tool_use_unique_id".to_string());
        assert_eq!(response.response_type, "tool_result".to_string());
        assert!(!response.content.is_empty());
    }

    #[tokio::test]
    async fn test_get_extraction_script() {
        let payload = json!({
            "id": "tool_use_unique_id",
            "name": "get_extraction_script",
            "input": {
                "url": "https://example.com",
                "info_type": "product_ingredients"
            }
        });
        let event = LambdaEvent::new(payload, Context::default());
        let response = function_handler(event).await.unwrap();

        println!("Response: {:?}", serde_json::to_string(&response).unwrap());
        assert_eq!(response.name, "get_extraction_script".to_string());
    }

    #[tokio::test]
    async fn test_normalize_url() {
        assert_eq!(
            normalize_url("https://www.example.com").unwrap(),
            "example.com"
        );
        assert_eq!(
            normalize_url("http://example.com/page?q=test").unwrap(),
            "example.com"
        );
        assert_eq!(
            normalize_url("https://subdomain.example.com").unwrap(),
            "subdomain.example.com"
        );
    }
}
