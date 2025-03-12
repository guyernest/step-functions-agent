//! Transform module for manipulating Lambda input events and output responses.
//!
//! This module handles the transformation of events and responses.
//! - For input events (LLM Lambda): Replace DynamoDB references with actual content
//! - For output responses (Tool Lambda): Replace large content with DynamoDB references

use chrono::Utc;
use serde_json::Value;
use std::collections::VecDeque;
use std::env;
use uuid::Uuid;

// Reference prefix
const DYNAMODB_REF_PREFIX: &str = "@content:dynamodb:table:";

// Default table name
const DEFAULT_TABLE_NAME: &str = "AgentContext";

// Default max content size before storing in DynamoDB
const DEFAULT_MAX_CONTENT_SIZE: usize = 5000;

// Default max depth for JSON processing
const DEFAULT_MAX_JSON_DEPTH: usize = 10;

/// Configuration for the transform module
struct TransformConfig {
    table_name: String,
    max_content_size: usize,
    max_json_depth: usize,
}

/// Get the transform configuration from environment variables
fn get_config() -> TransformConfig {
    // Table name from environment or default
    let table_name =
        env::var("AGENT_CONTEXT_TABLE").unwrap_or_else(|_| DEFAULT_TABLE_NAME.to_string());

    // Max content size from environment or default
    let max_content_size = env::var("MAX_CONTENT_SIZE")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(DEFAULT_MAX_CONTENT_SIZE);

    // Max JSON depth from environment or default
    let max_json_depth = env::var("MAX_JSON_DEPTH")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(DEFAULT_MAX_JSON_DEPTH);

    TransformConfig {
        table_name,
        max_content_size,
        max_json_depth,
    }
}

/// Extract record ID from a DynamoDB reference string
fn extract_record_id(reference: &str) -> Option<String> {
    if reference.starts_with(DYNAMODB_REF_PREFIX) {
        // Get the part after the prefix
        if let Some(id) = reference.strip_prefix(DYNAMODB_REF_PREFIX) {
            if !id.is_empty() {
                println!("[TRANSFORM] Extracted record ID: {}", id);
                return Some(id.to_string());
            }
        }
    }

    println!(
        "[TRANSFORM] Failed to extract record ID from: {}",
        reference
    );
    None
}

/// Transform input events coming from the Lambda Runtime API before passing to Lambda function
pub async fn transform_input_event_async(event_body: &[u8]) -> Result<Vec<u8>, String> {
    // Log a truncated version of the original event
    let event_str = String::from_utf8_lossy(event_body);
    let display_len = if event_str.len() > 500 {
        500
    } else {
        event_str.len()
    };
    println!(
        "[TRANSFORM] Original event (truncated): {}...",
        &event_str[..display_len]
    );
    println!(
        "[TRANSFORM] Original event length: {} bytes",
        event_body.len()
    );

    // Parse the event JSON
    match serde_json::from_slice::<Value>(event_body) {
        Ok(mut json_value) => {
            // Get configuration
            let config = get_config();

            // Process content references (looking for DynamoDB references to retrieve)
            process_input_json(&mut json_value, &config.table_name).await;

            // Add debug marker to indicate this event went through the proxy
            if let Value::Object(ref mut map) = json_value {
                if let Ok(debug_mode) = std::env::var("LRAP_DEBUG") {
                    if debug_mode == "true" {
                        map.insert("proxy_in".to_string(), Value::Bool(true));
                        println!("[TRANSFORM] Added 'proxy_in: true' marker to the event");
                    }
                }
            }

            // Serialize back to JSON
            let result = serde_json::to_vec(&json_value)
                .map_err(|e| format!("Failed to serialize transformed event: {}", e))?;

            println!(
                "[TRANSFORM] Transformed event length: {} bytes",
                result.len()
            );

            // Log a truncated version of the transformed event
            let transformed_str = String::from_utf8_lossy(&result);
            let display_len = if transformed_str.len() > 500 {
                500
            } else {
                transformed_str.len()
            };
            println!(
                "[TRANSFORM] Transformed event (truncated): {}...",
                &transformed_str[..display_len]
            );

            Ok(result)
        }
        Err(e) => {
            println!(
                "[TRANSFORM] Failed to parse JSON: {}, passing through original body",
                e
            );
            Ok(event_body.to_vec())
        }
    }
}

