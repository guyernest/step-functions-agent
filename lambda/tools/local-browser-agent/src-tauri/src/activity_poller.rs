use anyhow::{Context, Result};
use aws_sdk_sfn::Client as SfnClient;
use log::{info, warn, error, debug};
use serde_json::Value;
use std::sync::Arc;
use parking_lot::RwLock;
use tokio::time::{interval, Duration};
use chrono::Utc;

use crate::config::Config;
use crate::nova_act_executor::NovaActExecutor;
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
    executor: Arc<NovaActExecutor>,
    session_manager: Arc<RwLock<SessionManager>>,
    status: Arc<RwLock<PollerStatus>>,
    current_task: Arc<RwLock<Option<String>>>,
}

impl ActivityPoller {
    /// Create a new activity poller
    pub async fn new(
        config: Arc<Config>,
        executor: Arc<NovaActExecutor>,
        session_manager: Arc<RwLock<SessionManager>>,
    ) -> Result<Self> {
        // Load AWS config
        let aws_config = aws_config::from_env()
            .profile_name(&config.aws_profile)
            .load()
            .await;

        let sfn_client = SfnClient::new(&aws_config);

        info!("Activity poller initialized for ARN: {}", config.activity_arn);

        Ok(Self {
            config,
            sfn_client,
            executor,
            session_manager,
            status: Arc::new(RwLock::new(PollerStatus::Idle)),
            current_task: Arc::new(RwLock::new(None)),
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
                    error!("Error polling for task: {}", e);
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
            .context("Failed to poll for activity task")?;

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

        // Extract prompt for display
        let prompt = tool_params.get("prompt")
            .and_then(|v| v.as_str())
            .unwrap_or("Unknown task");

        *self.current_task.write() = Some(prompt.to_string());

        info!("Executing task: {}", prompt);

        // Start heartbeat task
        let heartbeat_handle = self.start_heartbeat_task(task_token.clone());

        // Execute Nova Act command
        let result = self.executor.execute(tool_params).await;

        // Cancel heartbeat
        heartbeat_handle.abort();

        // Wrap result in the expected format (matching local agent pattern)
        match result {
            Ok(nova_act_output) => {
                // Check if Nova Act execution was successful
                let execution_success = nova_act_output.get("success")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);

                if execution_success {
                    // Build response in the same format as local agent
                    let wrapped_response = serde_json::json!({
                        "tool_name": original_input.get("tool_name").unwrap_or(&serde_json::json!("browser_remote")),
                        "tool_use_id": original_input.get("tool_use_id").unwrap_or(&serde_json::json!("")),
                        "tool_input": {
                            "script_output": nova_act_output
                        },
                        "timestamp": original_input.get("timestamp").unwrap_or(&serde_json::json!(Utc::now().to_rfc3339())),
                        "context": original_input.get("context").unwrap_or(&serde_json::json!({})),
                        "approved": true
                    });

                    debug!("Wrapped response: {}", serde_json::to_string_pretty(&wrapped_response).unwrap_or_else(|_| "{}".to_string()));

                    self.send_task_success(&task_token, wrapped_response).await?;
                } else {
                    // Nova Act execution failed - extract error message
                    let error_msg = nova_act_output.get("error")
                        .and_then(|v| v.as_str())
                        .unwrap_or("Unknown browser automation error");

                    error!("Nova Act execution failed: {}", error_msg);
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
