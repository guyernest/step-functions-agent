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
        debug!("Transforming request to Bedrock Converse format");
        
        // Build the request body according to Bedrock Converse API spec
        let mut body = json!({
            "messages": self.transform_messages(&invocation.messages)?
        });
        
        // Add inferenceConfig with parameters
        let mut inference_config = json!({
            "maxTokens": invocation.max_tokens.unwrap_or(4096)
        });
        
        if let Some(temp) = invocation.temperature {
            inference_config["temperature"] = json!(temp);
        }
        if let Some(top_p) = invocation.top_p {
            inference_config["topP"] = json!(top_p);
        }
        
        body["inferenceConfig"] = inference_config;
        
        // Add tools if present - all Bedrock models use the same format
        if let Some(tools) = &invocation.tools {
            let bedrock_tools: Vec<Value> = tools
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
                "tools": bedrock_tools,
                "toolChoice": {"auto": {}}
            });
        }
        
        // Add system message if present - as an array per the API spec
        if let Some(system_msg) = self.extract_system_message(&invocation.messages) {
            body["system"] = json!([
                {
                    "text": system_msg
                }
            ]);
        }
        
        Ok(TransformedRequest {
            body,
            headers: HashMap::new(),
        })
    }
    
    fn transform_response(&self, response: Value) -> Result<TransformedResponse, ServiceError> {
        debug!("Transforming Bedrock response to unified format");
        
        // Bedrock Converse API response format
        let output = response.get("output")
            .ok_or_else(|| ServiceError::TransformError("No output in Bedrock response".to_string()))?;
        
        let message = output.get("message")
            .ok_or_else(|| ServiceError::TransformError("No message in output".to_string()))?;
        
        // Extract content from Bedrock Converse format
        let mut unified_blocks = Vec::new();
        let mut function_calls = Vec::new();
        
        if let Some(content_array) = message.get("content").and_then(|c| c.as_array()) {
            for content_item in content_array {
                if let Some(text_obj) = content_item.get("text") {
                    if let Some(text) = text_obj.as_str() {
                        unified_blocks.push(ContentBlock::Text {
                            text: text.to_string(),
                        });
                    }
                } else if let Some(tool_use) = content_item.get("toolUse") {
                    // Extract tool use
                    if let (Some(id), Some(name), Some(input)) = (
                        tool_use.get("toolUseId").and_then(|i| i.as_str()),
                        tool_use.get("name").and_then(|n| n.as_str()),
                        tool_use.get("input")
                    ) {
                        unified_blocks.push(ContentBlock::ToolUse {
                            id: id.to_string(),
                            name: name.to_string(),
                            input: input.clone(),
                        });
                        
                        function_calls.push(FunctionCall {
                            id: id.to_string(),
                            name: name.to_string(),
                            input: input.clone(),
                        });
                    }
                }
            }
        }
        
        // Build tool_calls for compatibility
        let tool_calls = if !function_calls.is_empty() {
            let tool_calls_array: Vec<Value> = function_calls
                .iter()
                .map(|fc| json!({
                    "id": fc.id,
                    "type": "function",
                    "function": {
                        "name": fc.name,
                        "arguments": fc.input.to_string()
                    }
                }))
                .collect();
            Some(json!(tool_calls_array))
        } else {
            None
        };
        
        // Extract usage from Bedrock Converse
        let usage = response.get("usage")
            .and_then(|u| {
                let input_tokens = u.get("inputTokens")?.as_u64()?;
                let output_tokens = u.get("outputTokens")?.as_u64()?;
                let total_tokens = u.get("totalTokens")?.as_u64()?;
                
                Some(TokenUsage {
                    input_tokens: input_tokens as u32,
                    output_tokens: output_tokens as u32,
                    total_tokens: total_tokens as u32,
                })
            });
        
        // Extract stop reason
        let stop_reason = response.get("stopReason")
            .and_then(|s| s.as_str())
            .map(|s| s.to_string());
        
        Ok(TransformedResponse {
            message: AssistantMessage {
                role: "assistant".to_string(),
                content: unified_blocks,
                tool_calls,
            },
            function_calls: if function_calls.is_empty() { None } else { Some(function_calls) },
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
                        // Add tool response messages in Bedrock Converse format
                        let tool_result_contents: Vec<Value> = tool_results
                            .into_iter()
                            .map(|(tool_use_id, content)| {
                                json!({
                                    "toolResult": {
                                        "toolUseId": tool_use_id,
                                        "content": [
                                            {
                                                "text": content
                                            }
                                        ]
                                    }
                                })
                            })
                            .collect();
                        
                        bedrock_messages.push(json!({
                            "role": "user",
                            "content": tool_result_contents
                        }));
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
                // Bedrock Converse expects content as an array
                msg["content"] = json!([
                    {
                        "text": content
                    }
                ]);
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
                
                // For blocks without tool uses, also use array format
                if !text_parts.is_empty() && !content.iter().any(|b| matches!(b, ContentBlock::ToolUse { .. })) {
                    msg["content"] = json!([
                        {
                            "text": text_parts.join("\n")
                        }
                    ]);
                }
                
                // Handle tool uses for Bedrock Converse format
                let tool_uses: Vec<Value> = content
                    .iter()
                    .filter_map(|block| {
                        if let ContentBlock::ToolUse { id, name, input } = block {
                            Some(json!({
                                "toolUseId": id,
                                "name": name,
                                "input": input
                            }))
                        } else {
                            None
                        }
                    })
                    .collect();
                
                if !tool_uses.is_empty() {
                    // For Bedrock Converse, tool uses go in the content array
                    let mut content_array = vec![];
                    
                    // Add text content if exists
                    if !text_parts.is_empty() {
                        content_array.push(json!({
                            "text": text_parts.join("\n")
                        }));
                    }
                    
                    // Add tool uses
                    for tool_use in tool_uses {
                        content_array.push(json!({
                            "toolUse": tool_use
                        }));
                    }
                    
                    msg["content"] = json!(content_array);
                }
            }
        }
        
        Ok(msg)
    }
    
}