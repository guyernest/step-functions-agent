//! Transform module for manipulating Lambda input events and output responses.
//!
//! This module handles the transformation of events and responses.
//! - For input events (LLM Lambda): Replace DynamoDB references with actual content
//! - For output responses (Tool Lambda): Replace large content with DynamoDB references

use chrono::Utc;
use serde_json::{Map, Value};
use std::env;
use uuid::Uuid;

// Reference prefix
const DYNAMODB_REF_PREFIX: &str = "@content:dynamodb:table:";

// Default table name
const DEFAULT_TABLE_NAME: &str = "AgentContext";

// Default max content size before storing in DynamoDB (50 chars for testing)
const DEFAULT_MAX_CONTENT_SIZE: usize = 50;

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
            // Use the configured max depth for JSON processing
            process_input_json(&mut json_value, &config.table_name, config.max_json_depth).await;

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
async fn process_input_json(json: &mut Value, table_name: &str, max_depth: usize) {
    println!(
        "[TRANSFORM] Processing input JSON to resolve DynamoDB references (max depth: {})",
        max_depth
    );

    // Check for special case: API Gateway-style response with body field
    if let Value::Object(ref mut map) = json {
        // Try to parse body field as JSON if it exists
        if let Some(Value::String(body_str)) = map.get("body").cloned() {
            if let Ok(mut body_json) = serde_json::from_str::<Value>(&body_str) {
                // Process the body JSON with the configured depth
                process_input_json_by_levels(&mut body_json, table_name, max_depth).await;

                // Update the body field with processed content
                if let Ok(processed_body) = serde_json::to_string(&body_json) {
                    map.insert("body".to_string(), Value::String(processed_body));
                }
            }
        }

        // Process the main JSON with the configured depth
        process_input_json_by_levels(json, table_name, max_depth).await;
    } else {
        println!("[TRANSFORM] Input is not a JSON object, skipping processing");
    }
}

