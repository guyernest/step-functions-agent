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

pub struct BedrockTransformer;

#[async_trait]
impl MessageTransformer for BedrockTransformer {
    fn transform_request(&self, invocation: &LLMInvocation) -> Result<TransformedRequest, ServiceError> {
        debug!("Transforming request to Bedrock format");
        
        // Bedrock uses different formats for different models
        // This implementation handles the common format (Jamba, Nova)
        
        let mut body = json!({
            "messages": self.transform_messages(&invocation.messages)?,
            "max_tokens": invocation.max_tokens.unwrap_or(4096),
        });
        
        // Add model ID if not Nova (Nova uses different field name)
        if !invocation.provider_config.model_id.contains("nova") {
            body["model"] = json!(invocation.provider_config.model_id);
        }
        
        // Add optional parameters
        if let Some(temp) = invocation.temperature {
            body["temperature"] = json!(temp);
        }
        if let Some(top_p) = invocation.top_p {
            body["top_p"] = json!(top_p);
        }
        
        // Add tools if present
        if let Some(tools) = &invocation.tools {
            // Check if this is Nova model (uses different tool format)
            if invocation.provider_config.model_id.contains("nova") {
                let nova_tools: Vec<Value> = tools
                    .iter()
                    .map(|tool| {
                        json!({
                            "toolSpec": {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": {
                                    "json": utils::clean_tool_schema(&tool.input_schema)
                                }
                            }
                        })
                    })
                    .collect();
                body["toolConfig"] = json!({
                    "tools": nova_tools,
                    "toolChoice": {"auto": {}}
                });
            } else {
                // Standard Bedrock/OpenAI format
                let bedrock_tools: Vec<Value> = tools
                    .iter()
                    .map(|tool| {
                        json!({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": utils::clean_tool_schema(&tool.input_schema)
                            }
                        })
                    })
                    .collect();
                body["tools"] = json!(bedrock_tools);
            }
        }
        
        // Add system message if present
        if let Some(system_msg) = self.extract_system_message(&invocation.messages) {
            body["system"] = json!(system_msg);
        }
        
        Ok(TransformedRequest {
            body,
            headers: HashMap::new(),
        })
    }
    
    fn transform_response(&self, response: Value) -> Result<TransformedResponse, ServiceError> {
        debug!("Transforming Bedrock response to unified format");
        
        // Bedrock response format is similar to OpenAI
        let choice = response.get("choices")
            .and_then(|c| c.get(0))
            .or_else(|| response.get("output")) // Some Bedrock models use "output" directly
            .ok_or_else(|| ServiceError::TransformError("No choices/output in response".to_string()))?;
        
        let message = if choice.is_object() && choice.get("message").is_some() {
            choice.get("message").unwrap()
        } else {
            &choice
        };
        
        // Extract content
        let mut unified_blocks = Vec::new();
        if let Some(content) = message.get("content").and_then(|c| c.as_str()) {
            if !content.is_empty() {
                unified_blocks.push(ContentBlock::Text {
                    text: content.to_string(),
                });
            }
        }
        
        // Extract tool calls
        let (tool_calls, function_calls) = self.extract_tool_calls(message)?;
        
        // Extract usage
        let usage = self.extract_usage(&response);
        
        // Extract stop reason
        let stop_reason = choice.get("finish_reason")
            .or_else(|| response.get("stop_reason"))
            .and_then(|s| s.as_str())
            .map(|s| s.to_string());
        
        Ok(TransformedResponse {
            message: AssistantMessage {
                role: "assistant".to_string(),
                content: unified_blocks,
                tool_calls,
            },
            function_calls,
            usage,
            stop_reason,
        })
    }
}