/// Transform input events (synchronous wrapper for async function)
pub fn transform_input_event(event_body: &[u8]) -> Result<Vec<u8>, String> {
    // This should be called from within a tokio runtime context already
    match tokio::runtime::Handle::try_current() {
        Ok(handle) => {
            // We're in a tokio runtime, use block_in_place to prevent blocking the runtime
            tokio::task::block_in_place(|| handle.block_on(transform_input_event_async(event_body)))
        }
        Err(e) => {
            println!("[TRANSFORM] Not running in tokio runtime: {}", e);
            Ok(event_body.to_vec())
        }
    }
}

/// Process input JSON to find and resolve DynamoDB references
async fn process_input_json(json: &mut Value, table_name: &str) {
    println!("[TRANSFORM] Processing input JSON to resolve DynamoDB references");

    // Check for special case: API Gateway-style response with body field
    if let Value::Object(ref mut map) = json {
        // Try to parse body field as JSON if it exists
        if let Some(Value::String(body_str)) = map.get("body").cloned() {
            if let Ok(mut body_json) = serde_json::from_str::<Value>(&body_str) {
                // Process the body JSON
                process_json_bfs(&mut body_json, table_name, 0, false).await;

                // Update the body field with processed content
                if let Ok(processed_body) = serde_json::to_string(&body_json) {
                    map.insert("body".to_string(), Value::String(processed_body));
                }
            }
        }

        // Process the main JSON
        process_json_bfs(json, table_name, 0, false).await;
    } else {
        println!("[TRANSFORM] Input is not a JSON object, skipping processing");
    }
}

/// Transform Lambda function responses before sending to the Lambda Runtime API
pub async fn transform_response_async(response_body: &[u8]) -> Result<Vec<u8>, String> {
    // Log a truncated version of the original response
    let response_str = String::from_utf8_lossy(response_body);
    let display_len = if response_str.len() > 500 {
        500
    } else {
        response_str.len()
    };
    println!(
        "[TRANSFORM] Original response (truncated): {}...",
        &response_str[..display_len]
    );
    println!(
        "[TRANSFORM] Original response length: {} bytes",
        response_body.len()
    );

    // Parse the response JSON
    match serde_json::from_slice::<Value>(response_body) {
        Ok(mut json_value) => {
            // Get configuration
            let config = get_config();
            println!(
                "[TRANSFORM] Using max_content_size: {}, max_json_depth: {}",
                config.max_content_size, config.max_json_depth
            );

            // Process the JSON object to store large content in DynamoDB
            process_output_json(&mut json_value, &config.table_name, config.max_content_size).await;

            // Add debug marker to indicate this response went through the proxy
            if let Value::Object(ref mut map) = json_value {
                if let Ok(debug_mode) = std::env::var("LRAP_DEBUG") {
                    if debug_mode == "true" {
                        map.insert("proxy_out".to_string(), Value::Bool(true));
                        println!("[TRANSFORM] Added 'proxy_out: true' marker to the response");
                    }
                }
            }

            // Serialize back to JSON
            let result = serde_json::to_vec(&json_value)
                .map_err(|e| format!("Failed to serialize transformed response: {}", e))?;

            println!(
                "[TRANSFORM] Transformed response length: {} bytes",
                result.len()
            );

            // Log a truncated version of the transformed response
            let transformed_str = String::from_utf8_lossy(&result);
            let display_len = if transformed_str.len() > 500 {
                500
            } else {
                transformed_str.len()
            };
            println!(
                "[TRANSFORM] Transformed response (truncated): {}...",
                &transformed_str[..display_len]
            );

            Ok(result)
        }
        Err(e) => {
            println!(
                "[TRANSFORM] Failed to parse response JSON: {}, passing through original body",
                e
            );
            Ok(response_body.to_vec())
        }
    }
}

