use anyhow::{Context, Result};
use aws_sdk_sfn::Client as SfnClient;
use log::{info, warn, error, debug};
use serde_json::Value;
use std::sync::Arc;
use parking_lot::RwLock;
use tokio::time::{interval, Duration};
use chrono::Utc;

use crate::config::Config;
use crate::script_executor::{PersistentScriptExecutor, ScriptExecutor, ScriptExecutionConfig};
use crate::session_manager::SessionManager;

/// Status of the activity poller
#[derive(Debug, Clone, PartialEq)]
pub enum PollerStatus {
    Idle,
    Polling,
    ExecutingTask,
    SendingHeartbeat,
    Error(String),
}

/// Activity poller that polls Step Functions for browser automation tasks
pub struct ActivityPoller {
    config: Arc<Config>,
    sfn_client: SfnClient,
    script_executor: ScriptExecutor,
    session_manager: Arc<RwLock<SessionManager>>,
    status: Arc<RwLock<PollerStatus>>,
    current_task: Arc<RwLock<Option<String>>>,
    /// Persistent browser session (initialized lazily on first task when enabled)
    persistent_executor: tokio::sync::Mutex<Option<PersistentScriptExecutor>>,
}

impl ActivityPoller {
    /// Create a new activity poller
    pub async fn new(
        config: Arc<Config>,
        session_manager: Arc<RwLock<SessionManager>>,
    ) -> Result<Self> {
        // Load AWS config
        info!("Loading AWS config for profile: {}", config.aws_profile);
        let aws_config = aws_config::from_env()
            .profile_name(&config.aws_profile)
            .load()
            .await;
        info!("AWS config loaded successfully");

        info!("Creating SFN client...");
        let sfn_client = SfnClient::new(&aws_config);
        info!("SFN client created");

        // Create unified script executor (respects browser_engine config)
        info!("Creating ScriptExecutor...");
        let script_executor = ScriptExecutor::new(Arc::clone(&config))?;
        info!("ScriptExecutor created successfully");

        info!("Activity poller initialized for ARN: {}", config.activity_arn);
        info!("Using browser engine: {}", config.browser_engine);
        info!("Building ActivityPoller struct...");

        Ok(Self {
            config,
            sfn_client,
            script_executor,
            session_manager,
            status: Arc::new(RwLock::new(PollerStatus::Idle)),
            current_task: Arc::new(RwLock::new(None)),
            persistent_executor: tokio::sync::Mutex::new(None),
        })
    }

    /// Get current poller status
    pub fn get_status(&self) -> PollerStatus {
        self.status.read().clone()
    }

    /// Get current task description
    pub fn get_current_task(&self) -> Option<String> {
        self.current_task.read().clone()
    }

    /// Start polling for tasks
    pub async fn start_polling(&self) -> Result<()> {
        info!("Starting Activity polling loop...");
        info!("Configuration:");
        info!("  Activity ARN: {}", self.config.activity_arn);
        info!("  AWS Profile: {}", self.config.aws_profile);
        info!("  Worker Name: local-browser-agent");
        info!("  Heartbeat Interval: {}s", self.config.heartbeat_interval);

        loop {
            // Update status
            *self.status.write() = PollerStatus::Polling;
            *self.current_task.write() = None;

            // Poll for task
            match self.poll_for_task().await {
                Ok(Some((task_token, input))) => {
                    info!("Received task from Activity");

                    // Update status
                    *self.status.write() = PollerStatus::ExecutingTask;

                    // Execute task
                    match self.execute_task(task_token, input).await {
                        Ok(_) => {
                            info!("Task completed successfully");
                        }
                        Err(e) => {
                            error!("Task execution failed: {}", e);
                            *self.status.write() = PollerStatus::Error(e.to_string());
                        }
                    }
                }
                Ok(None) => {
                    // No task available, continue polling
                    debug!("No task available, continuing polling...");
                }
                Err(e) => {
                    // Error already logged in poll_for_task with details
                    error!("Error polling for task: {}", e);

                    // Provide troubleshooting hints based on common errors
                    let error_str = e.to_string();
                    if error_str.contains("AccessDenied") || error_str.contains("UnauthorizedOperation") {
                        error!("TROUBLESHOOTING: This is a permission error. Check that:");
                        error!("  1. Your AWS credentials have 'states:GetActivityTask' permission");
                        error!("  2. The IAM policy allows access to this Activity ARN");
                        error!("  3. The AWS profile '{}' has the correct permissions", self.config.aws_profile);
                    } else if error_str.contains("InvalidArn") || error_str.contains("does not exist") {
                        error!("TROUBLESHOOTING: The Activity ARN appears to be invalid or doesn't exist:");
                        error!("  1. Verify the Activity ARN in your configuration");
                        error!("  2. Ensure the Activity exists in the AWS region");
                        error!("  3. Check the ARN format matches: arn:aws:states:region:account:activity:name");
                    } else if error_str.contains("timeout") || error_str.contains("timed out") {
                        error!("TROUBLESHOOTING: Network timeout error:");
                        error!("  1. Check your internet connection");
                        error!("  2. Verify AWS region is reachable");
                        error!("  3. Check firewall/proxy settings");
                    } else if error_str.contains("NoCredentials") || error_str.contains("CredentialsNotFound") {
                        error!("TROUBLESHOOTING: AWS credentials not found:");
                        error!("  1. Check that AWS profile '{}' exists in ~/.aws/credentials", self.config.aws_profile);
                        error!("  2. Run 'aws configure --profile {}' to set up credentials", self.config.aws_profile);
                        error!("  3. Or use 'assume {}' if using assume role", self.config.aws_profile);
                    }

                    *self.status.write() = PollerStatus::Error(e.to_string());

                    // Wait before retrying
                    tokio::time::sleep(Duration::from_secs(10)).await;
                }
            }
        }
    }