impl BedrockTransformer {
    fn extract_system_message(&self, messages: &[UnifiedMessage]) -> Option<String> {
        messages.first()
            .filter(|m| m.role == "system")
            .and_then(|m| match &m.content {
                MessageContent::Text { content } => Some(content.clone()),
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
                        Some(texts.join("\n"))
                    } else {
                        None
                    }
                }
            })
    }
    
    fn transform_messages(&self, messages: &[UnifiedMessage]) -> Result<Vec<Value>, ServiceError> {
        let mut bedrock_messages = Vec::new();
        let mut i = 0;
        
        while i < messages.len() {
            let message = &messages[i];
            
            // Skip system messages (handled separately)
            if message.role == "system" {
                i += 1;
                continue;
            }
            
            // Check for tool results (similar to OpenAI)
            if message.role == "user" {
                if let MessageContent::Blocks { content } = &message.content {
                    let tool_results: Vec<_> = content
                        .iter()
                        .filter_map(|block| {
                            if let ContentBlock::ToolResult { tool_use_id, content } = block {
                                Some((tool_use_id.clone(), content.clone()))
                            } else {
                                None
                            }
                        })
                        .collect();
                    
                    if !tool_results.is_empty() {
                        // Add tool response messages
                        for (tool_use_id, content) in tool_results {
                            bedrock_messages.push(json!({
                                "role": "tool",
                                "tool_call_id": tool_use_id,
                                "content": content
                            }));
                        }
                        i += 1;
                        continue;
                    }
                }
            }
            
            bedrock_messages.push(self.transform_single_message(message)?);
            i += 1;
        }
        
        Ok(bedrock_messages)
    }
    
    fn transform_single_message(&self, message: &UnifiedMessage) -> Result<Value, ServiceError> {
        let mut msg = json!({
            "role": message.role,
        });
        
        match &message.content {
            MessageContent::Text { content } => {
                msg["content"] = json!(content);
            }
            MessageContent::Blocks { content } => {
                let text_parts: Vec<String> = content
                    .iter()
                    .filter_map(|block| {
                        if let ContentBlock::Text { text } = block {
                            Some(text.clone())
                        } else {
                            None
                        }
                    })
                    .collect();
                
                if !text_parts.is_empty() {
                    msg["content"] = json!(text_parts.join("\n"));
                }
                
                // Handle tool uses
                let tool_uses: Vec<Value> = content
                    .iter()
                    .filter_map(|block| {
                        if let ContentBlock::ToolUse { id, name, input } = block {
                            Some(json!({
                                "id": id,
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": input.to_string()
                                }
                            }))
                        } else {
                            None
                        }
                    })
                    .collect();
                
                if !tool_uses.is_empty() {
                    msg["tool_calls"] = json!(tool_uses);
                }
            }
        }
        
        Ok(msg)
    }
    
    fn extract_tool_calls(&self, message: &Value) -> Result<(Option<Value>, Option<Vec<FunctionCall>>), ServiceError> {
        if let Some(tool_calls) = message.get("tool_calls") {
            if let Some(calls_array) = tool_calls.as_array() {
                let function_calls: Vec<FunctionCall> = calls_array
                    .iter()
                    .filter_map(|call| {
                        let id = call.get("id")?.as_str()?;
                        let function = call.get("function")?;
                        let name = function.get("name")?.as_str()?;
                        let args_str = function.get("arguments")?.as_str()?;
                        
                        let input = serde_json::from_str(args_str).unwrap_or(json!({}));
                        
                        Some(FunctionCall {
                            id: id.to_string(),
                            name: name.to_string(),
                            input,
                        })
                    })
                    .collect();
                
                if !function_calls.is_empty() {
                    return Ok((Some(tool_calls.clone()), Some(function_calls)));
                }
            }
        }
        
        Ok((None, None))
    }
    
    fn extract_usage(&self, response: &Value) -> Option<TokenUsage> {
        let usage = response.get("usage")?;
        
        let input_tokens = usage.get("input_tokens")
            .or_else(|| usage.get("prompt_tokens"))
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u32;
        
        let output_tokens = usage.get("output_tokens")
            .or_else(|| usage.get("completion_tokens"))
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u32;
        
        Some(TokenUsage {
            input_tokens,
            output_tokens,
            total_tokens: input_tokens + output_tokens,
        })
    }
}