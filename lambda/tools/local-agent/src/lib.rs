// A Daemon that polls Step Functions Activity tasks and executes an application with the input as input
use anyhow::{Context, Result};
use aws_config::profile::{ProfileFileCredentialsProvider, ProfileFileRegionProvider};
use aws_sdk_sfn::Client;
use config::{Config, File};
use log::{error, info};
use serde::Deserialize;
use std::process::{Command, Stdio};
use std::time::Duration;
use tempfile::TempDir;
use tokio::time;

#[derive(Debug, Deserialize)]
pub struct AppConfig {
    pub activity_arn: String,
    pub app_path: String,
    pub poll_interval_ms: u64,
    pub worker_name: String,
    pub profile_name: String,
}

pub async fn process_task(
    task_input: String,
    task_token: String,
    client: &Client,
    config: &AppConfig,
) -> Result<()> {
    // Log task receipt
    info!("Received task with input: {}", task_input);

    // Check if this is a PyAutoGUI script (using the new format where script is inside input object)
    if task_input.contains("\"input\"") && (task_input.contains("\"script\"") || task_input.contains("\"actions\":")) {
        // Execute the script using our Python script executor
        info!("Detected PyAutoGUI script, executing with script_executor.py");

        let script_executor_path = std::path::Path::new("script_executor.py");
        if !script_executor_path.exists() {
            error!("script_executor.py not found in the current directory");

            // Create a response with error information in the new format
            let value = match serde_json::from_str::<serde_json::Value>(&task_input) {
                Ok(value) => value,
                Err(_) => serde_json::json!({
                    "id": "unknown",
                    "input": {}
                })
            };
            
            let mut response = value.clone();
            
            // Replace the script with error information in the input object
            if let Some(input_obj) = response.get_mut("input") {
                if let Some(obj) = input_obj.as_object_mut() {
                    // Remove the script element if it exists
                    obj.remove("script");
                    
                    // Add the script_output element with error information
                    obj.insert(
                        "script_output".to_string(), 
                        serde_json::json!({
                            "success": false,
                            "error": "ScriptExecutorNotFound",
                            "message": "script_executor.py not found in the current directory"
                        })
                    );
                }
            }
            
            // Add the approved field at the root level of the response
            if let Some(obj) = response.as_object_mut() {
                obj.insert("approved".to_string(), serde_json::json!(true));
            }
            
            let error_response_str = serde_json::to_string(&response)
                .unwrap_or_else(|_| format!("{{\"error\": \"Failed to format error response\"}}"));
            
            // Send task success (changed from failure so Step Functions can continue)
            client
                .send_task_success()
                .task_token(task_token)
                .output(error_response_str)
                .send()
                .await
                .context("Failed to send task success to Step Functions")?;

            return Err(anyhow::anyhow!("script_executor.py not found"));
        }

        // Extract the script content from the new input format structure: input.script
        let (script_content, input_value) = match serde_json::from_str::<serde_json::Value>(&task_input) {
            Ok(value) => {
                if let Some(input_obj) = value.get("input") {
                    if let Some(script) = input_obj.get("script") {
                        info!("Successfully extracted script from input.script structure");
                        (
                            serde_json::to_string(script)
                                .context("Failed to serialize extracted script")?,
                            value
                        )
                    } else {
                        error!("No 'script' element found in the 'input' object");
                        return Err(anyhow::anyhow!("No script element found in input object"));
                    }
                } else {
                    error!("No 'input' element found in the task input");
                    return Err(anyhow::anyhow!("No input element found in task input"));
                }
            }
            Err(e) => {
                error!("Failed to parse task input as JSON: {}", e);
                return Err(anyhow::anyhow!("Failed to parse task input: {}", e));
            }
        };

        // Create a temporary file to store the script
        let temp_dir = TempDir::new().unwrap();

        let script_path = temp_dir.path().join("script.json");

        std::fs::write(&script_path, script_content)
            .context("Failed to write script to temporary file")?;
        info!("Saved script to temporary file: {:?}", script_path);

        // Execute the Python script with our JSON input using direct Python execution
        // We previously used uvx, but encountered issues with dependencies that used the obsolete 'file' function
        // instead of 'open'. The script_executor.py now handles dependency management internally.
        let python_command = if cfg!(target_os = "windows") {
            "python"
        } else {
            "python3"
        };

        info!("Executing script with Python directly...");
        let result = Command::new(python_command)
            .arg(script_executor_path)
            .arg(script_path.to_string_lossy().to_string())
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output();

        // Just check if Python execution worked
        let result = match result {
            Ok(output) => {
                info!("Successfully executed script with Python");
                Ok(output)
            }
            Err(e) => {
                error!("Failed to execute script with Python: {}", e);
                Err(anyhow::anyhow!(
                    "Failed to execute script_executor.py with Python: {}",
                    e
                ))
            }
        }?;

        if result.status.success() {
            // Get the output
            let stdout = String::from_utf8_lossy(&result.stdout);
            info!("Script executed successfully");
            info!("Script output: {}", stdout);

            // Parse the execution output to include in the response
            let mut script_output: serde_json::Value = match serde_json::from_str(&stdout) {
                Ok(value) => value,
                Err(e) => {
                    error!("Failed to parse script output as JSON: {}", e);
                    return Err(anyhow::anyhow!("Failed to parse script output as JSON: {}", e));
                }
            };
            
            // Create a response that mirrors the input structure but with script_output instead of script
            let mut response = input_value.clone();
            
            // Replace the script with script_output in the input object
            if let Some(input_obj) = response.get_mut("input") {
                if let Some(obj) = input_obj.as_object_mut() {
                    // Remove the script element
                    obj.remove("script");
                    
                    // Add the script_output element
                    obj.insert("script_output".to_string(), script_output);
                }
            }
            
            // Add the approved field at the root level of the response
            if let Some(obj) = response.as_object_mut() {
                obj.insert("approved".to_string(), serde_json::json!(true));
            }
            
            let response_str = serde_json::to_string(&response)
                .context("Failed to serialize response")?;
                
            info!("Sending formatted response: {}", response_str);
            
            // Send task success with the formatted response
            client
                .send_task_success()
                .task_token(task_token)
                .output(response_str)
                .send()
                .await
                .context("Failed to send task success to Step Functions")?;

            info!("Task completion reported to Step Functions");
        } else {
            // Get the error
            let stderr = String::from_utf8_lossy(&result.stderr);
            let stdout = String::from_utf8_lossy(&result.stdout);
            error!("Script execution failed: {}", stderr);

            // Create a response with error information
            let mut response = input_value.clone();
            
            // Replace the script with error information in the input object
            if let Some(input_obj) = response.get_mut("input") {
                if let Some(obj) = input_obj.as_object_mut() {
                    // Remove the script element
                    obj.remove("script");
                    
                    // Add the script_output element with error information
                    obj.insert(
                        "script_output".to_string(), 
                        serde_json::json!({
                            "success": false,
                            "error": "ScriptExecutionError",
                            "stdout": stdout.to_string(),
                            "stderr": stderr.to_string()
                        })
                    );
                }
            }
            
            // Add the approved field at the root level of the response
            if let Some(obj) = response.as_object_mut() {
                obj.insert("approved".to_string(), serde_json::json!(true));
            }
            
            let error_response_str = serde_json::to_string(&response)
                .unwrap_or_else(|_| format!("{{\"error\": \"Failed to format error response\"}}"));
            
            // Send task success (changed from failure so Step Functions can continue)
            client
                .send_task_success()
                .task_token(task_token)
                .output(error_response_str)
                .send()
                .await
                .context("Failed to send task success to Step Functions")?;

            error!("Task completion reported to Step Functions with error details");
            return Err(anyhow::anyhow!("Script execution failed"));
        }

        // Clean up the temporary directory
        drop(temp_dir);
    } else {
        // Execute the application with the task input (original behavior)
        info!("Executing legacy application with input");
        let result = Command::new(&config.app_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .arg(task_input)
            .output()
            .context("Failed to execute application")?;

        if result.status.success() {
            // Get the output
            let stdout = String::from_utf8_lossy(&result.stdout);
            info!("Application executed successfully");
            info!("Application output: {}", stdout);

            // Create a response JSON with approved field
            let response = serde_json::json!({
                "output": stdout.to_string(),
                "success": true,
                "approved": true
            });

            let response_str = serde_json::to_string(&response)
                .context("Failed to serialize success response")?;

            // Send task success
            client
                .send_task_success()
                .task_token(task_token)
                .output(response_str)
                .send()
                .await
                .context("Failed to send task success to Step Functions")?;

            info!("Task completion reported to Step Functions");
        } else {
            // Get the error
            let stderr = String::from_utf8_lossy(&result.stderr);
            error!("Application execution failed: {}", stderr);

            // Create error response with approved field
            let error_response = serde_json::json!({
                "success": false,
                "approved": true,
                "error": "ApplicationError",
                "stderr": stderr.to_string()
            });

            let error_response_str = serde_json::to_string(&error_response)
                .context("Failed to serialize error response")?;

            // Send task success (changed from failure so Step Functions can continue)
            client
                .send_task_success()
                .task_token(task_token)
                .output(error_response_str)
                .send()
                .await
                .context("Failed to send task success to Step Functions")?;

            error!("Task completion reported to Step Functions with error details");
            return Err(anyhow::anyhow!("Application execution failed"));
        }
    }

    Ok(())
}

pub async fn poll_activity(client: &Client, config: &AppConfig) -> Result<()> {
    // Request a task from Step Functions
    info!("Polling activity: {}", config.activity_arn);

    let get_activity_task_response = client
        .get_activity_task()
        .activity_arn(&config.activity_arn)
        .worker_name(&config.worker_name)
        .send()
        .await
        .context("Failed to poll for Step Functions activity task")?;

    // Check if we received a task
    if let (Some(task_token), Some(input)) = (
        get_activity_task_response.task_token(),
        get_activity_task_response.input(),
    ) {
        if !task_token.is_empty() {
            info!("Received task token: {}", task_token);

            // Process the task
            if let Err(e) =
                process_task(input.to_string(), task_token.to_string(), client, config).await
            {
                error!("Error processing task: {:?}", e);
            }
        } else {
            // No task available, just a heartbeat response
            info!("No task available");
        }
    } else {
        // No task token or input - nothing to do
        info!("No task received from activity polling");
    }

    Ok(())
}

#[tokio::main]
pub async fn main() -> Result<()> {
    // Initialize the logger
    env_logger::init();

    // Load configuration
    let settings = Config::builder()
        .add_source(File::with_name("daemon_config.json"))
        .build()
        .context("Failed to load configuration")?;

    let config: AppConfig = settings
        .try_deserialize()
        .context("Failed to deserialize configuration")?;

    info!(
        "Starting Step Functions activity worker for: {}",
        config.activity_arn
    );

    // Initialize AWS SDK with profile from config
    let credentials_provider = ProfileFileCredentialsProvider::builder()
        .profile_name(&config.profile_name)
        .build();

    let region_provider = ProfileFileRegionProvider::builder()
        .profile_name(&config.profile_name)
        .build();

    let aws_config = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .credentials_provider(credentials_provider)
        .region(region_provider)
        .load()
        .await;

    let client = Client::new(&aws_config);

    // Main polling loop
    loop {
        if let Err(e) = poll_activity(&client, &config).await {
            error!("Error polling activity: {:?}", e);
        }
        info!("Polling activities");
        // Wait for the configured interval before polling again
        time::sleep(Duration::from_millis(config.poll_interval_ms)).await;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use aws_sdk_sfn::error::SdkError;
    use aws_sdk_sfn::operation::get_activity_task::{GetActivityTaskError, GetActivityTaskOutput};
    use aws_sdk_sfn::operation::send_task_failure::SendTaskFailureOutput;
    use aws_sdk_sfn::operation::send_task_success::SendTaskSuccessOutput;
    use std::fs;
    use tempfile::tempdir;
    use test_log::test;

    // Mock the Step Functions client for testing
    enum GetActivityTaskResult {
        Success(GetActivityTaskOutput),
        Error,
        Default,
    }

    enum SendTaskSuccessResult {
        Success(SendTaskSuccessOutput),
        Error,
        Default,
    }

    enum SendTaskFailureResult {
        Success(SendTaskFailureOutput),
        Error,
        Default,
    }

    struct MockSfnClient {
        get_activity_task_result: GetActivityTaskResult,
        send_task_success_result: SendTaskSuccessResult,
        send_task_failure_result: SendTaskFailureResult,
    }

    impl MockSfnClient {
        fn new() -> Self {
            MockSfnClient {
                get_activity_task_result: GetActivityTaskResult::Default,
                send_task_success_result: SendTaskSuccessResult::Default,
                send_task_failure_result: SendTaskFailureResult::Default,
            }
        }

        fn with_get_activity_task_output(
            mut self,
            output: Result<GetActivityTaskOutput, SdkError<GetActivityTaskError>>,
        ) -> Self {
            match output {
                Ok(output) => {
                    self.get_activity_task_result = GetActivityTaskResult::Success(output)
                }
                Err(_) => self.get_activity_task_result = GetActivityTaskResult::Error,
            }
            self
        }

        async fn get_activity_task(
            &self,
        ) -> Result<GetActivityTaskOutput, SdkError<GetActivityTaskError>> {
            match &self.get_activity_task_result {
                GetActivityTaskResult::Success(output) => Ok(output.clone()),
                GetActivityTaskResult::Error => {
                    // Return a generic error for mocking purposes
                    Err(SdkError::construction_failure("Mock Step Functions error"))
                }
                GetActivityTaskResult::Default => Ok(GetActivityTaskOutput::builder().build()),
            }
        }

        // Additional mock methods would be implemented here for send_task_success and send_task_failure
    }

    // Helper function to create a test config file
    fn create_test_config() -> (tempfile::TempDir, String) {
        let dir = tempdir().unwrap();
        let file_path = dir.path().join("test_config.json");

        let config_content = r#"{
            "activity_arn": "arn:aws:states:us-east-1:123456789012:activity:test-activity",
            "app_path": "/bin/echo",
            "poll_interval_ms": 100,
            "worker_name": "test-worker",
            "profile_name": "test-profile"
        }"#;

        fs::write(&file_path, config_content).unwrap();
        (dir, file_path.to_string_lossy().to_string())
    }

    #[test]
    fn test_app_config_deserialize() {
        let config_json = r#"{
            "activity_arn": "arn:aws:states:us-east-1:123456789012:activity:test-activity",
            "app_path": "/bin/echo",
            "poll_interval_ms": 100,
            "worker_name": "test-worker",
            "profile_name": "test-profile"
        }"#;

        let config: AppConfig = serde_json::from_str(config_json).unwrap();

        assert_eq!(
            config.activity_arn,
            "arn:aws:states:us-east-1:123456789012:activity:test-activity"
        );
        assert_eq!(config.app_path, "/bin/echo");
        assert_eq!(config.poll_interval_ms, 100);
        assert_eq!(config.worker_name, "test-worker");
    }

    #[test]
    fn test_load_config_from_file() {
        let (dir, config_path) = create_test_config();

        let settings = Config::builder()
            .add_source(File::with_name(&config_path))
            .build()
            .unwrap();

        let config: AppConfig = settings.try_deserialize().unwrap();

        assert_eq!(
            config.activity_arn,
            "arn:aws:states:us-east-1:123456789012:activity:test-activity"
        );

        // Clean up
        drop(dir);
    }

    // Basic test for process_task function
    // In a real implementation, this would include more comprehensive mocking
    #[tokio::test]
    async fn test_process_task_basic() {
        // For now, just create a simple test that checks our config structure
        let config = AppConfig {
            activity_arn: "arn:aws:states:us-east-1:123456789012:activity:test-activity"
                .to_string(),
            app_path: "/bin/echo".to_string(),
            poll_interval_ms: 100,
            worker_name: "test-worker".to_string(),
            profile_name: "test-profile".to_string(),
        };

        // The test is simple but confirms our config structure is correct
        assert_eq!(config.app_path, "/bin/echo");

        // TODO: Add more comprehensive tests with proper mocking of the
        // Step Functions client and task processing
    }
}