    /// Poll for a single task
    async fn poll_for_task(&self) -> Result<Option<(String, String)>> {
        debug!("Polling for task from Activity ARN: {}", self.config.activity_arn);

        let response = self.sfn_client
            .get_activity_task()
            .activity_arn(&self.config.activity_arn)
            .worker_name("local-browser-agent")
            .send()
            .await
            .map_err(|e| {
                // Extract detailed error information from AWS SDK
                let error_msg = if let Some(service_err) = e.as_service_error() {
                    // Get the error code and message from the service error
                    format!("AWS Step Functions error: {} - {}",
                        service_err.meta().code().unwrap_or("Unknown"),
                        service_err.meta().message().unwrap_or("No message"))
                } else {
                    // Network, timeout, or other SDK errors
                    format!("SDK error: {}", e)
                };

                // Log the detailed error
                error!("Failed to poll for activity task: {}", error_msg);
                error!("  Activity ARN: {}", self.config.activity_arn);
                error!("  AWS Profile: {}", self.config.aws_profile);

                // Return anyhow error with details
                anyhow::anyhow!("{}", error_msg)
            })?;

        // Check if we got a task (following local-agent pattern)
        if let (Some(task_token), Some(input)) = (response.task_token(), response.input()) {
            if !task_token.is_empty() {
                info!("Received task token");
                return Ok(Some((task_token.to_string(), input.to_string())));
            }
        }

        Ok(None)
    }

    /// Execute a task
    async fn execute_task(&self, task_token: String, input_str: String) -> Result<()> {

        // Parse input - this is the full Step Functions payload
        let original_input: Value = serde_json::from_str(&input_str)
            .context("Failed to parse task input as JSON")?;

        debug!("Received task input: {}", serde_json::to_string_pretty(&original_input).unwrap_or_else(|_| input_str.clone()));

        // Extract the actual tool parameters from tool_input field
        let tool_params = if let Some(tool_input) = original_input.get("tool_input") {
            info!("Unwrapping tool_input from Step Functions Activity payload");
            tool_input.clone()
        } else {
            original_input.clone()
        };

        debug!("Extracted parameters: {}", serde_json::to_string_pretty(&tool_params).unwrap_or_else(|_| "{}".to_string()));

        // Extract task description for display
        // Priority: name > description > prompt > "Unknown task"
        let task_description = tool_params.get("name")
            .and_then(|v| v.as_str())
            .or_else(|| tool_params.get("description").and_then(|v| v.as_str()))
            .or_else(|| tool_params.get("prompt").and_then(|v| v.as_str()))
            .unwrap_or("Unknown task");

        *self.current_task.write() = Some(task_description.to_string());

        info!("Executing task: {}", task_description);

        // Start heartbeat task
        let heartbeat_handle = self.start_heartbeat_task(task_token.clone());

        // Convert tool_params to script JSON string for unified executor
        let script_content = serde_json::to_string(&tool_params)
            .context("Failed to serialize script")?;

        // Execute using persistent or one-shot executor based on config
        let result = if self.config.persistent_browser_session {
            self.execute_with_persistent_session(&script_content).await
        } else {
            let exec_config = ScriptExecutionConfig {
                script_content,
                aws_profile: self.config.aws_profile.clone(),
                s3_bucket: Some(self.config.s3_bucket.clone()),
                headless: self.config.headless,
                browser_channel: self.config.browser_channel.clone(),
                navigation_timeout: 60000,
                user_data_dir: None,
            };
            self.script_executor.execute(exec_config).await
        };

        // Cancel heartbeat
        heartbeat_handle.abort();

        // Wrap result in the expected format (matching local agent pattern)
        match result {
            Ok(execution_result) => {
                if execution_result.success {
                    // Parse output as JSON if possible
                    let script_output: Value = if let Some(ref output) = execution_result.output {
                        serde_json::from_str(output).unwrap_or_else(|_| {
                            serde_json::json!({"raw_output": output})
                        })
                    } else {
                        serde_json::json!({"success": true})
                    };

                    // Build response in the same format as local agent
                    let wrapped_response = serde_json::json!({
                        "tool_name": original_input.get("tool_name").unwrap_or(&serde_json::json!("browser_remote")),
                        "tool_use_id": original_input.get("tool_use_id").unwrap_or(&serde_json::json!("")),
                        "tool_input": {
                            "script_output": script_output
                        },
                        "timestamp": original_input.get("timestamp").unwrap_or(&serde_json::json!(Utc::now().to_rfc3339())),
                        "context": original_input.get("context").unwrap_or(&serde_json::json!({})),
                        "approved": true
                    });

                    debug!("Wrapped response: {}", serde_json::to_string_pretty(&wrapped_response).unwrap_or_else(|_| "{}".to_string()));

                    self.send_task_success(&task_token, wrapped_response).await?;
                } else {
                    // Execution failed - extract error message
                    let error_msg = execution_result.error
                        .as_deref()
                        .unwrap_or("Unknown browser automation error");

                    error!("Script execution failed: {}", error_msg);
                    self.send_task_failure(&task_token, error_msg.to_string()).await?;
                }
            }
            Err(e) => {
                // Rust executor error (not Nova Act error)
                error!("Executor error: {}", e);
                self.send_task_failure(&task_token, e.to_string()).await?;
            }
        }

        Ok(())
    }

