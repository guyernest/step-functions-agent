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

pub struct AnthropicTransformer;

#[async_trait]
impl MessageTransformer for AnthropicTransformer {
    fn transform_request(&self, invocation: &LLMInvocation) -> Result<TransformedRequest, ServiceError> {
        debug!("Transforming request to Anthropic format");
        
        // Transform messages
        let messages = self.transform_messages(&invocation.messages)?;
        
        // Extract system prompt if present
        let system = self.extract_system_prompt(&invocation.messages);
        
        let mut body = json!({
            "model": invocation.provider_config.model_id,
            "messages": messages,
            "max_tokens": invocation.max_tokens.unwrap_or(4096),
        });
        
        // Add system prompt if present
        if let Some(system_text) = system {
            body["system"] = json!([{
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"}
            }]);
        }
        
        // Add optional parameters
        if let Some(temp) = invocation.temperature {
            body["temperature"] = json!(temp);
        }
        if let Some(top_p) = invocation.top_p {
            body["top_p"] = json!(top_p);
        }
        if let Some(stream) = invocation.stream {
            body["stream"] = json!(stream);
        }
        
        // Add tools if present
        if let Some(tools) = &invocation.tools {
            let anthropic_tools: Vec<Value> = tools
                .iter()
                .enumerate()
                .map(|(i, tool)| {
                    let mut tool_json = json!({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": utils::clean_tool_schema(&tool.input_schema)
                    });
                    
                    // Add cache control to last tool
                    if i == tools.len() - 1 {
                        tool_json["cache_control"] = json!({"type": "ephemeral"});
                    }
                    
                    tool_json
                })
                .collect();
            body["tools"] = json!(anthropic_tools);
            body["tool_choice"] = json!({"type": "auto"});
        }
        
        // Add Anthropic-specific headers
        let mut headers = HashMap::new();
        headers.insert("anthropic-version".to_string(), "2023-06-01".to_string());
        headers.insert("content-type".to_string(), "application/json".to_string());
        
        Ok(TransformedRequest { body, headers })
    }
    
    fn transform_response(&self, response: Value) -> Result<TransformedResponse, ServiceError> {
        debug!("Transforming Anthropic response to unified format");
        
        // Extract content blocks
        let content_array = response.get("content")
            .ok_or_else(|| ServiceError::TransformError("No content in response".to_string()))?
            .as_array()
            .ok_or_else(|| ServiceError::TransformError("Content is not an array".to_string()))?;
        
        let mut unified_blocks = Vec::new();
        let mut function_calls = Vec::new();
        let mut tool_use_blocks = Vec::new();
        
        for block in content_array {
            match block.get("type").and_then(|t| t.as_str()) {
                Some("text") => {
                    if let Some(text) = block.get("text").and_then(|t| t.as_str()) {
                        unified_blocks.push(ContentBlock::Text {
                            text: text.to_string(),
                        });
                    }
                }
                Some("tool_use") => {
                    let id = block.get("id")
                        .and_then(|i| i.as_str())
                        .unwrap_or("")
                        .to_string();
                    let name = block.get("name")
                        .and_then(|n| n.as_str())
                        .unwrap_or("")
                        .to_string();
                    let input = block.get("input")
                        .cloned()
                        .unwrap_or(json!({}));
                    
                    // Add to content blocks
                    unified_blocks.push(ContentBlock::ToolUse {
                        id: id.clone(),
                        name: name.clone(),
                        input: input.clone(),
                    });
                    
                    // Also add to function_calls
                    function_calls.push(FunctionCall {
                        id: id.clone(),
                        name: name.clone(),
                        input: input.clone(),
                    });
                    
                    // Keep the original tool_use block for provider-specific format
                    tool_use_blocks.push(block.clone());
                }
                _ => {
                    warn!("Unknown content block type: {:?}", block.get("type"));
                }
            }
        }
        
        // Extract usage
        let usage = self.extract_usage(&response);
        
        // Extract stop reason
        let stop_reason = response.get("stop_reason")
            .and_then(|s| s.as_str())
            .map(|s| s.to_string());
        
        Ok(TransformedResponse {
            message: AssistantMessage {
                role: "assistant".to_string(),
                content: unified_blocks,
                tool_calls: if !tool_use_blocks.is_empty() {
                    Some(json!(tool_use_blocks))
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

impl AnthropicTransformer {
    fn extract_system_prompt(&self, messages: &[UnifiedMessage]) -> Option<String> {
        // Check if first message is system
        if let Some(first) = messages.first() {
            if first.role == "system" {
                match &first.content {
                    MessageContent::Text { content } => return Some(content.clone()),
                    MessageContent::Blocks { content } => {
                        let texts: Vec<String> = content
                            .iter()
                            .filter_map(|block| {
                                if let ContentBlock::Text { text } = block {
                                    Some(text.clone())
                                } else {
                                    None
                                }
                            })
                            .collect();
                        if !texts.is_empty() {
                            return Some(texts.join("\n"));
                        }
                    }
                }
            }
        }
        None
    }
    
    fn transform_messages(&self, messages: &[UnifiedMessage]) -> Result<Vec<Value>, ServiceError> {
        let mut anthropic_messages = Vec::new();
        
        for message in messages {
            // Skip system messages (handled separately)
            if message.role == "system" {
                continue;
            }
            
            let content = match &message.content {
                MessageContent::Text { content } => {
                    vec![json!({
                        "type": "text",
                        "text": content
                    })]
                }
                MessageContent::Blocks { content } => {
                    self.transform_content_blocks(&content)?
                }
            };
            
            // Only add non-empty messages
            if !content.is_empty() {
                anthropic_messages.push(json!({
                    "role": message.role,
                    "content": content
                }));
            }
        }
        
        Ok(anthropic_messages)
    }
    
    fn transform_content_blocks(&self, blocks: &[ContentBlock]) -> Result<Vec<Value>, ServiceError> {
        let mut anthropic_blocks = Vec::new();
        
        for block in blocks {
            match block {
                ContentBlock::Text { text } => {
                    anthropic_blocks.push(json!({
                        "type": "text",
                        "text": text
                    }));
                }
                ContentBlock::ToolUse { id, name, input } => {
                    anthropic_blocks.push(json!({
                        "type": "tool_use",
                        "id": id,
                        "name": name,
                        "input": input
                    }));
                }
                ContentBlock::ToolResult { tool_use_id, content } => {
                    anthropic_blocks.push(json!({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": content
                    }));
                }
                ContentBlock::Image { source } => {
                    anthropic_blocks.push(json!({
                        "type": "image",
                        "source": {
                            "type": source.source_type,
                            "media_type": source.media_type,
                            "data": source.data
                        }
                    }));
                }
            }
        }
        
        Ok(anthropic_blocks)
    }
    
    fn extract_usage(&self, response: &Value) -> Option<TokenUsage> {
        let usage = response.get("usage")?;
        
        let input_tokens = usage.get("input_tokens")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u32;
        let output_tokens = usage.get("output_tokens")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u32;
        
        Some(TokenUsage {
            input_tokens,
            output_tokens,
            total_tokens: input_tokens + output_tokens,
        })
    }
}