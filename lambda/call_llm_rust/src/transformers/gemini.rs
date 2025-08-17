use super::{MessageTransformer, utils};
use crate::error::ServiceError;
use crate::models::{
    AssistantMessage, ContentBlock, FunctionCall, LLMInvocation, MessageContent, TokenUsage,
    TransformedRequest, TransformedResponse, UnifiedMessage,
};
use async_trait::async_trait;
use serde_json::{json, Value};
use std::collections::HashMap;
use tracing::{debug, warn};

pub struct GeminiTransformer;

#[async_trait]
impl MessageTransformer for GeminiTransformer {
    fn transform_request(&self, invocation: &LLMInvocation) -> Result<TransformedRequest, ServiceError> {
        debug!("Transforming request to Gemini format");
        
        let mut body = json!({
            "contents": self.transform_messages(&invocation.messages)?,
            "generationConfig": {
                "temperature": invocation.temperature.unwrap_or(0.7),
                "maxOutputTokens": invocation.max_tokens.unwrap_or(4096),
                "topP": invocation.top_p.unwrap_or(1.0),
            }
        });
        
        // Add tools if present
        if let Some(tools) = &invocation.tools {
            let function_declarations: Vec<Value> = tools
                .iter()
                .map(|tool| {
                    let schema = utils::clean_tool_schema(&tool.input_schema);
                    let mut func_decl = json!({
                        "name": tool.name,
                        "description": tool.description,
                    });
                    
                    // Only add parameters if schema has properties
                    if let Some(props) = schema.get("properties") {
                        if !props.as_object().map(|o| o.is_empty()).unwrap_or(true) {
                            func_decl["parameters"] = schema;
                        }
                    }
                    
                    func_decl
                })
                .collect();
            
            if !function_declarations.is_empty() {
                body["tools"] = json!([{
                    "functionDeclarations": function_declarations
                }]);
            }
        }
        
        Ok(TransformedRequest {
            body,
            headers: HashMap::new(),
        })
    }
    
    fn transform_response(&self, response: Value) -> Result<TransformedResponse, ServiceError> {
        debug!("Transforming Gemini response to unified format");
        
        // Extract candidate
        let candidate = response.get("candidates")
            .and_then(|c| c.get(0))
            .ok_or_else(|| ServiceError::TransformError("No candidates in response".to_string()))?;
        
        // Extract content parts
        let parts = candidate.get("content")
            .and_then(|c| c.get("parts"))
            .and_then(|p| p.as_array())
            .ok_or_else(|| ServiceError::TransformError("No parts in content".to_string()))?;
        
        let mut unified_blocks = Vec::new();
        let mut function_calls = Vec::new();
        let mut function_call_parts = Vec::new();
        
        for part in parts {
            if let Some(text) = part.get("text").and_then(|t| t.as_str()) {
                unified_blocks.push(ContentBlock::Text {
                    text: text.to_string(),
                });
            } else if let Some(func_call) = part.get("functionCall") {
                let name = func_call.get("name")
                    .and_then(|n| n.as_str())
                    .unwrap_or("")
                    .to_string();
                let args = func_call.get("args")
                    .cloned()
                    .unwrap_or(json!({}));
                let id = utils::generate_tool_id();
                
                unified_blocks.push(ContentBlock::ToolUse {
                    id: id.clone(),
                    name: name.clone(),
                    input: args.clone(),
                });
                
                function_calls.push(FunctionCall {
                    id,
                    name,
                    input: args,
                });
                
                // Keep only the function call parts for tool_calls
                function_call_parts.push(part.clone());
            }
        }
        
        // Extract usage - it's at root level, not in candidate
        let usage = self.extract_usage(&response);
        
        // Extract stop reason
        let stop_reason = candidate.get("finishReason")
            .and_then(|s| s.as_str())
            .map(|s| s.to_string());
        
        Ok(TransformedResponse {
            message: AssistantMessage {
                role: "assistant".to_string(),
                content: unified_blocks,
                tool_calls: if !function_call_parts.is_empty() {
                    Some(json!(function_call_parts))
                } else {
                    None
                },
            },
            function_calls: if !function_calls.is_empty() {
                Some(function_calls)
            } else {
                None
            },
            usage,
            stop_reason,
        })
    }
}

impl GeminiTransformer {
    fn transform_messages(&self, messages: &[UnifiedMessage]) -> Result<Vec<Value>, ServiceError> {
        let mut gemini_messages = Vec::new();
        
        for message in messages {
            // Skip empty assistant messages (Gemini doesn't like them)
            if message.role == "assistant" {
                match &message.content {
                    MessageContent::Text { content } if content.is_empty() => continue,
                    MessageContent::Blocks { content } if content.is_empty() => continue,
                    _ => {}
                }
            }
            
            let parts = self.transform_message_to_parts(message)?;
            if !parts.is_empty() {
                gemini_messages.push(json!({
                    "role": if message.role == "assistant" { "model" } else { "user" },
                    "parts": parts
                }));
            }
        }
        
        Ok(gemini_messages)
    }
    
    fn transform_message_to_parts(&self, message: &UnifiedMessage) -> Result<Vec<Value>, ServiceError> {
        let mut parts = Vec::new();
        
        match &message.content {
            MessageContent::Text { content } => {
                parts.push(json!({ "text": content }));
            }
            MessageContent::Blocks { content } => {
                for block in content {
                    match block {
                        ContentBlock::Text { text } => {
                            parts.push(json!({ "text": text }));
                        }
                        ContentBlock::ToolUse { name, input, .. } => {
                            parts.push(json!({
                                "functionCall": {
                                    "name": name,
                                    "args": input
                                }
                            }));
                        }
                        ContentBlock::ToolResult { tool_use_id: _, content } => {
                            // Gemini uses function_response format
                            parts.push(json!({
                                "functionResponse": {
                                    "name": "tool_response",
                                    "response": {
                                        "result": content
                                    }
                                }
                            }));
                        }
                        ContentBlock::Image { .. } => {
                            // TODO: Implement image support for Gemini
                            warn!("Image blocks not yet implemented for Gemini");
                        }
                    }
                }
            }
        }
        
        Ok(parts)
    }
    
    fn extract_usage(&self, response: &Value) -> Option<TokenUsage> {
        // Try both camelCase and snake_case variations as Gemini API might use either
        let metadata = response.get("usageMetadata")
            .or_else(|| response.get("usage_metadata"));
        
        if metadata.is_none() {
            debug!("No usageMetadata found in Gemini response. Available keys: {:?}", 
                response.as_object().map(|o| o.keys().collect::<Vec<_>>()));
            return None;
        }
        
        let metadata = metadata?;
        
        let input_tokens = metadata.get("promptTokenCount")
            .or_else(|| metadata.get("prompt_token_count"))
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u32;
        
        let output_tokens = metadata.get("candidatesTokenCount")
            .or_else(|| metadata.get("candidates_token_count"))
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u32;
        
        // Some responses might include total_token_count
        let total_tokens = metadata.get("totalTokenCount")
            .or_else(|| metadata.get("total_token_count"))
            .and_then(|v| v.as_u64())
            .map(|v| v as u32)
            .unwrap_or(input_tokens + output_tokens);
        
        if input_tokens == 0 && output_tokens == 0 {
            warn!("Gemini token counts are zero. Metadata: {:?}", metadata);
        }
        
        Some(TokenUsage {
            input_tokens,
            output_tokens,
            total_tokens,
        })
    }
}