    /// Execute a script using the persistent browser session.
    ///
    /// Lazily starts the persistent executor on the first call.
    /// If the persistent executor has died, restarts it.
    async fn execute_with_persistent_session(
        &self,
        script_content: &str,
    ) -> Result<crate::script_executor::ExecutionResult> {
        let mut guard = self.persistent_executor.lock().await;

        // Check if we need to start or restart the persistent session
        let needs_start = match guard.as_mut() {
            None => true,
            Some(executor) => !executor.is_running(),
        };

        if needs_start {
            if guard.is_some() {
                info!("Persistent session died, restarting...");
                // Try to clean up the dead session
                if let Some(mut old) = guard.take() {
                    let _ = old.stop().await;
                }
            } else {
                info!("Starting persistent browser session for first task...");
            }

            let exec_config = ScriptExecutionConfig {
                script_content: script_content.to_string(),
                aws_profile: self.config.aws_profile.clone(),
                s3_bucket: Some(self.config.s3_bucket.clone()),
                headless: self.config.headless,
                browser_channel: self.config.browser_channel.clone(),
                navigation_timeout: 60000,
                user_data_dir: None,
            };

            let (executor, first_result) = PersistentScriptExecutor::start(
                Arc::clone(&self.config),
                exec_config,
            )
            .await
            .context("Failed to start persistent browser session")?;

            *guard = Some(executor);

            // Return the result of the first script execution
            return Ok(first_result);
        }

        // Use existing persistent session
        let executor = guard.as_mut().unwrap();
        executor.execute(script_content).await
    }

    /// Start heartbeat task
    fn start_heartbeat_task(&self, task_token: String) -> tokio::task::JoinHandle<()> {
        let sfn_client = self.sfn_client.clone();
        let heartbeat_interval = self.config.heartbeat_interval;
        let status = Arc::clone(&self.status);

        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(heartbeat_interval));

            loop {
                interval.tick().await;

                *status.write() = PollerStatus::SendingHeartbeat;

                debug!("Sending heartbeat for task: {}", task_token);

                match sfn_client
                    .send_task_heartbeat()
                    .task_token(&task_token)
                    .send()
                    .await
                {
                    Ok(_) => {
                        debug!("Heartbeat sent successfully");
                        *status.write() = PollerStatus::ExecutingTask;
                    }
                    Err(e) => {
                        warn!("Failed to send heartbeat: {}", e);
                        break;
                    }
                }
            }
        })
    }

    /// Send task success
    async fn send_task_success(&self, task_token: &str, output: Value) -> Result<()> {
        let output_str = serde_json::to_string(&output)
            .context("Failed to serialize output")?;

        self.sfn_client
            .send_task_success()
            .task_token(task_token)
            .output(output_str)
            .send()
            .await
            .context("Failed to send task success")?;

        info!("Task success sent to Step Functions");

        Ok(())
    }

    /// Send task failure
    async fn send_task_failure(&self, task_token: &str, error: String) -> Result<()> {
        self.sfn_client
            .send_task_failure()
            .task_token(task_token)
            .error("BrowserAutomationError")
            .cause(error)
            .send()
            .await
            .context("Failed to send task failure")?;

        warn!("Task failure sent to Step Functions");

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_poller_status() {
        let status = PollerStatus::Idle;
        assert_eq!(status, PollerStatus::Idle);

        let error_status = PollerStatus::Error("test error".to_string());
        match error_status {
            PollerStatus::Error(msg) => assert_eq!(msg, "test error"),
            _ => panic!("Expected error status"),
        }
    }
}
