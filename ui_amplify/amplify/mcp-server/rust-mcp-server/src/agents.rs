//! Step Functions Agents Client for MCP Server

use aws_sdk_sfn::{Client as SfnClient};
use aws_sdk_dynamodb::{Client as DynamoDbClient, types::AttributeValue};
use anyhow::{Result, anyhow};
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use tracing::info;
use uuid::Uuid;
use serde_json::{json, Value};

/// Client for interacting with Step Functions agents  
pub struct StepFunctionsAgentsClient {
    sfn: SfnClient,
    dynamodb: DynamoDbClient,
    environment: String,
    graphql_endpoint: Option<String>,
    api_key: Option<String>,
}

/// Agent definition from registry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Agent {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub version: String,
    pub status: String,
    pub state_machine_arn: Option<String>,
    pub tools: Vec<String>,
    pub llm_provider: Option<String>,
    pub llm_model: Option<String>,
    pub system_prompt: Option<String>,
    pub parameters: Option<String>,
    pub metadata: Option<String>,
}

/// Request to start agent execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartExecutionRequest {
    pub agent_name: String,
    pub input_message: String,
    pub execution_name: Option<String>,
    pub client_id: Option<String>,
}

/// Response from starting agent execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartExecutionResponse {
    pub execution_id: String,
    pub execution_arn: String,
    pub execution_name: String,
    pub status: String,
    pub estimated_duration_seconds: i64,
}

/// Execution information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionInfo {
    pub execution_arn: String,
    pub execution_name: String,
    pub status: String,
    pub start_time: Option<DateTime<Utc>>,
    pub end_time: Option<DateTime<Utc>>,
    pub input: Option<serde_json::Value>,
    pub output: Option<serde_json::Value>,
    pub error: Option<String>,
}

impl StepFunctionsAgentsClient {
    /// Create new client
    pub async fn new(aws_config: &aws_config::SdkConfig) -> Self {
        let sfn = SfnClient::new(aws_config);
        let dynamodb = DynamoDbClient::new(aws_config);
        let environment = std::env::var("ENVIRONMENT").unwrap_or_else(|_| "prod".to_string());
        let graphql_endpoint = std::env::var("GRAPHQL_ENDPOINT").ok();
        let api_key = std::env::var("GRAPHQL_API_KEY").ok();
        
        info!("Initialized StepFunctionsAgentsClient for environment: {}", environment);
        if let Some(ref endpoint) = graphql_endpoint {
            info!("GraphQL endpoint configured: {}", endpoint);
        } else {
            info!("GraphQL endpoint not found in environment variables");
        }
        if api_key.is_some() {
            info!("GraphQL API key configured");
        } else {
            info!("GraphQL API key not found in environment variables");
        }
        
        Self {
            sfn,
            dynamodb,
            environment,
            graphql_endpoint,
            api_key,
        }
    }
    
    /// Start agent execution
    pub async fn start_agent_execution(&self, request: StartExecutionRequest) -> Result<StartExecutionResponse> {
        info!("Starting execution for agent: {}", request.agent_name);
        
        // Generate execution name if not provided
        let execution_name = request.execution_name
            .unwrap_or_else(|| format!("{}-{}", request.agent_name, Uuid::new_v4().to_string()[..8].to_string()));
            
        // Construct state machine ARN from agent name
        // Region will be automatically resolved by AWS SDK from Lambda runtime
        let account_id = std::env::var("AWS_ACCOUNT_ID").unwrap_or_else(|_| "123456789012".to_string());
        let region = std::env::var("AWS_DEFAULT_REGION").unwrap_or_else(|_| "us-east-1".to_string());
        let environment = std::env::var("ENVIRONMENT").unwrap_or_else(|_| "prod".to_string());
        
        // State machines follow the pattern: {agent-name}-{environment}
        let state_machine_name = format!("{}-{}", request.agent_name, environment);
        let state_machine_arn = format!(
            "arn:aws:states:{}:{}:stateMachine:{}",
            region,
            account_id,
            state_machine_name
        );
        
        // Create execution input in the format expected by Step Functions
        // The state machine expects a messages array with role and content
        let input = serde_json::json!({
            "messages": [
                {
                    "role": "user",
                    "content": request.input_message
                }
            ]
        });
        
        // Start execution
        let result = self.sfn
            .start_execution()
            .state_machine_arn(&state_machine_arn)
            .name(&execution_name)
            .input(serde_json::to_string(&input)?)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to start execution: {}", e))?;
            
        let execution_arn = result.execution_arn;
            
        info!("Started execution: {}", execution_arn);
        
        // Generate execution ID (short form)
        let execution_id = execution_arn.split(':').last()
            .unwrap_or(&execution_name)
            .to_string();
        
        Ok(StartExecutionResponse {
            execution_id,
            execution_arn,
            execution_name,
            status: "RUNNING".to_string(),
            estimated_duration_seconds: 60, // Default estimate
        })
    }
    