/// Process JSON without recursion by using explicit checking at each level
async fn process_input_json_by_levels(json: &mut Value, table_name: &str, max_depth: usize) {
    println!(
        "[TRANSFORM] Processing input JSON by levels (max depth: {})",
        max_depth
    );

    // Level 0 (top level)
    if let Value::Object(ref mut map) = json {
        check_content_for_reference(map, table_name).await;

        // Collect all keys to avoid borrowing issues
        let level0_keys: Vec<String> = map.keys().cloned().collect();

        // Process level 1
        for key0 in level0_keys {
            if max_depth < 1 {
                continue;
            }

            if let Some(value1) = map.get_mut(&key0) {
                match value1 {
                    Value::Object(ref mut map1) => {
                        check_content_for_reference(map1, table_name).await;

                        // Process level 2
                        let level1_keys: Vec<String> = map1.keys().cloned().collect();
                        for key1 in level1_keys {
                            if max_depth < 2 {
                                continue;
                            }

                            if let Some(value2) = map1.get_mut(&key1) {
                                match value2 {
                                    Value::Object(ref mut map2) => {
                                        check_content_for_reference(map2, table_name).await;

                                        // Process level 3
                                        let level2_keys: Vec<String> =
                                            map2.keys().cloned().collect();
                                        for key2 in level2_keys {
                                            if max_depth < 3 {
                                                continue;
                                            }

                                            if let Some(value3) = map2.get_mut(&key2) {
                                                match value3 {
                                                    Value::Object(ref mut map3) => {
                                                        check_content_for_reference(
                                                            map3, table_name,
                                                        )
                                                        .await;

                                                        // Process level 4
                                                        let level3_keys: Vec<String> =
                                                            map3.keys().cloned().collect();
                                                        for key3 in level3_keys {
                                                            if max_depth < 4 {
                                                                continue;
                                                            }

                                                            if let Some(value4) =
                                                                map3.get_mut(&key3)
                                                            {
                                                                match value4 {
                                                                    Value::Object(ref mut map4) => {
                                                                        check_content_for_reference(map4, table_name).await;

                                                                        // Process level 5
                                                                        let level4_keys: Vec<
                                                                            String,
                                                                        > = map4
                                                                            .keys()
                                                                            .cloned()
                                                                            .collect();
                                                                        for key4 in level4_keys {
                                                                            if max_depth < 5 {
                                                                                continue;
                                                                            }

                                                                            if let Some(value5) =
                                                                                map4.get_mut(&key4)
                                                                            {
                                                                                match value5 {
                                                                                    Value::Object(ref mut map5) => {
                                                                                        check_content_for_reference(map5, table_name).await;
                                                                                        // We stop at level 5 explicitly
                                                                                    },
                                                                                    Value::Array(ref mut items5) => {
                                                                                        for item5 in items5.iter_mut() {
                                                                                            if let Value::Object(ref mut item_map5) = item5 {
                                                                                                check_content_for_reference(item_map5, table_name).await;
                                                                                            }
                                                                                        }
                                                                                    },
                                                                                    _ => {}
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                    Value::Array(
                                                                        ref mut items4,
                                                                    ) => {
                                                                        for item4 in
                                                                            items4.iter_mut()
                                                                        {
                                                                            if let Value::Object(
                                                                                ref mut item_map4,
                                                                            ) = item4
                                                                            {
                                                                                check_content_for_reference(item_map4, table_name).await;
                                                                            }
                                                                        }
                                                                    }
                                                                    _ => {}
                                                                }
                                                            }
                                                        }
                                                    }
                                                    Value::Array(ref mut items3) => {
                                                        for item3 in items3.iter_mut() {
                                                            if let Value::Object(
                                                                ref mut item_map3,
                                                            ) = item3
                                                            {
                                                                check_content_for_reference(
                                                                    item_map3, table_name,
                                                                )
                                                                .await;
                                                            }
                                                        }
                                                    }
                                                    _ => {}
                                                }
                                            }
                                        }
                                    }
                                    Value::Array(ref mut items2) => {
                                        for item2 in items2.iter_mut() {
                                            if let Value::Object(ref mut item_map2) = item2 {
                                                check_content_for_reference(item_map2, table_name)
                                                    .await;
                                            }
                                        }
                                    }
                                    _ => {}
                                }
                            }
                        }
                    }
                    Value::Array(ref mut items1) => {
                        for item1 in items1.iter_mut() {
                            if let Value::Object(ref mut item_map1) = item1 {
                                check_content_for_reference(item_map1, table_name).await;

                                // Process level 2 inside arrays
                                if max_depth < 2 {
                                    continue;
                                }

                                let item1_keys: Vec<String> = item_map1.keys().cloned().collect();
                                for item1_key in item1_keys {
                                    if let Some(item1_value) = item_map1.get_mut(&item1_key) {
                                        match item1_value {
                                            Value::Object(ref mut inner_map) => {
                                                check_content_for_reference(inner_map, table_name)
                                                    .await;
                                            }
                                            Value::Array(ref mut inner_items) => {
                                                for inner_item in inner_items.iter_mut() {
                                                    if let Value::Object(ref mut inner_item_map) =
                                                        inner_item
                                                    {
                                                        check_content_for_reference(
                                                            inner_item_map,
                                                            table_name,
                                                        )
                                                        .await;
                                                    }
                                                }
                                            }
                                            _ => {}
                                        }
                                    }
                                }
                            }
                        }
                    }
                    _ => {}
                }
            }
        }
    } else if let Value::Array(ref mut items) = json {
        // Top level is an array - process each item
        for item in items.iter_mut() {
            if let Value::Object(ref mut item_map) = item {
                check_content_for_reference(item_map, table_name).await;

                // Continue processing for remaining levels if needed
                if max_depth >= 1 {
                    let item_keys: Vec<String> = item_map.keys().cloned().collect();
                    for item_key in item_keys {
                        if let Some(Value::Object(ref mut inner_map)) = item_map.get_mut(&item_key)
                        {
                            check_content_for_reference(inner_map, table_name).await;
                        }
                    }
                }
            }
        }
    }

    println!(
        "[TRANSFORM] Completed processing up to {} levels deep",
        max_depth
    );
}

/// Check if a JSON object has a "content" field with a DynamoDB reference and resolve it
async fn check_content_for_reference(map: &mut Map<String, Value>, table_name: &str) {
    if let Some(Value::String(content_str)) = map.get("content") {
        if content_str.starts_with(DYNAMODB_REF_PREFIX) {
            println!("[TRANSFORM] Found DynamoDB reference: {}", content_str);

            if let Some(record_id) = extract_record_id(content_str) {
                // Try to retrieve the content from DynamoDB
                match dynamodb_get_item(table_name, &record_id).await {
                    Ok(content) => {
                        // Replace the reference with the actual content
                        map.insert("content".to_string(), content);
                        println!("[TRANSFORM] Replaced DynamoDB reference with actual content");
                    }
                    Err(error) => {
                        println!("[TRANSFORM] Failed to retrieve from DynamoDB: {}", error);
                        // Keep the reference, but mark as error
                        map.insert(
                            "content".to_string(),
                            Value::String(format!("{} (ERROR: {})", content_str, error)),
                        );
                    }
                }
            }
        }
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

            // Process the JSON object to store large content in DynamoDB with the configured depth
            process_output_json(
                &mut json_value,
                &config.table_name,
                config.max_content_size,
                config.max_json_depth,
            )
            .await;

            // Add debug marker to indicate this response went through the proxy
            if let Value::Object(ref mut map) = json_value {
                map.insert("proxy_out".to_string(), Value::Bool(true));
                println!("[TRANSFORM] Added 'proxy_out: true' marker to the response");
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
async fn process_output_json(
    json: &mut Value,
    table_name: &str,
    max_content_size: usize,
    max_depth: usize,
) {
    println!(
        "[TRANSFORM] Processing output JSON to store large content (max depth: {})",
        max_depth
    );

    // Check for special case: API Gateway-style response with body field
    if let Value::Object(ref mut map) = json {
        // Try to parse body field as JSON if it exists
        if let Some(Value::String(body_str)) = map.get("body").cloned() {
            if let Ok(mut body_json) = serde_json::from_str::<Value>(&body_str) {
                // Process the body JSON with configured depth
                process_output_json_by_levels(
                    &mut body_json,
                    table_name,
                    max_content_size,
                    max_depth,
                )
                .await;

                // Update the body field with processed content
                if let Ok(processed_body) = serde_json::to_string(&body_json) {
                    map.insert("body".to_string(), Value::String(processed_body));
                    println!("[TRANSFORM] Updated body field with processed content");
                }
            }
        }

        // Process the main JSON with configured depth
        process_output_json_by_levels(json, table_name, max_content_size, max_depth).await;
    } else {
        println!("[TRANSFORM] Output is not a JSON object, skipping processing");
    }
}

/// Process output JSON by levels to find large content
async fn process_output_json_by_levels(
    json: &mut Value,
    table_name: &str,
    max_content_size: usize,
    max_depth: usize,
) {
    println!(
        "[TRANSFORM] Processing output JSON by levels (max depth: {})",
        max_depth
    );

    // Level 0 (top level)
    if let Value::Object(ref mut map) = json {
        check_content_size(map, table_name, max_content_size).await;

        // Collect all keys to avoid borrowing issues
        let level0_keys: Vec<String> = map.keys().cloned().collect();

        // Process level 1
        for key0 in level0_keys {
            if max_depth < 1 {
                continue;
            }

            if let Some(value1) = map.get_mut(&key0) {
                match value1 {
                    Value::Object(ref mut map1) => {
                        check_content_size(map1, table_name, max_content_size).await;

                        // Process level 2
                        let level1_keys: Vec<String> = map1.keys().cloned().collect();
                        for key1 in level1_keys {
                            if max_depth < 2 {
                                continue;
                            }

                            if let Some(value2) = map1.get_mut(&key1) {
                                match value2 {
                                    Value::Object(ref mut map2) => {
                                        check_content_size(map2, table_name, max_content_size)
                                            .await;

                                        // Process level 3
                                        let level2_keys: Vec<String> =
                                            map2.keys().cloned().collect();
                                        for key2 in level2_keys {
                                            if max_depth < 3 {
                                                continue;
                                            }

                                            if let Some(value3) = map2.get_mut(&key2) {
                                                match value3 {
                                                    Value::Object(ref mut map3) => {
                                                        check_content_size(
                                                            map3,
                                                            table_name,
                                                            max_content_size,
                                                        )
                                                        .await;

                                                        // Process level 4
                                                        let level3_keys: Vec<String> =
                                                            map3.keys().cloned().collect();
                                                        for key3 in level3_keys {
                                                            if max_depth < 4 {
                                                                continue;
                                                            }

                                                            if let Some(value4) =
                                                                map3.get_mut(&key3)
                                                            {
                                                                match value4 {
                                                                    Value::Object(ref mut map4) => {
                                                                        check_content_size(
                                                                            map4,
                                                                            table_name,
                                                                            max_content_size,
                                                                        )
                                                                        .await;

                                                                        // Process level 5
                                                                        let level4_keys: Vec<
                                                                            String,
                                                                        > = map4
                                                                            .keys()
                                                                            .cloned()
                                                                            .collect();
                                                                        for key4 in level4_keys {
                                                                            if max_depth < 5 {
                                                                                continue;
                                                                            }

                                                                            if let Some(value5) =
                                                                                map4.get_mut(&key4)
                                                                            {
                                                                                match value5 {
                                                                                    Value::Object(ref mut map5) => {
                                                                                        check_content_size(map5, table_name, max_content_size).await;
                                                                                        // We stop at level 5 explicitly
                                                                                    },
                                                                                    Value::Array(ref mut items5) => {
                                                                                        for item5 in items5.iter_mut() {
                                                                                            if let Value::Object(ref mut item_map5) = item5 {
                                                                                                check_content_size(item_map5, table_name, max_content_size).await;
                                                                                            }
                                                                                        }
                                                                                    },
                                                                                    _ => {}
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                    Value::Array(
                                                                        ref mut items4,
                                                                    ) => {
                                                                        for item4 in
                                                                            items4.iter_mut()
                                                                        {
                                                                            if let Value::Object(
                                                                                ref mut item_map4,
                                                                            ) = item4
                                                                            {
                                                                                check_content_size(item_map4, table_name, max_content_size).await;
                                                                            }
                                                                        }
                                                                    }
                                                                    _ => {}
                                                                }
                                                            }
                                                        }
                                                    }
                                                    Value::Array(ref mut items3) => {
                                                        for item3 in items3.iter_mut() {
                                                            if let Value::Object(
                                                                ref mut item_map3,
                                                            ) = item3
                                                            {
                                                                check_content_size(
                                                                    item_map3,
                                                                    table_name,
                                                                    max_content_size,
                                                                )
                                                                .await;
                                                            }
                                                        }
                                                    }
                                                    _ => {}
                                                }
                                            }
                                        }
                                    }
                                    Value::Array(ref mut items2) => {
                                        for item2 in items2.iter_mut() {
                                            if let Value::Object(ref mut item_map2) = item2 {
                                                check_content_size(
                                                    item_map2,
                                                    table_name,
                                                    max_content_size,
                                                )
                                                .await;
                                            }
                                        }
                                    }
                                    _ => {}
                                }
                            }
                        }
                    }
                    Value::Array(ref mut items1) => {
                        for item1 in items1.iter_mut() {
                            if let Value::Object(ref mut item_map1) = item1 {
                                check_content_size(item_map1, table_name, max_content_size).await;

                                // Process level 2 inside arrays
                                if max_depth < 2 {
                                    continue;
                                }

                                let item1_keys: Vec<String> = item_map1.keys().cloned().collect();
                                for item1_key in item1_keys {
                                    if let Some(item1_value) = item_map1.get_mut(&item1_key) {
                                        match item1_value {
                                            Value::Object(ref mut inner_map) => {
                                                check_content_size(
                                                    inner_map,
                                                    table_name,
                                                    max_content_size,
                                                )
                                                .await;
                                            }
                                            Value::Array(ref mut inner_items) => {
                                                for inner_item in inner_items.iter_mut() {
                                                    if let Value::Object(ref mut inner_item_map) =
                                                        inner_item
                                                    {
                                                        check_content_size(
                                                            inner_item_map,
                                                            table_name,
                                                            max_content_size,
                                                        )
                                                        .await;
                                                    }
                                                }
                                            }
                                            _ => {}
                                        }
                                    }
                                }
                            }
                        }
                    }
                    _ => {}
                }
            }
        }
    } else if let Value::Array(ref mut items) = json {
        // Top level is an array - process each item
        for item in items.iter_mut() {
            if let Value::Object(ref mut item_map) = item {
                check_content_size(item_map, table_name, max_content_size).await;

                // Continue processing for remaining levels if needed
                if max_depth >= 1 {
                    let item_keys: Vec<String> = item_map.keys().cloned().collect();
                    for item_key in item_keys {
                        if let Some(Value::Object(ref mut inner_map)) = item_map.get_mut(&item_key)
                        {
                            check_content_for_reference(inner_map, table_name).await;
                        }
                    }
                }
            }
        }
    }

    println!(
        "[TRANSFORM] Completed processing output for content size up to {} levels deep",
        max_depth
    );
}

/// Check if a JSON object has a "content" field that exceeds the size threshold and store it in DynamoDB
async fn check_content_size(
    map: &mut Map<String, Value>,
    table_name: &str,
    max_content_size: usize,
) {
    if let Some(Value::String(content_str)) = map.get("content") {
        let content_len = content_str.len();
        println!("[TRANSFORM] Found content field of size: {}", content_len);

        if content_len > max_content_size {
            println!("[TRANSFORM] Content exceeds size threshold, storing in DynamoDB");

            // Get a clone of the value to store in DynamoDB
            let content_value = map.get("content").unwrap().clone();

            // Store the content in DynamoDB
            match dynamodb_put_item(table_name, &content_value).await {
                Ok(record_id) => {
                    // Create the reference string
                    let dynamo_ref = format!("{}{}", DYNAMODB_REF_PREFIX, record_id);

                    // Replace the content with the reference
                    map.insert("content".to_string(), Value::String(dynamo_ref.clone()));
                    println!(
                        "[TRANSFORM] Replaced large content with DynamoDB reference: {}",
                        dynamo_ref
                    );
                }
                Err(error) => {
                    println!("[TRANSFORM] Failed to store content in DynamoDB: {}", error);
                    // Keep the original content if we can't store it
                }
            }
        } else {
            println!("[TRANSFORM] Content size is below threshold, not storing");
        }
    }
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
