use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

// ===== Request Models =====

#[derive(Debug, Clone, Deserialize)]
pub struct LLMInvocation {
    pub provider_config: ProviderConfig,
    pub messages: Vec<UnifiedMessage>,
    #[serde(default)]
    pub tools: Option<Vec<UnifiedTool>>,
    #[serde(default)]
    pub temperature: Option<f32>,
    #[serde(default)]
    pub max_tokens: Option<i32>,
    #[serde(default)]
    pub top_p: Option<f32>,
    #[serde(default)]
    pub stream: Option<bool>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ProviderConfig {
    pub provider_id: String,
    pub model_id: String,
    pub endpoint: String,
    pub auth_header_name: String,
    #[serde(default)]
    pub auth_header_prefix: Option<String>,
    pub secret_path: String,
    pub secret_key_name: String,
    pub request_transformer: String,
    pub response_transformer: String,
    #[serde(default = "default_timeout")]
    pub timeout: u64,
    #[serde(default)]
    pub custom_headers: Option<HashMap<String, String>>,
}

fn default_timeout() -> u64 {
    30
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnifiedMessage {
    pub role: String,
    #[serde(flatten)]
    pub content: MessageContent,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum MessageContent {
    Text {
        content: String,
    },
    Blocks {
        content: Vec<ContentBlock>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ContentBlock {
    #[serde(rename = "text")]
    Text { text: String },
    
    #[serde(rename = "tool_use")]
    ToolUse {
        id: String,
        name: String,
        input: Value,
    },
    
    #[serde(rename = "tool_result")]
    ToolResult {
        tool_use_id: String,
        content: String,
    },
    
    #[serde(rename = "image")]
    Image {
        source: ImageSource,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageSource {
    #[serde(rename = "type")]
    pub source_type: String,
    pub media_type: String,
    pub data: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnifiedTool {
    pub name: String,
    pub description: String,
    pub input_schema: Value,
}

// ===== Response Models =====

#[derive(Debug, Clone, Serialize)]
pub struct LLMResponse {
    pub message: AssistantMessage,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub function_calls: Option<Vec<FunctionCall>>,
    pub metadata: ResponseMetadata,
}

#[derive(Debug, Clone, Serialize)]
pub struct AssistantMessage {
    pub role: String,
    pub content: Vec<ContentBlock>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_calls: Option<Value>, // Provider-specific format
}

#[derive(Debug, Clone, Serialize)]
pub struct FunctionCall {
    pub id: String,
    pub name: String,
    pub input: Value,
}

#[derive(Debug, Clone, Serialize)]
pub struct ResponseMetadata {
    pub model_id: String,
    pub provider_id: String,
    pub latency_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tokens_used: Option<TokenUsage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stop_reason: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct TokenUsage {
    pub input_tokens: u32,
    pub output_tokens: u32,
    pub total_tokens: u32,
}

// ===== Internal Models =====

#[derive(Debug, Clone)]
pub struct TransformedRequest {
    pub body: Value,
    pub headers: HashMap<String, String>,
}

#[derive(Debug, Clone)]
pub struct TransformedResponse {
    pub message: AssistantMessage,
    pub function_calls: Option<Vec<FunctionCall>>,
    pub usage: Option<TokenUsage>,
    pub stop_reason: Option<String>,
}