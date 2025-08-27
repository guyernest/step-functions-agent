mod auth;
mod agents;

use anyhow::Result;
use lambda_http::{run, service_fn, Body, Error, Request, Response};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{error, info, warn};

use auth::ApiKeyAuth;
use agents::StepFunctionsAgentsClient;

// MCP protocol types
#[derive(Debug, Serialize, Deserialize)]
struct JsonRpcRequest {
    jsonrpc: String,
    method: String,
    params: Option<Value>,
    id: Option<Value>,
}

#[derive(Debug, Serialize, Deserialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<JsonRpcError>,
    id: Option<Value>,
}

#[derive(Debug, Serialize, Deserialize)]
struct JsonRpcError {
    code: i32,
    message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<Value>,
}

// Standard JSON-RPC error codes
const METHOD_NOT_FOUND: i32 = -32601;
const INVALID_PARAMS: i32 = -32602;
const INTERNAL_ERROR: i32 = -32603;

// MCP server implementation
#[derive(Clone)]
struct McpServer {
    auth_client: Arc<ApiKeyAuth>,
    agents_client: Arc<StepFunctionsAgentsClient>,
    client_id: Arc<Mutex<Option<String>>>,
    client_name: Arc<Mutex<Option<String>>>,
}

impl McpServer {
    async fn new() -> Self {
        let aws_config = aws_config::defaults(aws_config::BehaviorVersion::latest()).load().await;
        
        let auth_client = Arc::new(ApiKeyAuth::new(&aws_config).await);
        let agents_client = Arc::new(StepFunctionsAgentsClient::new(&aws_config).await);

        Self {
            auth_client,
            agents_client,
            client_id: Arc::new(Mutex::new(None)),
            client_name: Arc::new(Mutex::new(None)),
        }
    }

    async fn set_client_info(&self, client_id: String, client_name: String) {
        let mut id = self.client_id.lock().await;
        let mut name = self.client_name.lock().await;
        *id = Some(client_id);
        *name = Some(client_name);
        info!("Client info updated for MCP server");
    }

    async fn handle_request(&self, request: JsonRpcRequest) -> JsonRpcResponse {
        let request_id = request.id.clone();
        
        match request.method.as_str() {
            "initialize" => self.handle_initialize(request.params, request_id).await,
            "tools/list" => self.handle_list_tools(request_id).await,
            "tools/call" => self.handle_tool_call(request.params, request_id).await,
            _ => JsonRpcResponse {
                jsonrpc: "2.0".to_string(),
                result: None,
                error: Some(JsonRpcError {
                    code: METHOD_NOT_FOUND,
                    message: format!("Method '{}' not found", request.method),
                    data: None,
                }),
                id: request_id,
            },
        }
    }