/// Transform response (synchronous wrapper for async function)
pub fn transform_response(response_body: &[u8]) -> Result<Vec<u8>, String> {
    // This should be called from within a tokio runtime context already
    match tokio::runtime::Handle::try_current() {
        Ok(handle) => {
            // We're in a tokio runtime, use block_in_place to prevent blocking the runtime
            tokio::task::block_in_place(|| handle.block_on(transform_response_async(response_body)))
        }
        Err(e) => {
            println!("[TRANSFORM] Not running in tokio runtime: {}", e);
            Ok(response_body.to_vec())
        }
    }
}

/// Process output JSON to find large content and store it in DynamoDB
async fn process_output_json(json: &mut Value, table_name: &str, max_content_size: usize) {
    println!("[TRANSFORM] Processing output JSON to store large content");

    // Check for special case: API Gateway-style response with body field
    if let Value::Object(ref mut map) = json {
        // Try to parse body field as JSON if it exists
        if let Some(Value::String(body_str)) = map.get("body").cloned() {
            if let Ok(mut body_json) = serde_json::from_str::<Value>(&body_str) {
                // Process the body JSON
                process_json_bfs(&mut body_json, table_name, max_content_size, true).await;

                // Update the body field with processed content
                if let Ok(processed_body) = serde_json::to_string(&body_json) {
                    map.insert("body".to_string(), Value::String(processed_body));
                    println!("[TRANSFORM] Updated body field with processed content");
                }
            }
        }

        // Process the main JSON
        process_json_bfs(json, table_name, max_content_size, true).await;
    } else {
        println!("[TRANSFORM] Output is not a JSON object, skipping processing");
    }
}

/// Process a JSON value using BFS traversal to handle nested structures
/// This function handles both retrieving content from DynamoDB and storing large content
///
/// When store_large_values is true:
///   - String values larger than max_content_size will be stored in DynamoDB
///   - max_content_size is used as the threshold
///
/// When store_large_values is false:
///   - DynamoDB references will be resolved to their actual content
///   - max_content_size is ignored
async fn process_json_bfs(
    json: &mut Value,
    table_name: &str,
    max_content_size: usize,
    store_large_values: bool,
) {
    // Use a queue for BFS traversal to avoid recursion issues
    let mut node_queue = VecDeque::new();

    // Track visited nodes to avoid cycles (store memory addresses as strings)
    let mut visited = std::collections::HashSet::new();

    // Start with the root node
    node_queue.push_back((json as *mut Value, 0));

    while let Some((node_ptr, depth)) = node_queue.pop_front() {
        // Safety: We ensure the pointer is valid and we're the only ones modifying it
        let node = unsafe { &mut *node_ptr };

        // Track pointer to avoid cycles
        let ptr_str = format!("{:p}", node_ptr);
        if visited.contains(&ptr_str) {
            continue;
        }
        visited.insert(ptr_str);

        match node {
            Value::Object(map) => {
                // Process all fields in the object
                let keys: Vec<String> = map.keys().cloned().collect();

                for key in keys {
                    if let Some(value) = map.get_mut(&key) {
                        match value {
                            // Process nested objects and arrays
                            Value::Object(_) | Value::Array(_) => {
                                node_queue.push_back((value as *mut Value, depth + 1));
                            }

                            // Process string values
                            Value::String(content) => {
                                // If we're retrieving content (not storing)
                                if !store_large_values && content.starts_with(DYNAMODB_REF_PREFIX) {
                                    if let Some(record_id) = extract_record_id(content) {
                                        // Try to retrieve the content from DynamoDB
                                        match dynamodb_get_item(table_name, &record_id).await {
                                            Ok(retrieved_content) => {
                                                // Replace the reference with the actual content
                                                *value = retrieved_content;
                                                println!("[TRANSFORM] Replaced DynamoDB reference with actual content");
                                            }
                                            Err(error) => {
                                                println!("[TRANSFORM] Failed to retrieve from DynamoDB: {}", error);
                                            }
                                        }
                                    }
                                }
                                // If we're storing content and it's large enough
                                else if store_large_values && content.len() > max_content_size {
                                    // Store the content in DynamoDB
                                    match dynamodb_put_item(table_name, value).await {
                                        Ok(record_id) => {
                                            // Create the reference string
                                            let dynamo_ref =
                                                format!("{}{}", DYNAMODB_REF_PREFIX, record_id);

                                            // Replace the content with the reference
                                            *value = Value::String(dynamo_ref.clone());
                                            println!("[TRANSFORM] Replaced large content '{}' with DynamoDB reference", key);
                                        }
                                        Err(error) => {
                                            println!("[TRANSFORM] Failed to store content in DynamoDB: {}", error);
                                        }
                                    }
                                }
                            }
                            _ => {} // Other value types don't need processing
                        }
                    }
                }
            }
            Value::Array(items) => {
                // Process all items in the array
                for item in items.iter_mut() {
                    node_queue.push_back((item as *mut Value, depth + 1));
                }
            }
            _ => {} // Other value types don't need processing
        }
    }

    println!("[TRANSFORM] Completed BFS processing of JSON structure");
}

