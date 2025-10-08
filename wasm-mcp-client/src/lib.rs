use wasm_bindgen::prelude::*;
use pmcp::WasmHttpClient;
use serde_json::{json, Value};
use serde::{Deserialize, Serialize};

// Set up console error panic hook for better debugging
#[wasm_bindgen(start)]
pub fn init_panic_hook() {
    console_error_panic_hook::set_once();
}

#[derive(Serialize)]
struct JsonRpcRequest {
    jsonrpc: String,
    id: i64,
    method: String,
    params: Value,
}

#[derive(Deserialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    id: Option<i64>,
    #[serde(default)]
    result: Option<Value>,
    #[serde(default)]
    error: Option<Value>,
}

#[wasm_bindgen]
pub struct PmcpWasmClient {
    server_url: String,
    client: Option<WasmHttpClient>,
    next_id: i64,
}

#[wasm_bindgen]
impl PmcpWasmClient {
    #[wasm_bindgen(constructor)]
    pub fn new(server_url: String) -> PmcpWasmClient {
        PmcpWasmClient {
            server_url,
            client: None,
            next_id: 1,
        }
    }

    fn get_next_id(&mut self) -> i64 {
        let id = self.next_id;
        self.next_id += 1;
        id
    }

    /// Initialize the MCP connection using pmcp WasmHttpClient
    #[wasm_bindgen]
    pub async fn initialize(&mut self) -> Result<JsValue, JsValue> {
        // Log the server URL being used
        web_sys::console::log_1(&format!("Initializing WASM client with URL: {}", self.server_url).into());

        let config = pmcp::WasmHttpConfig {
            url: self.server_url.clone(),
            extra_headers: vec![],
        };

        let mut client = WasmHttpClient::new(config);

        // Send direct JSON-RPC initialize request
        let id = self.get_next_id();
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            id,
            method: "initialize".to_string(),
            params: json!({
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "pmcp-wasm-client",
                    "version": "1.0.0"
                }
            }),
        };

        web_sys::console::log_1(&"Sending initialize request...".into());

        let response: JsonRpcResponse = client.request(request).await
            .map_err(|e| {
                let error_msg = format!("Failed to initialize: {}", e);
                web_sys::console::error_1(&error_msg.clone().into());
                JsValue::from_str(&error_msg)
            })?;

        web_sys::console::log_1(&"Received initialize response".into());

        // Check for errors
        if let Some(error) = response.error {
            let error_msg = format!("Server error: {}", error);
            web_sys::console::error_1(&error_msg.clone().into());
            return Err(JsValue::from_str(&error_msg));
        }

        self.client = Some(client);
        Ok(JsValue::from_str("Initialized successfully"))
    }

    /// List all available tools using pmcp
    #[wasm_bindgen]
    pub async fn list_tools(&mut self) -> Result<JsValue, JsValue> {
        // Get ID first before borrowing client
        let id = self.get_next_id();

        let client = self.client.as_mut()
            .ok_or_else(|| JsValue::from_str("Client not initialized"))?;

        // Send direct JSON-RPC list tools request
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            id,
            method: "tools/list".to_string(),
            params: json!({}),
        };

        let response: JsonRpcResponse = client.request(request).await
            .map_err(|e| JsValue::from_str(&format!("Failed to list tools: {}", e)))?;

        // Check for errors
        if let Some(error) = response.error {
            return Err(JsValue::from_str(&format!("Server error: {}", error)));
        }

        // Return the tools array from result
        if let Some(result) = response.result {
            if let Some(tools) = result.get("tools") {
                // Convert to JSON string first, then parse in JS to preserve all nested fields
                let json_str = serde_json::to_string(&tools)
                    .map_err(|e| JsValue::from_str(&format!("Failed to serialize tools: {}", e)))?;

                // Parse the JSON string in JavaScript to get proper objects
                let js_json = js_sys::JSON::parse(&json_str)
                    .map_err(|e| JsValue::from_str(&format!("Failed to parse JSON: {:?}", e)))?;

                return Ok(js_json);
            }
        }

        Err(JsValue::from_str("Invalid response from server"))
    }

    /// Call a tool using pmcp
    #[wasm_bindgen]
    pub async fn call_tool(&mut self, tool_name: String, arguments: JsValue) -> Result<JsValue, JsValue> {
        // Get ID first before borrowing client
        let id = self.get_next_id();

        let client = self.client.as_mut()
            .ok_or_else(|| JsValue::from_str("Client not initialized"))?;

        // Convert JS arguments to Value
        let args: Value = serde_wasm_bindgen::from_value(arguments)
            .map_err(|e| JsValue::from_str(&format!("Failed to parse arguments: {}", e)))?;

        // Send direct JSON-RPC call tool request
        
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            id,
            method: "tools/call".to_string(),
            params: json!({
                "name": tool_name,
                "arguments": args
            }),
        };

        let response: JsonRpcResponse = client.request(request).await
            .map_err(|e| JsValue::from_str(&format!("Tool call failed: {}", e)))?;

        // Check for errors
        if let Some(error) = response.error {
            return Err(JsValue::from_str(&format!("Server error: {}", error)));
        }

        // Return the result
        if let Some(result) = response.result {
            // Use JSON.parse to preserve all nested fields
            let json_str = serde_json::to_string(&result)
                .map_err(|e| JsValue::from_str(&format!("Failed to serialize result: {}", e)))?;

            let js_json = js_sys::JSON::parse(&json_str)
                .map_err(|e| JsValue::from_str(&format!("Failed to parse JSON: {:?}", e)))?;

            return Ok(js_json);
        }

        Err(JsValue::from_str("Invalid response from server"))
    }

    /// List all available resources using pmcp
    #[wasm_bindgen]
    pub async fn list_resources(&mut self) -> Result<JsValue, JsValue> {
        // Get ID first before borrowing client
        let id = self.get_next_id();

        let client = self.client.as_mut()
            .ok_or_else(|| JsValue::from_str("Client not initialized"))?;

        
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            id,
            method: "resources/list".to_string(),
            params: json!({}),
        };

        let response: JsonRpcResponse = client.request(request).await
            .map_err(|e| JsValue::from_str(&format!("Failed to list resources: {}", e)))?;

        if let Some(error) = response.error {
            return Err(JsValue::from_str(&format!("Server error: {}", error)));
        }

        if let Some(result) = response.result {
            if let Some(resources) = result.get("resources") {
                // Use JSON.parse to preserve all nested fields
                let json_str = serde_json::to_string(&resources)
                    .map_err(|e| JsValue::from_str(&format!("Failed to serialize resources: {}", e)))?;

                let js_json = js_sys::JSON::parse(&json_str)
                    .map_err(|e| JsValue::from_str(&format!("Failed to parse JSON: {:?}", e)))?;

                return Ok(js_json);
            }
        }

        Err(JsValue::from_str("Invalid response from server"))
    }

    /// Read a specific resource using pmcp
    #[wasm_bindgen]
    pub async fn read_resource(&mut self, uri: String) -> Result<JsValue, JsValue> {
        // Get ID first before borrowing client
        let id = self.get_next_id();

        let client = self.client.as_mut()
            .ok_or_else(|| JsValue::from_str("Client not initialized"))?;

        
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            id,
            method: "resources/read".to_string(),
            params: json!({
                "uri": uri
            }),
        };

        let response: JsonRpcResponse = client.request(request).await
            .map_err(|e| JsValue::from_str(&format!("Failed to read resource: {}", e)))?;

        if let Some(error) = response.error {
            return Err(JsValue::from_str(&format!("Server error: {}", error)));
        }

        if let Some(result) = response.result {
            // Use JSON.parse to preserve all nested fields
            let json_str = serde_json::to_string(&result)
                .map_err(|e| JsValue::from_str(&format!("Failed to serialize resource: {}", e)))?;

            let js_json = js_sys::JSON::parse(&json_str)
                .map_err(|e| JsValue::from_str(&format!("Failed to parse JSON: {:?}", e)))?;

            return Ok(js_json);
        }

        Err(JsValue::from_str("Invalid response from server"))
    }

    /// List all available prompts using pmcp
    #[wasm_bindgen]
    pub async fn list_prompts(&mut self) -> Result<JsValue, JsValue> {
        // Get ID first before borrowing client
        let id = self.get_next_id();

        let client = self.client.as_mut()
            .ok_or_else(|| JsValue::from_str("Client not initialized"))?;

        
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            id,
            method: "prompts/list".to_string(),
            params: json!({}),
        };

        let response: JsonRpcResponse = client.request(request).await
            .map_err(|e| JsValue::from_str(&format!("Failed to list prompts: {}", e)))?;

        if let Some(error) = response.error {
            return Err(JsValue::from_str(&format!("Server error: {}", error)));
        }

        if let Some(result) = response.result {
            if let Some(prompts) = result.get("prompts") {
                // Use JSON.parse to preserve all nested fields
                let json_str = serde_json::to_string(&prompts)
                    .map_err(|e| JsValue::from_str(&format!("Failed to serialize prompts: {}", e)))?;

                let js_json = js_sys::JSON::parse(&json_str)
                    .map_err(|e| JsValue::from_str(&format!("Failed to parse JSON: {:?}", e)))?;

                return Ok(js_json);
            }
        }

        Err(JsValue::from_str("Invalid response from server"))
    }

    /// Get a prompt with arguments using pmcp
    #[wasm_bindgen]
    pub async fn get_prompt(&mut self, name: String, arguments: JsValue) -> Result<JsValue, JsValue> {
        // Get ID first before borrowing client
        let id = self.get_next_id();

        let client = self.client.as_mut()
            .ok_or_else(|| JsValue::from_str("Client not initialized"))?;

        let args: Value = if arguments.is_null() || arguments.is_undefined() {
            json!({})
        } else {
            serde_wasm_bindgen::from_value(arguments)
                .map_err(|e| JsValue::from_str(&format!("Failed to parse arguments: {}", e)))?
        };

        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            id,
            method: "prompts/get".to_string(),
            params: json!({
                "name": name,
                "arguments": args
            }),
        };

        let response: JsonRpcResponse = client.request(request).await
            .map_err(|e| JsValue::from_str(&format!("Failed to get prompt: {}", e)))?;

        if let Some(error) = response.error {
            return Err(JsValue::from_str(&format!("Server error: {}", error)));
        }

        if let Some(result) = response.result {
            // Use JSON.parse to preserve all nested fields
            let json_str = serde_json::to_string(&result)
                .map_err(|e| JsValue::from_str(&format!("Failed to serialize prompt: {}", e)))?;

            let js_json = js_sys::JSON::parse(&json_str)
                .map_err(|e| JsValue::from_str(&format!("Failed to parse JSON: {:?}", e)))?;

            return Ok(js_json);
        }

        Err(JsValue::from_str("Invalid response from server"))
    }
}