    async fn handle_initialize(&self, _params: Option<Value>, request_id: Option<Value>) -> JsonRpcResponse {
        info!("Initializing Step Functions Agents MCP server");
        
        JsonRpcResponse {
            jsonrpc: "2.0".to_string(),
            result: Some(json!({
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "step-functions-agents-mcp-server",
                    "version": "1.0.0"
                }
            })),
            error: None,
            id: request_id,
        }
    }

    async fn handle_list_tools(&self, request_id: Option<Value>) -> JsonRpcResponse {
        info!("Listing available MCP tools");
        
        let tools = vec![
            json!({
                "name": "start_agent",
                "description": "Start execution of a Step Functions agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent to execute"
                        },
                        "input_message": {
                            "type": "string", 
                            "description": "Input message for the agent"
                        },
                        "execution_name": {
                            "type": "string",
                            "description": "Optional execution name"
                        }
                    },
                    "required": ["agent_name", "input_message"]
                }
            }),
            json!({
                "name": "get_execution_status",
                "description": "Get status of an agent execution",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "execution_arn": {
                            "type": "string",
                            "description": "ARN of the execution to check"
                        }
                    },
                    "required": ["execution_arn"]
                }
            }),
            json!({
                "name": "list_available_agents",
                "description": "List all available agents",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            })
        ];

        JsonRpcResponse {
            jsonrpc: "2.0".to_string(),
            result: Some(json!({
                "tools": tools
            })),
            error: None,
            id: request_id,
        }
    }

    async fn handle_tool_call(&self, params: Option<Value>, request_id: Option<Value>) -> JsonRpcResponse {
        let params = match params {
            Some(p) => p,
            None => {
                return JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: None,
                    error: Some(JsonRpcError {
                        code: INVALID_PARAMS,
                        message: "Missing parameters".to_string(),
                        data: None,
                    }),
                    id: request_id,
                };
            }
        };

        let tool_name = match params.get("name").and_then(|n| n.as_str()) {
            Some(name) => name,
            None => {
                return JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: None,
                    error: Some(JsonRpcError {
                        code: INVALID_PARAMS,
                        message: "Missing tool name".to_string(),
                        data: None,
                    }),
                    id: request_id,
                };
            }
        };

        let arguments = params.get("arguments").cloned().unwrap_or(json!({}));

        match tool_name {
            "start_agent" => self.handle_start_agent(arguments, request_id).await,
            "get_execution_status" => self.handle_get_execution_status(arguments, request_id).await,
            "list_available_agents" => self.handle_list_available_agents(arguments, request_id).await,
            _ => JsonRpcResponse {
                jsonrpc: "2.0".to_string(),
                result: None,
                error: Some(JsonRpcError {
                    code: METHOD_NOT_FOUND,
                    message: format!("Tool '{}' not found", tool_name),
                    data: None,
                }),
                id: request_id,
            },
        }
    }

    async fn handle_start_agent(&self, arguments: Value, request_id: Option<Value>) -> JsonRpcResponse {
        let agent_name = match arguments.get("agent_name").and_then(|n| n.as_str()) {
            Some(name) => name,
            None => {
                return JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: None,
                    error: Some(JsonRpcError {
                        code: INVALID_PARAMS,
                        message: "Missing required parameter: agent_name".to_string(),
                        data: None,
                    }),
                    id: request_id,
                };
            }
        };

        let input_message = match arguments.get("input_message").and_then(|m| m.as_str()) {
            Some(msg) => msg,
            None => {
                return JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: None,
                    error: Some(JsonRpcError {
                        code: INVALID_PARAMS,
                        message: "Missing required parameter: input_message".to_string(),
                        data: None,
                    }),
                    id: request_id,
                };
            }
        };

        let execution_name = arguments.get("execution_name").and_then(|n| n.as_str()).map(|s| s.to_string());
        let client_id = self.client_id.lock().await.clone();

        let request = agents::StartExecutionRequest {
            agent_name: agent_name.to_string(),
            input_message: input_message.to_string(),
            execution_name,
            client_id,
        };

        match self.agents_client.start_agent_execution(request).await {
            Ok(response) => {
                let result_text = format!(
                    "✅ Agent execution started successfully!\n\n\
                     **Agent:** {}\n\
                     **Execution ID:** {}\n\
                     **Execution Name:** {}\n\
                     **Status:** {}\n\
                     **ARN:** {}\n\n\
                     Use `get_execution_status` with the execution ARN to check progress.",
                    agent_name,
                    response.execution_id,
                    response.execution_name,
                    response.status,
                    response.execution_arn
                );

                JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: Some(json!({
                        "content": [{
                            "type": "text",
                            "text": result_text
                        }],
                        "execution_arn": response.execution_arn,
                        "execution_id": response.execution_id,
                        "status": response.status
                    })),
                    error: None,
                    id: request_id,
                }
            }
            Err(e) => {
                error!("Failed to start agent execution: {}", e);
                JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: None,
                    error: Some(JsonRpcError {
                        code: INTERNAL_ERROR,
                        message: format!("Failed to start agent execution: {}", e),
                        data: None,
                    }),
                    id: request_id,
                }
            }
        }
    }

    async fn handle_get_execution_status(&self, arguments: Value, request_id: Option<Value>) -> JsonRpcResponse {
        let execution_arn = match arguments.get("execution_arn").and_then(|a| a.as_str()) {
            Some(arn) => arn,
            None => {
                return JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: None,
                    error: Some(JsonRpcError {
                        code: INVALID_PARAMS,
                        message: "Missing required parameter: execution_arn".to_string(),
                        data: None,
                    }),
                    id: request_id,
                };
            }
        };

        match self.agents_client.get_execution_status(execution_arn).await {
            Ok(execution_info) => {
                let status_emoji = match execution_info.status.as_str() {
                    "RUNNING" => "🏃",
                    "SUCCEEDED" => "✅", 
                    "FAILED" => "❌",
                    "TIMED_OUT" => "⏰",
                    "ABORTED" => "🛑",
                    _ => "❓"
                };

                let mut result_text = format!(
                    "{} **Execution Status**\n\n\
                     **Name:** {}\n\
                     **Status:** {}\n\
                     **ARN:** {}\n",
                    status_emoji,
                    execution_info.execution_name,
                    execution_info.status,
                    execution_arn
                );
                
                // Add timestamps if available
                if let Some(start_time) = execution_info.start_time {
                    result_text.push_str(&format!("**Started:** {}\n", start_time.format("%Y-%m-%d %H:%M:%S UTC")));
                }
                if let Some(end_time) = execution_info.end_time {
                    result_text.push_str(&format!("**Ended:** {}\n", end_time.format("%Y-%m-%d %H:%M:%S UTC")));
                    
                    // Calculate duration if both timestamps exist
                    if let Some(start_time) = execution_info.start_time {
                        let duration = end_time.signed_duration_since(start_time);
                        let seconds = duration.num_seconds();
                        let formatted_duration = if seconds >= 3600 {
                            format!("{}h {}m {}s", seconds / 3600, (seconds % 3600) / 60, seconds % 60)
                        } else if seconds >= 60 {
                            format!("{}m {}s", seconds / 60, seconds % 60)
                        } else {
                            format!("{}s", seconds)
                        };
                        result_text.push_str(&format!("**Duration:** {}\n", formatted_duration));
                    }
                }
                
                // Add error if present
                if let Some(ref error_msg) = execution_info.error {
                    result_text.push_str(&format!("\n❌ **Error:** {}\n", error_msg));
                }
                
                // Extract and format messages from output
                if let Some(ref output) = execution_info.output {
                    if let Some(messages) = output.get("messages").and_then(|m| m.as_array()) {
                        result_text.push_str("\n📝 **Conversation:**\n\n");
                        
                        for message in messages {
                            let role = message.get("role")
                                .and_then(|r| r.as_str())
                                .unwrap_or("unknown");
                            
                            let role_emoji = match role {
                                "user" => "👤",
                                "assistant" => "🤖",
                                "tool" => "🔧",
                                "system" => "⚙️",
                                _ => "📋"
                            };
                            
                            result_text.push_str(&format!("{} **{}**\n", role_emoji, role.to_uppercase()));
                            
                            // Handle different content types
                            if let Some(content) = message.get("content") {
                                if let Some(text) = content.as_str() {
                                    // Simple text content
                                    result_text.push_str(&format!("{}\n\n", text));
                                } else if let Some(content_array) = content.as_array() {
                                    // Array of content items (tool uses, etc.)
                                    for item in content_array {
                                        if let Some(item_type) = item.get("type").and_then(|t| t.as_str()) {
                                            match item_type {
                                                "text" => {
                                                    if let Some(text) = item.get("text").and_then(|t| t.as_str()) {
                                                        result_text.push_str(&format!("{}\n\n", text));
                                                    }
                                                }
                                                "tool_use" => {
                                                    let tool_name = item.get("name")
                                                        .and_then(|n| n.as_str())
                                                        .unwrap_or("Unknown Tool");
                                                    result_text.push_str(&format!("🔧 Using tool: **{}**\n", tool_name));
                                                    if let Some(input) = item.get("input") {
                                                        let input_str = serde_json::to_string_pretty(input).unwrap_or_default();
                                                        // Truncate long inputs
                                                        let truncated = if input_str.len() > 500 {
                                                            format!("{}...", &input_str[..500])
                                                        } else {
                                                            input_str
                                                        };
                                                        result_text.push_str(&format!("```json\n{}\n```\n\n", truncated));
                                                    }
                                                }
                                                "tool_result" => {
                                                    result_text.push_str("📊 Tool Result:\n");
                                                    if let Some(tool_content) = item.get("content") {
                                                        if let Some(text) = tool_content.as_str() {
                                                            // Truncate long results
                                                            let truncated = if text.len() > 1000 {
                                                                format!("{}...", &text[..1000])
                                                            } else {
                                                                text.to_string()
                                                            };
                                                            result_text.push_str(&format!("{}\n\n", truncated));
                                                        } else {
                                                            let content_str = serde_json::to_string_pretty(tool_content).unwrap_or_default();
                                                            let truncated = if content_str.len() > 500 {
                                                                format!("{}...", &content_str[..500])
                                                            } else {
                                                                content_str
                                                            };
                                                            result_text.push_str(&format!("```json\n{}\n```\n\n", truncated));
                                                        }
                                                    }
                                                }
                                                _ => {
                                                    result_text.push_str(&format!("Content type: {}\n\n", item_type));
                                                }
                                            }
                                        }
                                    }
                                } else {
                                    // Complex content object
                                    let content_str = serde_json::to_string_pretty(content).unwrap_or_default();
                                    let truncated = if content_str.len() > 500 {
                                        format!("{}...", &content_str[..500])
                                    } else {
                                        content_str
                                    };
                                    result_text.push_str(&format!("```json\n{}\n```\n\n", truncated));
                                }
                            }
                        }
                    } else if let Some(response) = output.get("response").and_then(|r| r.as_str()) {
                        // Fallback: simple response field
                        result_text.push_str(&format!("\n📝 **Response:**\n{}\n", response));
                    }
                }

                JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: Some(json!({
                        "content": [{
                            "type": "text",
                            "text": result_text
                        }],
                        "execution_arn": execution_arn,
                        "status": execution_info.status,
                        "execution_name": execution_info.execution_name,
                        "output": execution_info.output
                    })),
                    error: None,
                    id: request_id,
                }
            }
            Err(e) => {
                error!("Failed to get execution status: {}", e);
                JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: None,
                    error: Some(JsonRpcError {
                        code: INTERNAL_ERROR,
                        message: format!("Failed to get execution status: {}", e),
                        data: None,
                    }),
                    id: request_id,
                }
            }
        }
    }

    async fn handle_list_available_agents(&self, _arguments: Value, request_id: Option<Value>) -> JsonRpcResponse {
        match self.agents_client.list_available_agents().await {
            Ok(agents) => {
                if agents.is_empty() {
                    let result_text = "📭 No agents found in the registry.";
                    return JsonRpcResponse {
                        jsonrpc: "2.0".to_string(),
                        result: Some(json!({
                            "content": [{
                                "type": "text",
                                "text": result_text
                            }],
                            "agents": []
                        })),
                        error: None,
                        id: request_id,
                    };
                }

                let mut result_text = format!("🤖 **Available Agents** ({})\n\n", agents.len());

                for (i, agent) in agents.iter().enumerate() {
                    let status_emoji = match agent.status.as_str() {
                        "active" => "✅",
                        "inactive" => "⏸️", 
                        "deprecated" => "⚠️",
                        _ => "❓"
                    };

                    let description = agent.description
                        .as_ref()
                        .map(|d| d.as_str())
                        .unwrap_or("No description available");

                    result_text.push_str(&format!(
                        "{}. {} **{}** (v{})\n   {}\n   Status: {}\n   Tools: {}\n\n",
                        i + 1,
                        status_emoji,
                        agent.name,
                        agent.version,
                        description,
                        agent.status,
                        agent.tools.join(", ")
                    ));
                }

                JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: Some(json!({
                        "content": [{
                            "type": "text", 
                            "text": result_text
                        }],
                        "agents": agents
                    })),
                    error: None,
                    id: request_id,
                }
            }
            Err(e) => {
                error!("Failed to list available agents: {}", e);
                JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    result: None,
                    error: Some(JsonRpcError {
                        code: INTERNAL_ERROR,
                        message: format!("Failed to list available agents: {}", e),
                        data: None,
                    }),
                    id: request_id,
                }
            }
        }
    }
}