/// Retrieve an item from DynamoDB
async fn dynamodb_get_item(table_name: &str, record_id: &str) -> Result<Value, String> {
    // Create the AWS config
    let config = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .load()
        .await;

    // Create the DynamoDB client
    let client = aws_sdk_dynamodb::Client::new(&config);

    // Create the request
    let request = client.get_item().table_name(table_name).key(
        "id",
        aws_sdk_dynamodb::types::AttributeValue::S(record_id.to_string()),
    );

    // Execute the request
    match request.send().await {
        Ok(response) => {
            // Check if item exists
            if let Some(item) = response.item {
                // Extract content attribute
                if let Some(content_attr) = item.get("content") {
                    if let aws_sdk_dynamodb::types::AttributeValue::S(content_str) = content_attr {
                        // Parse the JSON content
                        match serde_json::from_str::<Value>(content_str) {
                            Ok(json_value) => {
                                println!("[TRANSFORM] Retrieved content from DynamoDB table {} with ID {}", 
                                         table_name, record_id);
                                Ok(json_value)
                            }
                            Err(_) => {
                                // If not valid JSON, return as string
                                Ok(Value::String(content_str.clone()))
                            }
                        }
                    } else {
                        Err(format!(
                            "Content is not a string in DynamoDB record {}",
                            record_id
                        ))
                    }
                } else {
                    Err(format!(
                        "Content attribute not found in DynamoDB record {}",
                        record_id
                    ))
                }
            } else {
                Err(format!(
                    "Record {} not found in DynamoDB table {}",
                    record_id, table_name
                ))
            }
        }
        Err(e) => Err(format!("Failed to retrieve from DynamoDB: {}", e)),
    }
}

/// Store an item in DynamoDB
async fn dynamodb_put_item(table_name: &str, content: &Value) -> Result<String, String> {
    // Generate a unique record ID
    let record_id = format!("record-{}", Uuid::new_v4());

    // Create the AWS config
    let config = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .load()
        .await;

    // Create the DynamoDB client
    let client = aws_sdk_dynamodb::Client::new(&config);

    // Convert content to JSON string
    let content_json = match serde_json::to_string(content) {
        Ok(json) => json,
        Err(e) => return Err(format!("Failed to serialize content to JSON: {}", e)),
    };

    let content_len = content_json.len();

    // Create the item
    let request = client
        .put_item()
        .table_name(table_name)
        .item(
            "id",
            aws_sdk_dynamodb::types::AttributeValue::S(record_id.clone()),
        )
        .item(
            "content",
            aws_sdk_dynamodb::types::AttributeValue::S(content_json),
        )
        .item(
            "timestamp",
            aws_sdk_dynamodb::types::AttributeValue::N(Utc::now().timestamp().to_string()),
        );

    // Execute the request
    match request.send().await {
        Ok(_) => {
            println!(
                "[TRANSFORM] Stored {} bytes in DynamoDB table {} with ID {}",
                content_len, table_name, record_id
            );
            Ok(record_id)
        }
        Err(e) => Err(format!("Failed to store in DynamoDB: {}", e)),
    }
}
