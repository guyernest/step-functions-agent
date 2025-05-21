// A Daemon that polls Step Functions Activity tasks and executes an application with the input as input
use anyhow::{Context, Result};
use aws_config::meta::region::ProvideRegion; // Added for region_provider.region()
use aws_config::profile::{ProfileFileCredentialsProvider, ProfileFileRegionProvider};
use aws_sdk_sfn::Client;
use config::{Config, File};
use log::{error, info, warn}; // warn will be used by setup_python_environment
use serde::Deserialize;
use std::path::Path;
use std::process::{Command, Stdio};
use std::time::Duration;
use tempfile::TempDir;
use tokio::time;

#[derive(Debug, Deserialize, Clone)]
pub struct AppConfig {
    pub activity_arn: String,
    pub app_path: String,
    pub poll_interval_ms: u64,
    pub worker_name: String,
    pub profile_name: String,
    pub uv_executable_path: Option<String>, 
    pub python_script_timeout_sec: Option<u64>, 
}

// Global static variable to store the path to the venv Python interpreter
static VENV_PYTHON_PATH: tokio::sync::OnceCell<Result<PathBuf, String>> = tokio::sync::OnceCell::const_new();


pub async fn process_task(
    task_input: String,
    task_token: String,
    client: &Client,
    config: &AppConfig, // AppConfig is already passed, no need for global static for config
) -> Result<()> {
    // Log task receipt
    info!("Received task with input: {}", task_input);

    // Check if this is a PyAutoGUI script (using the new format where script is inside input object)
    if task_input.contains("\"input\"") && (task_input.contains("\"script\"") || task_input.contains("\"actions\":")) {
        // Execute the script using our Python script executor
        info!("Detected PyAutoGUI script, executing with script_executor.py");
        
        // Determine script_executor.py path reliably
        let mut script_executor_path_candidate = Path::new("script_executor.py").to_path_buf();
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                let derived_path = exe_dir.join("script_executor.py");
                if derived_path.exists() {
                    script_executor_path_candidate = derived_path;
                } else {
                    warn!(
                        "script_executor.py not found at derived path {:?}, using default {:?}",
                        derived_path, script_executor_path_candidate
                    );
                }
            } else {
                warn!(
                    "Failed to get parent directory of executable, using default script_executor.py path: {:?}",
                    script_executor_path_candidate
                );
            }
        } else {
            warn!(
                "Failed to get current executable path, using default script_executor.py path: {:?}",
                script_executor_path_candidate
            );
        }

        let script_executor_path = match script_executor_path_candidate.canonicalize() {
            Ok(path) => path,
            Err(e) => {
                warn!(
                    "Failed to canonicalize script_executor.py path {:?}: {}. Using original.",
                    script_executor_path_candidate, e
                );
                script_executor_path_candidate // Use the non-canonicalized path if canonicalization fails
            }
        };
        info!("Using script_executor.py path: {:?}", script_executor_path);

        if !script_executor_path.exists() {
            error!("script_executor.py not found at path: {:?}", script_executor_path);
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

            return Err(anyhow::anyhow!("script_executor.py not found at path: {:?}", script_executor_path));
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
        let venv_python_path = Path::new(".venv").join("bin").join("python");
        info!(
            "Executing script with Python from venv: {:?}",
            venv_python_path
        );
        
        let venv_python_interpreter_path = match VENV_PYTHON_PATH.get() {
            Some(Ok(path)) => Some(path.clone()),
            Some(Err(err_msg)) => {
                warn!("Venv setup previously failed: {}. Will attempt fallback.", err_msg);
                None
            }
            None => {
                // This case should ideally not happen if main calls setup_agent_venv.
                // However, as a safeguard, or if called from a context where main didn't run (e.g. some tests)
                warn!("VENV_PYTHON_PATH not initialized. This is unexpected in normal operation. Will attempt fallback.");
                None
            }
        };

        let mut cmd;
        let mut using_venv = false;

        if let Some(interpreter_path) = venv_python_interpreter_path {
            if interpreter_path.exists() {
                info!("Using venv Python interpreter: {:?}", interpreter_path);
                cmd = tokio::process::Command::new(interpreter_path);
                cmd.arg(&script_executor_path)
                   .arg(script_path.to_string_lossy().to_string());
                using_venv = true;
            } else {
                warn!("Venv Python interpreter path {:?} does not exist. Attempting fallback.", interpreter_path);
                // Fallthrough to uv run
                let uv_exe = config.uv_executable_path.as_deref().unwrap_or("uv");
                cmd = tokio::process::Command::new(uv_exe);
                cmd.arg("run")
                   .arg("--pip")
                   .arg("pyautogui")
                   .arg("--pip")
                   .arg("pillow")
                   .arg("--pip")
                   .arg("opencv-python") // opencv-python is optional in script_executor.py
                   .arg(&script_executor_path)
                   .arg(script_path.to_string_lossy().to_string());
                info!("Falling back to 'uv run' with command: {:?}", cmd);
            }
        } else {
            let uv_exe = config.uv_executable_path.as_deref().unwrap_or("uv");
            cmd = tokio::process::Command::new(uv_exe);
            cmd.arg("run")
               .arg("--pip")
               .arg("pyautogui")
               .arg("--pip")
               .arg("pillow")
               .arg("--pip")
               .arg("opencv-python") // opencv-python is optional in script_executor.py
               .arg(&script_executor_path)
               .arg(script_path.to_string_lossy().to_string());
            info!("Venv Python not available. Using 'uv run' with command: {:?}", cmd);
        }

        cmd.stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .kill_on_drop(true); // Ensure process is killed if this future is dropped

        let timeout_duration_secs = config.python_script_timeout_sec.unwrap_or(300);
        let timeout_duration = Duration::from_secs(timeout_duration_secs);

        let execution_result = match time::timeout(timeout_duration, cmd.output()).await {
            Ok(Ok(output)) => { // Timeout did not occur, command finished
                info!("Python script finished execution.");
                Ok(output)
            }
            Ok(Err(e)) => { // Timeout did not occur, command failed to start or other IO error
                error!("Failed to execute Python script command: {}", e);
                Err(anyhow::anyhow!("Failed to execute Python script command: {}", e))
            }
            Err(_) => { // Timeout occurred
                error!("Python script execution timed out after {} seconds", timeout_duration_secs);
                Err(anyhow::anyhow!("ScriptTimeoutError: Python script execution timed out after {} seconds", timeout_duration_secs))
            }
        };
        
        let mut response = input_value.clone(); // Prepare response structure early

        match execution_result {
            Ok(output) => {
                let stdout_str = String::from_utf8_lossy(&output.stdout).to_string();
                let stderr_str = String::from_utf8_lossy(&output.stderr).to_string();

                if output.status.success() {
                    info!("Script executed successfully. Stdout: {}", stdout_str);
                    match serde_json::from_str::<serde_json::Value>(&stdout_str) {
                        Ok(script_json_output) => {
                             if let Some(input_obj) = response.get_mut("input") {
                                if let Some(obj) = input_obj.as_object_mut() {
                                    obj.remove("script");
                                    obj.insert("script_output".to_string(), script_json_output);
                                }
                            }
                        }
                        Err(e) => {
                            error!("Failed to parse script output as JSON: {}. Raw stdout: {}", e, stdout_str);
                            let error_payload = serde_json::json!({
                                "success": false,
                                "error": "InvalidScriptOutputError",
                                "message": format!("Python script produced invalid JSON output. Error: {}", e),
                                "raw_stdout": stdout_str,
                                "raw_stderr": stderr_str
                            });
                            if let Some(input_obj) = response.get_mut("input") {
                                if let Some(obj) = input_obj.as_object_mut() {
                                    obj.remove("script");
                                    obj.insert("script_output".to_string(), error_payload);
                                }
                            }
                        }
                    }
                } else {
                    error!("Script execution failed (non-zero exit code). Stderr: {}. Stdout: {}", stderr_str, stdout_str);
                    let error_payload = serde_json::json!({
                        "success": false,
                        "error": "ScriptExecutionError", // Generic execution error for non-zero exit
                        "message": "Python script exited with a non-zero status code.",
                        "exit_code": output.status.code(),
                        "raw_stdout": stdout_str,
                        "raw_stderr": stderr_str
                    });
                     if let Some(input_obj) = response.get_mut("input") {
                        if let Some(obj) = input_obj.as_object_mut() {
                            obj.remove("script");
                            obj.insert("script_output".to_string(), error_payload);
                        }
                    }
                }
            }
            Err(e) => { // Covers timeout or other execution errors from cmd.output()
                error!("Python script command execution failed: {}", e);
                let (error_type, error_message) = if e.to_string().contains("ScriptTimeoutError") {
                    ("ScriptTimeoutError", format!("Python script execution timed out after {} seconds.", timeout_duration_secs))
                } else {
                    ("ScriptExecutionError", format!("Failed to execute Python script: {}", e))
                };
                let error_payload = serde_json::json!({
                    "success": false,
                    "error": error_type,
                    "message": error_message
                });
                if let Some(input_obj) = response.get_mut("input") {
                    if let Some(obj) = input_obj.as_object_mut() {
                        obj.remove("script");
                        obj.insert("script_output".to_string(), error_payload);
                    }
                }
            }
        }
        
        // Add the approved field at the root level of the response
        if let Some(obj) = response.as_object_mut() {
            obj.insert("approved".to_string(), serde_json::json!(true));
        }
        
        let response_str = serde_json::to_string(&response)
            .context("Failed to serialize final response")?;
            
        info!("Sending final response to Step Functions: {}", response_str);
        
        client.send_task_success()
            .task_token(task_token)
            .output(response_str)
            .send().await
            .context("Failed to send task success to Step Functions")?;

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

async fn setup_python_environment(config: &AppConfig) -> Result<()> {
    let venv_dir = Path::new(".venv");
    let python_executable = &config.base_python_executable;

    // Check if the base Python executable exists
    if !Path::new(python_executable).exists() {
        error!("Python executable not found: {}", python_executable);
        return Err(anyhow::anyhow!(
            "Python executable not found: {}",
            python_executable
        ));
    }

    // Create virtual environment if it doesn't exist
    if !venv_dir.exists() {
        info!("Creating Python virtual environment at .venv");
        let status = Command::new(python_executable)
            .arg("-m")
            .arg("venv")
            .arg(".venv")
            .status()
            .context("Failed to create Python virtual environment")?;

        if !status.success() {
            error!("Failed to create Python virtual environment");
            return Err(anyhow::anyhow!(
                "Failed to create Python virtual environment"
            ));
        }
        info!("Python virtual environment created successfully");
    } else {
        info!("Python virtual environment already exists at .venv");
    }

    // Install dependencies
    let venv_python_path = venv_dir.join("bin").join("python");
    let packages = ["pyautogui", "pillow", "opencv-python"];

    for package in &packages {
        info!("Installing {}...", package);
        let status = Command::new(&venv_python_path)
            .arg("-m")
            .arg("pip")
            .arg("install")
            .arg(package)
            .status();
        
        match status {
            Ok(status) if status.success() => {
                info!("Successfully installed {}", package);
            }
            Ok(status) => {
                // Installation failed
                if *package == "opencv-python" {
                    warn!( // warn is used here
                        "Failed to install opencv-python. Continuing without OpenCV support. Status: {:?}",
                        status
                    );
                } else {
                    error!("Failed to install {}. Status: {:?}", package, status);
                    return Err(anyhow::anyhow!("Failed to install {}", package));
                }
            }
            Err(e) => {
                // Command execution failed
                if *package == "opencv-python" {
                    warn!( // warn is used here
                        "Failed to execute pip install for opencv-python. Continuing without OpenCV support. Error: {}",
                        e
                    );
                } else {
                    error!("Failed to execute pip install for {}. Error: {}", package, e);
                    return Err(anyhow::anyhow!(
                        "Failed to execute pip install for {}",
                        package
                    ));
                }
            }
        }
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

    // Setup Python environment / agent venv
    // Initialize VENV_PYTHON_PATH once.
    VENV_PYTHON_PATH.get_or_init(|| async {
        setup_agent_venv(&config).await.map_err(|e| {
            let err_msg = format!("Failed to setup agent venv: {}", e);
            error!("{}", err_msg); // Log the error during setup
            err_msg // Store the error message
        })
    }).await;

    // Log whether venv setup succeeded or failed for clarity after initialization
    match VENV_PYTHON_PATH.get() {
        Some(Ok(path)) => info!("Agent venv Python interpreter path: {:?}", path),
        Some(Err(err_msg)) => warn!("Agent venv setup failed or was skipped: {}. Fallback to 'uv run' will be used for Python scripts.", err_msg),
        None => error!("VENV_PYTHON_PATH was not initialized, which is unexpected."), // Should not happen
    }
    
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

    // For aws-config 0.55.3, BehaviorVersion and defaults() are not available.
    // We construct SdkConfig manually using the providers.
    let region = region_provider.region().await; // Await the region from the provider

    let sdk_config = aws_config::SdkConfig::builder()
        .credentials_provider(aws_credential_types::provider::SharedCredentialsProvider::new(credentials_provider))
        .region(region) 
        .build();

    let client = Client::new(&sdk_config);

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
    use std::path::PathBuf; // Was missing
    use tempfile::tempdir;
    use test_log::test;
    use serde_json; // Was missing

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
            "profile_name": "test-profile",
            "uv_executable_path": "uv",
            "uv_executable_path": "uv",
            "python_script_timeout_sec": 300
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
            "profile_name": "test-profile",
            "base_python_executable": "python3",
            "python_script_timeout_sec": 300
        }"#;

        let config: AppConfig = serde_json::from_str(config_json).unwrap();

        assert_eq!(
            config.activity_arn,
            "arn:aws:states:us-east-1:123456789012:activity:test-activity"
        );
        assert_eq!(config.app_path, "/bin/echo");
        assert_eq!(config.poll_interval_ms, 100);
        assert_eq!(config.worker_name, "test-worker");
        assert_eq!(config.uv_executable_path, Some("uv".to_string()));
        assert_eq!(config.python_script_timeout_sec, Some(300));
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
            uv_executable_path: Some("uv".to_string()),
            python_script_timeout_sec: Some(300),
        };

        // The test is simple but confirms our config structure is correct
        assert_eq!(config.app_path, "/bin/echo");

        // TODO: Add more comprehensive tests with proper mocking of the
        // Step Functions client and task processing
    }
}