    /// Get execution status with detailed information
    pub async fn get_execution_status(&self, execution_arn: &str) -> Result<ExecutionInfo> {
        info!("Getting status for execution: {}", execution_arn);
        
        let result = self.sfn
            .describe_execution()
            .execution_arn(execution_arn)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to describe execution: {}", e))?;
        
        // Convert status to string
        let status = match result.status {
            aws_sdk_sfn::types::ExecutionStatus::Running => "RUNNING",
            aws_sdk_sfn::types::ExecutionStatus::Succeeded => "SUCCEEDED",
            aws_sdk_sfn::types::ExecutionStatus::Failed => "FAILED",
            aws_sdk_sfn::types::ExecutionStatus::TimedOut => "TIMED_OUT",
            aws_sdk_sfn::types::ExecutionStatus::Aborted => "ABORTED",
            aws_sdk_sfn::types::ExecutionStatus::PendingRedrive => "PENDING_REDRIVE",
            _ => "UNKNOWN",
        }.to_string();
        
        // Parse timestamps - AWS SDK returns DateTime directly for start_date, Option<DateTime> for stop_date
        let start_time = Some(DateTime::<Utc>::from_timestamp(result.start_date.secs(), 0)
            .unwrap_or_else(|| Utc::now()));
        
        let end_time = result.stop_date.map(|dt| {
            DateTime::<Utc>::from_timestamp(dt.secs(), 0)
                .unwrap_or_else(|| Utc::now())
        });
        
        let execution_name = execution_arn.split(':').last()
            .unwrap_or("unknown")
            .to_string();
        
        // Parse input and output as JSON
        let input = result.input.as_ref().and_then(|s| serde_json::from_str(s).ok());
        let output = result.output.as_ref().and_then(|s| serde_json::from_str(s).ok());
        
        info!("Execution status: {}, has output: {}", status, output.is_some());
        if let Some(ref out) = output {
            info!("Output preview: {}", serde_json::to_string(out).unwrap_or_default());
        }
        
        Ok(ExecutionInfo {
            execution_arn: execution_arn.to_string(),
            execution_name,
            status,
            start_time,
            end_time,
            input,
            output,
            error: result.error,
        })
    }
    
