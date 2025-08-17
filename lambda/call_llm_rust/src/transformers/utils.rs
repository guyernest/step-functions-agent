use serde_json::Value;
use tracing::warn;

/// Safely extract a field from a JSON value using dot notation
pub fn safe_extract_field(value: &Value, path: &str) -> Option<Value> {
    let parts: Vec<&str> = path.split('.').collect();
    let mut current = value;
    
    for part in parts {
        if let Ok(index) = part.parse::<usize>() {
            // Array index
            current = current.get(index)?;
        } else {
            // Object field
            current = current.get(part)?;
        }
    }
    
    Some(current.clone())
}

/// Try multiple paths and return the first successful extraction
pub fn extract_with_fallback(value: &Value, paths: &[&str]) -> Option<Value> {
    for path in paths {
        if let Some(result) = safe_extract_field(value, path) {
            return Some(result);
        }
    }
    None
}

/// Extract a string field with fallback paths
pub fn extract_string(value: &Value, paths: &[&str]) -> Option<String> {
    extract_with_fallback(value, paths)?
        .as_str()
        .map(|s| s.to_string())
}

/// Extract an integer field with fallback paths
pub fn extract_u32(value: &Value, paths: &[&str], default: u32) -> u32 {
    extract_with_fallback(value, paths)
        .and_then(|v| v.as_u64())
        .map(|v| v as u32)
        .unwrap_or(default)
}

/// Generate a unique ID for tool calls
pub fn generate_tool_id() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis();
    format!("call_{}", timestamp)
}

/// Clean and validate JSON schema for tools
pub fn clean_tool_schema(schema: &Value) -> Value {
    if let Value::Object(map) = schema {
        let mut clean = serde_json::Map::new();
        
        // Always set type to object
        clean.insert("type".to_string(), Value::String("object".to_string()));
        
        // Copy properties if they exist
        if let Some(props) = map.get("properties") {
            clean.insert("properties".to_string(), props.clone());
        }
        
        // Copy required fields if they exist
        if let Some(required) = map.get("required") {
            if let Value::Array(arr) = required {
                if !arr.is_empty() {
                    clean.insert("required".to_string(), required.clone());
                }
            }
        }
        
        Value::Object(clean)
    } else {
        // Default to empty object schema
        serde_json::json!({
            "type": "object",
            "properties": {}
        })
    }
}