// Future Rust Unit/Integration Test Scenarios (Placeholder)
// These tests should be implemented once the Rust build environment is stable.
//
// 1. Configuration Loading (`AppConfig`):
//    - Test loading a valid `daemon_config.json`.
//    - Test behavior with missing optional fields (e.g., `uv_executable_path`, `python_script_timeout_sec`) - ensure defaults are applied.
//    - Test failure with invalid or missing required fields.
//
// 2. `setup_agent_venv` Function:
//    - Mock `std::env::current_exe()` to control base path.
//    - Mock `Command::output()` for `uv venv` and `uv pip install` calls.
//    - Test successful venv creation and dependency installation (marker file created, correct Python path returned).
//    - Test venv already exists and is valid (marker file present, skips setup).
//    - Test existing incomplete venv (no marker file) is removed and recreated.
//    - Test failure if `uv` executable is not found (using a bad path in `uv_executable_path`).
//    - Test failure during `uv venv` command.
//    - Test failure during `uv pip install` for essential packages (pyautogui, pillow).
//    - Test warning/partial success if `opencv-python` fails to install but essentials succeed.
//    - Test file system errors (e.g., permission issues creating venv or marker file).
//
// 3. `VENV_PYTHON_PATH` Global Static Initialization (in `main`):
//    - Test that `setup_agent_venv` is called only once.
//    - Test that subsequent accesses to `VENV_PYTHON_PATH` retrieve the stored result without re-running setup.
//    - Test behavior if `setup_agent_venv` returns an error (ensure error is stored and logged).
//
// 4. `process_task` Function - Python Script Execution Paths:
//    - Mock `VENV_PYTHON_PATH.get()` to simulate different venv states.
//    - **Venv Path (Success):**
//        - Simulate venv Python path available and valid.
//        - Mock `tokio::process::Command::output()` for the venv Python execution.
//        - Verify script is called with `<venv_python> script_executor.py <script_file>`.
//        - Test successful script output (valid JSON).
//        - Test script outputting invalid JSON.
//        - Test script exiting with non-zero status.
//    - **Fallback Path (`uv run`):**
//        - Simulate venv Python path unavailable (e.g., `VENV_PYTHON_PATH` stores Err, or path doesn't exist).
//        - Mock `tokio::process::Command::output()` for `uv run ...` execution.
//        - Verify `uv run` is called with correct `--pip` arguments and script path.
//        - Test successful script output via `uv run`.
//        - Test `uv run` command itself failing (e.g., `uv` not found, `uv run` returns error).
//    - **Script Executor Path Determination:**
//        - Mock `std::env::current_exe()` and `Path::exists()` / `Path::canonicalize()` to test different scenarios for finding `script_executor.py`.
//        - Test finding it next to the executable.
//        - Test fallback to default path if not found next to executable.
//        - Test error if `script_executor.py` is not found at all.
//
// 5. `process_task` Function - Timeout Logic:
//    - For both venv path and `uv run` path:
//        - Mock `tokio::process::Command::output()` to simulate a script that runs longer than the timeout.
//        - Verify `ScriptTimeoutError` is correctly generated in the output JSON.
//        - Verify script that finishes within timeout does not produce timeout error.
//        - Test with default timeout (if `python_script_timeout_sec` is None in config) and custom timeout.
//
// 6. `process_task` Function - Error Reporting to Step Functions:
//    - Verify that for various failures (script not found, venv setup fails completely, script execution error, timeout, invalid output JSON), the task is still reported as "success" to Step Functions, but the `output` field in the SFN success call contains the JSON detailing the error (e.g., `script_output.error`, `script_output.message`).
//
// 7. Legacy Task Execution (`app_path` in `daemon_config.json`):
//    - Test execution of a simple command (e.g., `echo`) via `app_path` when the input is not a Python script.
//    - Verify output is captured correctly.
//    - Test failure if `app_path` command fails.
//
// 8. End-to-End Mocking (Simplified):
//    - Mock `aws_sdk_sfn::Client` to simulate receiving a task and sending a success/failure response.
//    - Provide a sample task input (Python script).
//    - Verify the overall flow through `poll_activity` and `process_task`, checking the structure of the output sent back to the mocked SFN client.
