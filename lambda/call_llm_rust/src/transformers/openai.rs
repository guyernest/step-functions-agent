use super::{MessageTransformer, utils};
use crate::error::ServiceError;
use crate::models::{
    AssistantMessage, ContentBlock, FunctionCall, LLMInvocation, MessageContent, TokenUsage,
    TransformedRequest, TransformedResponse, UnifiedMessage,
};
use async_trait::async_trait;
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use tracing::{debug, warn};

pub struct OpenAITransformer;

#[async_trait]
impl MessageTransformer for OpenAITransformer {
    fn transform_request(&self, invocation: &LLMInvocation) -> Result<TransformedRequest, ServiceError> {
        debug!("Transforming request to OpenAI format");
        
        let mut body = json!({
            "model": invocation.provider_config.model_id,
            "messages": self.transform_messages(&invocation.messages)?,
        });
        
        // Add optional parameters
        if let Some(temp) = invocation.temperature {
            body["temperature"] = json!(temp);
        }
        if let Some(max_tokens) = invocation.max_tokens {
            body["max_tokens"] = json!(max_tokens);
        }
        if let Some(top_p) = invocation.top_p {
            body["top_p"] = json!(top_p);
        }
        if let Some(stream) = invocation.stream {
            body["stream"] = json!(stream);
        }
        
        // Add tools if present
        if let Some(tools) = &invocation.tools {
            let openai_tools: Vec<Value> = tools
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
            body["tools"] = json!(openai_tools);
        }
        
        Ok(TransformedRequest {
            body,
            headers: HashMap::new(),
        })
    }
    
    fn transform_response(&self, response: Value) -> Result<TransformedResponse, ServiceError> {
        debug!("Transforming OpenAI response to unified format");
        
        // Extract choice
        let choice = utils::extract_with_fallback(&response, &["choices.0", "results.0"])
            .ok_or_else(|| ServiceError::TransformError("No choices in response".to_string()))?;
        
        // Extract message
        let message = choice.get("message")
            .ok_or_else(|| ServiceError::TransformError("No message in choice".to_string()))?;
        
        // Transform content
        let content = self.transform_response_content(message)?;
        
        // Extract tool calls if present
        let (tool_calls, function_calls) = self.extract_tool_calls(message)?;
        
        // Extract usage
        let usage = self.extract_usage(&response);
        
        // Extract stop reason
        let stop_reason = utils::extract_string(&choice, &["finish_reason", "stop_reason"]);
        
        Ok(TransformedResponse {
            message: AssistantMessage {
                role: "assistant".to_string(),
                content,
                tool_calls,
            },
            function_calls,
            usage,
            stop_reason,
        })
    }
}

impl OpenAITransformer {
    fn transform_messages(&self, messages: &[UnifiedMessage]) -> Result<Vec<Value>, ServiceError> {
        let mut openai_messages: Vec<Value> = Vec::new();
        let mut i = 0;
        let mut processed_assistant_indices = HashSet::new();
        
        while i < messages.len() {
            let message = &messages[i];
            
            // Check if this is a user message with tool results
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
                        // Find the previous assistant message that should have tool_calls
                        let mut found_assistant = false;
                        for j in (0..i).rev() {
                            if messages[j].role == "assistant" {
                                // Check if we already processed this assistant message
                                if !processed_assistant_indices.contains(&j) {
                                    // Remove the previously added message without tool_calls
                                    // Find and remove it from openai_messages
                                    let messages_to_check = openai_messages.len().min(i);
                                    for k in (0..messages_to_check).rev() {
                                        if openai_messages[k].get("role") == Some(&json!("assistant")) {
                                            openai_messages.remove(k);
                                            break;
                                        }
                                    }
                                    
                                    // Now add it with tool_calls
                                    let mut assistant_msg = self.transform_single_message(&messages[j])?;
                                    
                                    // Add tool_calls if not present
                                    if !assistant_msg.get("tool_calls").is_some() {
                                        let tool_calls = self.reconstruct_tool_calls(&messages[j], &tool_results)?;
                                        assistant_msg["tool_calls"] = json!(tool_calls);
                                    }
                                    
                                    openai_messages.push(assistant_msg);
                                    processed_assistant_indices.insert(j);
                                }
                                found_assistant = true;
                                break;
                            }
                        }
                        
                        // Add tool response messages
                        for (tool_use_id, content) in tool_results {
                            openai_messages.push(json!({
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
            
            // Skip if this assistant message was already processed with tool_calls
            if message.role == "assistant" && processed_assistant_indices.contains(&i) {
                i += 1;
                continue;
            }
            
            openai_messages.push(self.transform_single_message(message)?);
            i += 1;
        }
        
        Ok(openai_messages)
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
                
                // Set content - OpenAI requires this field to be a string (even if empty)
                if !text_parts.is_empty() {
                    msg["content"] = json!(text_parts.join("\n"));
                } else {
                    // OpenAI requires content field to be an empty string when there's no text
                    msg["content"] = json!("");
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
    
    fn reconstruct_tool_calls(&self, message: &UnifiedMessage, tool_results: &[(String, String)]) -> Result<Vec<Value>, ServiceError> {
        if let MessageContent::Blocks { content } = &message.content {
            let tool_calls: Vec<Value> = content
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
            
            if !tool_calls.is_empty() {
                return Ok(tool_calls);
            }
        }
        
        // If we can't find tool uses in the message, create from results
        Ok(tool_results
            .iter()
            .map(|(id, _)| {
                json!({
                    "id": id,
                    "type": "function",
                    "function": {
                        "name": "unknown",
                        "arguments": "{}"
                    }
                })
            })
            .collect())
    }
    
    fn transform_response_content(&self, message: &Value) -> Result<Vec<ContentBlock>, ServiceError> {
        let mut blocks = Vec::new();
        
        // Extract text content
        if let Some(content) = message.get("content") {
            if let Some(text) = content.as_str() {
                if !text.is_empty() {
                    blocks.push(ContentBlock::Text {
                        text: text.to_string(),
                    });
                }
            }
        }
        
        Ok(blocks)
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
        
        let input_tokens = utils::extract_u32(&usage, &["prompt_tokens", "input_tokens"], 0);
        let output_tokens = utils::extract_u32(&usage, &["completion_tokens", "output_tokens"], 0);
        
        Some(TokenUsage {
            input_tokens,
            output_tokens,
            total_tokens: input_tokens + output_tokens,
        })
    }
}