    /// List available agents from registry
    pub async fn list_available_agents(&self) -> Result<Vec<Agent>> {
        info!("Listing available agents from registry");
        
        // If GraphQL endpoint is configured, use it
        if let (Some(endpoint), Some(api_key)) = (&self.graphql_endpoint, &self.api_key) {
            info!("Using GraphQL API to list agents");
            info!("GraphQL endpoint: {}", endpoint);
            // Log API key length for security (not the actual key)
            info!("API key length: {}", api_key.len());
            
            let query = r#"
                query ListAgentsFromRegistry {
                    listAgentsFromRegistry {
                        id
                        name
                        description
                        version
                        type
                        createdAt
                        tools
                        systemPrompt
                        llmProvider
                        llmModel
                        status
                        parameters
                        metadata
                    }
                }
            "#;
            
            let client = reqwest::Client::new();
            
            // Try with x-api-key header (AppSync expects this exact header name)
            let mut request = client
                .post(endpoint)
                .header("Content-Type", "application/json");
                
            // Only add API key header if it's not empty
            if !api_key.is_empty() {
                request = request.header("x-api-key", api_key);
            } else {
                info!("Warning: API key is empty, request may fail");
            }
            
            let response = request
                .json(&json!({
                    "query": query
                }))
                .send()
                .await
                .map_err(|e| anyhow!("Failed to query GraphQL API: {}", e))?;
                
            let response_text = response.text().await
                .map_err(|e| anyhow!("Failed to read GraphQL response: {}", e))?;
            
            info!("GraphQL response: {}", response_text);
            
            let json: Value = serde_json::from_str(&response_text)
                .map_err(|e| anyhow!("Failed to parse GraphQL response: {}", e))?;
                
            // Check for errors in GraphQL response
            if let Some(errors) = json["errors"].as_array() {
                if !errors.is_empty() {
                    let error_msg = errors.iter()
                        .filter_map(|e| e["message"].as_str())
                        .collect::<Vec<_>>()
                        .join(", ");
                    return Err(anyhow!("GraphQL errors: {}", error_msg));
                }
            }
                
            // Extract agents from GraphQL response
            let agents_data = json["data"]["listAgentsFromRegistry"]
                .as_array()
                .ok_or_else(|| anyhow!("Invalid GraphQL response format. Response: {}", json))?;
                
            let mut agents = Vec::new();
            for agent_json in agents_data {
                if let Ok(agent) = serde_json::from_value::<Agent>(agent_json.clone()) {
                    agents.push(agent);
                }
            }
            
            info!("Found {} agents from GraphQL API", agents.len());
            return Ok(agents);
        }
        
        // Fallback to direct DynamoDB scan (with corrected field names)
        info!("Using direct DynamoDB scan");
        let table_name = format!("AgentRegistry-{}", self.environment);
        
        let result = self.dynamodb
            .scan()
            .table_name(table_name)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to scan agent registry: {}", e))?;
        
        let mut agents = Vec::new();
        
        if let Some(items) = result.items {
            for item in items {
                if let Ok(agent) = self.parse_agent_record(item) {
                    agents.push(agent);
                }
            }
        }
        
        info!("Found {} agents in registry", agents.len());
        Ok(agents)
    }
    
    /// Parse agent record from DynamoDB item
    fn parse_agent_record(&self, item: HashMap<String, AttributeValue>) -> Result<Agent> {
        // Try to get agent_name (actual field) or name (for compatibility)
        let name = item.get("agent_name")
            .or_else(|| item.get("name"))
            .and_then(|v| v.as_s().ok())
            .ok_or_else(|| anyhow!("Missing agent name"))?
            .to_string();
            
        let id = item.get("id")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string())
            .unwrap_or_else(|| name.clone());
            
        let description = item.get("description")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string());
            
        let version = item.get("version")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string())
            .unwrap_or_else(|| "1.0".to_string());
            
        let status = item.get("status")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string())
            .unwrap_or_else(|| "unknown".to_string());
        
        // Try to construct state machine ARN from agent name
        let account_id = std::env::var("AWS_ACCOUNT_ID").unwrap_or_else(|_| "123456789012".to_string());
        let region = std::env::var("AWS_DEFAULT_REGION").unwrap_or_else(|_| "us-east-1".to_string());
        let environment = std::env::var("ENVIRONMENT").unwrap_or_else(|_| "prod".to_string());
        
        // State machines follow the pattern: {agent-name}-{environment}
        let state_machine_name = format!("{}-{}", name, environment);
        let state_machine_arn = Some(format!(
            "arn:aws:states:{}:{}:stateMachine:{}",
            region,
            account_id,
            state_machine_name
        ));
        
        let tools = item.get("tools")
            .and_then(|v| v.as_ss().ok())
            .map(|ss| ss.iter().cloned().collect())
            .unwrap_or_else(|| vec!["general".to_string()]);
            
        let llm_provider = item.get("llmProvider")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string());
            
        let llm_model = item.get("llmModel")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string());
            
        let system_prompt = item.get("systemPrompt")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string());
            
        let parameters = item.get("parameters")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string());
            
        let metadata = item.get("metadata")
            .and_then(|v| v.as_s().ok())
            .map(|s| s.to_string());
        
        Ok(Agent {
            id,
            name,
            description,
            version,
            status,
            state_machine_arn,
            tools,
            llm_provider,
            llm_model,
            system_prompt,
            parameters,
            metadata,
        })
    }
}