async fn function_handler(event: Request) -> Result<Response<Body>, Error> {
    // Extract API key from headers
    let api_key = event.headers()
        .get("x-api-key")
        .and_then(|v| v.to_str().ok());

    let server = McpServer::new().await;

    // Authenticate if API key is provided
    if let Some(key) = api_key {
        match server.auth_client.validate_api_key(key).await {
            Ok(auth) => {
                info!("Authenticated client: {}", auth.client_name);
                server.set_client_info(auth.client_id, auth.client_name).await;
            }
            Err(e) => {
                warn!("API key validation failed: {}", e);
                return Ok(Response::builder()
                    .status(401)
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"error":"Unauthorized"}"#))?);
            }
        }
    }

    // Parse request body
    let body = match event.body() {
        lambda_http::Body::Text(text) => text.clone(),
        lambda_http::Body::Binary(bytes) => String::from_utf8_lossy(bytes).to_string(),
        lambda_http::Body::Empty => String::new(),
    };

    let request: JsonRpcRequest = match serde_json::from_str(&body) {
        Ok(req) => req,
        Err(e) => {
            error!("Failed to parse JSON-RPC request: {}", e);
            let error_response = JsonRpcResponse {
                jsonrpc: "2.0".to_string(),
                result: None,
                error: Some(JsonRpcError {
                    code: -32700, // Parse error
                    message: "Parse error".to_string(),
                    data: Some(json!({"details": e.to_string()})),
                }),
                id: None,
            };
            
            return Ok(Response::builder()
                .status(400)
                .header("content-type", "application/json")
                .body(Body::from(serde_json::to_string(&error_response)?))?);
        }
    };

    let response = server.handle_request(request).await;
    let response_json = serde_json::to_string(&response)?;

    Ok(Response::builder()
        .status(200)
        .header("content-type", "application/json")
        .body(Body::from(response_json))?)
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .json()
        .init();

    info!("Starting Step Functions Agents MCP Server");
    
    run(service_fn(function_handler)).await
}