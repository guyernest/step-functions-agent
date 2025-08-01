use serde_json::{Map, Value};
use std::collections::VecDeque;

/// Process a JSON value recursively using a non-recursive approach with a queue
/// This function can check all string values in the JSON structure, not just "content" fields
/// It will replace any string longer than max_content_size with a reference in DynamoDB
pub async fn process_json(
    json: &mut Value,
    table_name: &str,
    max_content_size: usize,
    store_large_values: bool,
) {
    // Queue for BFS traversal to avoid recursion issues in Rust
    let mut queue = VecDeque::new();
    
    // Start with the root node
    queue.push_back(json);
    
    while let Some(current) = queue.pop_front() {
        match current {
            Value::Object(map) => {
                // Process all fields in the object
                process_object_fields(map, table_name, max_content_size, store_large_values, &mut queue).await;
            }
            Value::Array(items) => {
                // Add all array items to the queue for processing
                for item in items.iter_mut() {
                    queue.push_back(item);
                }
            }
            _ => {} // Other value types don't need processing
        }
    }
}

/// Process all fields in a JSON object
async fn process_object_fields(
    map: &mut Map<String, Value>,
    table_name: &str,
    max_content_size: usize,
    store_large_values: bool,
    queue: &mut VecDeque<&mut Value>,
) {
    // First pass: Process all nested objects and arrays
    let keys: Vec<String> = map.keys().cloned().collect();
    for key in &keys {
        if let Some(value) = map.get_mut(key) {
            match value {
                Value::Object(_) | Value::Array(_) => {
                    queue.push_back(value);
                }
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
                    // If we're storing content
                    else if store_large_values && content.len() > max_content_size {
                        // Store the content in DynamoDB
                        match dynamodb_put_item(table_name, value).await {
                            Ok(record_id) => {
                                // Create the reference string
                                let dynamo_ref = format!("{}{}", DYNAMODB_REF_PREFIX, record_id);
                                
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

// The rest of the functions (extract_record_id, dynamodb_get_item, dynamodb_put_item) 
// remain the same as in the original code