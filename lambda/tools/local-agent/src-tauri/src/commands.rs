use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::io::{Write, Seek};
use std::sync::Mutex;

// Global state for polling
lazy_static::lazy_static! {
    static ref POLLING_STATE: Mutex<bool> = Mutex::new(false);
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub activity_arn: String,
    pub profile_name: String,
    pub worker_name: String,
    pub poll_interval_ms: u64,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            activity_arn: String::new(),
            profile_name: "default".to_string(),
            worker_name: "local-agent-worker".to_string(),
            poll_interval_ms: 5000,
        }
    }
}

fn get_config_path() -> PathBuf {
    // Use the parent directory's daemon_config.json
    PathBuf::from("../daemon_config.json")
}

#[tauri::command]
pub async fn load_config() -> Result<AppConfig, String> {
    let config_path = get_config_path();
    
    if !config_path.exists() {
        // Return default config if file doesn't exist
        return Ok(AppConfig::default());
    }
    
    let content = fs::read_to_string(&config_path)
        .map_err(|e| format!("Failed to read config file: {}", e))?;
    
    // Parse the existing daemon_config.json format
    let json: serde_json::Value = serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse config JSON: {}", e))?;
    
    let profile_name = json["profile_name"].as_str().unwrap_or("default").to_string();
    // Replace placeholder with default
    let profile_name = if profile_name == "<PROFILE_NAME>" {
        "default".to_string()
    } else {
        profile_name
    };
    
    Ok(AppConfig {
        activity_arn: json["activity_arn"].as_str().unwrap_or("").to_string(),
        profile_name,
        worker_name: json["worker_name"].as_str().unwrap_or("local-agent-worker").to_string(),
        poll_interval_ms: json["poll_interval_ms"].as_u64().unwrap_or(5000),
    })
}

#[tauri::command]
pub async fn save_config(config: AppConfig) -> Result<(), String> {
    let config_path = get_config_path();
    
    // Create JSON in the daemon_config.json format
    let json = serde_json::json!({
        "activity_arn": config.activity_arn,
        "app_path": "uv run script_executor.py",
        "poll_interval_ms": config.poll_interval_ms,
        "worker_name": config.worker_name,
        "profile_name": config.profile_name
    });
    
    let content = serde_json::to_string_pretty(&json)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;
    
    fs::write(&config_path, content)
        .map_err(|e| format!("Failed to write config file: {}", e))?;
    
    Ok(())
}

#[tauri::command]
pub async fn list_aws_profiles() -> Result<Vec<String>, String> {
    let home = dirs::home_dir()
        .ok_or_else(|| "Failed to get home directory".to_string())?;
    
    let credentials_path = home.join(".aws").join("credentials");
    
    if !credentials_path.exists() {
        return Ok(vec!["default".to_string()]);
    }
    
    let content = fs::read_to_string(&credentials_path)
        .map_err(|e| format!("Failed to read AWS credentials file: {}", e))?;
    
    let mut profiles = Vec::new();
    for line in content.lines() {
        if line.starts_with('[') && line.ends_with(']') {
            let profile = line.trim_start_matches('[').trim_end_matches(']');
            profiles.push(profile.to_string());
        }
    }
    
    if profiles.is_empty() {
        profiles.push("default".to_string());
    }
    
    Ok(profiles)
}

#[tauri::command]
pub async fn test_connection(config: AppConfig) -> Result<bool, String> {
    use aws_sdk_sfn::Client;
    
    eprintln!("Testing connection with profile: {}", config.profile_name);
    eprintln!("Activity ARN: {}", config.activity_arn);
    
    // Check for placeholder values
    if config.profile_name == "<PROFILE_NAME>" || config.profile_name.is_empty() {
        return Err("Please select a valid AWS profile from the dropdown".to_string());
    }
    
    if config.activity_arn.is_empty() {
        return Err("Activity ARN is required".to_string());
    }
    
    if !config.activity_arn.starts_with("arn:aws:states:") {
        return Err("Invalid Activity ARN format".to_string());
    }
    
    // Extract region from ARN (arn:aws:states:REGION:...)
    let arn_parts: Vec<&str> = config.activity_arn.split(':').collect();
    if arn_parts.len() < 4 {
        return Err("Invalid ARN format - cannot determine region".to_string());
    }
    let region = arn_parts[3];
    eprintln!("Using region: {}", region);
    
    // Create AWS config with the specified profile
    // First set the AWS_PROFILE environment variable
    std::env::set_var("AWS_PROFILE", &config.profile_name);
    
    // Load AWS config - this will use AWS_PROFILE we just set
    let mut config_loader = aws_config::from_env();
    config_loader = config_loader.region(aws_config::Region::new(region.to_string()));
    
    let aws_config = config_loader.load().await;
    
    let client = Client::new(&aws_config);
    
    // Use describe_activity to check if the activity exists without consuming any tasks
    match client
        .describe_activity()
        .activity_arn(&config.activity_arn)
        .send()
        .await
    {
        Ok(response) => {
            // Activity exists! Let's also check its status
            let activity_name = response.name();
            eprintln!("Activity '{}' found and accessible", activity_name);
            Ok(true)
        }
        Err(e) => {
            let error_msg = e.to_string();
            
            // Parse different error types for better user feedback
            if error_msg.contains("ResourceNotFound") || 
               error_msg.contains("ActivityDoesNotExist") ||
               error_msg.contains("does not exist") {
                Err(format!("Activity not found. Please check the ARN is correct:\n{}", config.activity_arn))
            } else if error_msg.contains("UnrecognizedClientException") || 
                      error_msg.contains("InvalidSignature") ||
                      error_msg.contains("credentials") ||
                      error_msg.contains("could not load credentials") {
                Err(format!("Authentication failed. Check your AWS profile '{}' and credentials", config.profile_name))
            } else if error_msg.contains("AccessDenied") || error_msg.contains("AccessDeniedException") {
                Err("Access denied. Check your IAM permissions for states:DescribeActivity".to_string())
            } else if error_msg.contains("could not connect") || error_msg.contains("timed out") {
                Err(format!("Could not connect to AWS. Check your network and region: {}", region))
            } else if error_msg.contains("ExpiredToken") || error_msg.contains("ExpiredTokenException") {
                Err("AWS credentials have expired. Please refresh your session".to_string())
            } else if error_msg.contains("InvalidArn") || error_msg.contains("ValidationException") {
                Err(format!("Invalid Activity ARN format: {}", config.activity_arn))
            } else {
                // Log the actual error for debugging
                eprintln!("AWS API Error: {}", error_msg);
                
                // Return the actual error for unknown cases
                Err(format!("Connection test failed: {}", error_msg))
            }
        }
    }
}

#[tauri::command]
pub async fn get_polling_status() -> Result<serde_json::Value, String> {
    let is_polling = *POLLING_STATE.lock().unwrap();
    Ok(serde_json::json!({
        "isPolling": is_polling,
        "connectionStatus": if is_polling { "connected" } else { "disconnected" },
        "currentTask": null,
        "tasksProcessed": 0,
        "lastTaskTime": null,
        "uptime": 0
    }))
}

#[tauri::command]
pub async fn start_polling() -> Result<(), String> {
    let mut state = POLLING_STATE.lock().unwrap();
    *state = true;
    eprintln!("Polling started");
    // TODO: Implement actual polling logic with AWS Step Functions
    Ok(())
}

#[tauri::command]
pub async fn stop_polling() -> Result<(), String> {
    let mut state = POLLING_STATE.lock().unwrap();
    *state = false;
    eprintln!("Polling stopped");
    // TODO: Stop the actual polling task
    Ok(())
}

#[tauri::command]
pub async fn list_example_scripts() -> Result<Vec<String>, String> {
    use std::fs;
    
    // Try both current directory and parent directory for examples
    let examples_dir = if PathBuf::from("examples").exists() {
        PathBuf::from("examples")
    } else if PathBuf::from("../examples").exists() {
        PathBuf::from("../examples")
    } else {
        eprintln!("Examples directory not found in current or parent directory");
        return Ok(Vec::new());
    };
    
    let mut scripts = Vec::new();
    
    match fs::read_dir(&examples_dir) {
        Ok(entries) => {
            for entry in entries {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.extension().and_then(|s| s.to_str()) == Some("json") {
                        if let Some(filename) = path.file_name().and_then(|s| s.to_str()) {
                            scripts.push(filename.to_string());
                        }
                    }
                }
            }
        }
        Err(e) => {
            eprintln!("Failed to read examples directory: {}", e);
        }
    }
    
    scripts.sort();
    Ok(scripts)
}

#[tauri::command]
pub async fn load_example_script(filename: String) -> Result<String, String> {
    // Sanitize filename to prevent directory traversal
    if filename.contains("..") || filename.contains("/") || filename.contains("\\") {
        return Err("Invalid filename".to_string());
    }
    
    // Try both current directory and parent directory for examples
    let script_path = if PathBuf::from("examples").join(&filename).exists() {
        PathBuf::from("examples").join(&filename)
    } else if PathBuf::from("../examples").join(&filename).exists() {
        PathBuf::from("../examples").join(&filename)
    } else {
        return Err(format!("Example script not found: {}", filename));
    };
    
    fs::read_to_string(&script_path)
        .map_err(|e| format!("Failed to read example script: {}", e))
}

#[tauri::command]
pub async fn validate_script(script: String) -> Result<serde_json::Value, String> {
    // Parse the script as JSON
    let parsed: serde_json::Value = match serde_json::from_str(&script) {
        Ok(val) => val,
        Err(e) => {
            return Ok(serde_json::json!({
                "valid": false,
                "errors": [format!("Invalid JSON: {}", e)]
            }));
        }
    };
    
    let mut errors = Vec::new();
    let mut warnings = Vec::new();
    
    // Check required fields
    if !parsed["name"].is_string() {
        errors.push("Missing or invalid 'name' field".to_string());
    }
    
    if !parsed["actions"].is_array() {
        errors.push("Missing or invalid 'actions' array".to_string());
    } else {
        let actions = parsed["actions"].as_array().unwrap();
        if actions.is_empty() {
            warnings.push("Script has no actions".to_string());
        }
        
        // Validate each action
        for (i, action) in actions.iter().enumerate() {
            if !action["type"].is_string() {
                errors.push(format!("Action {} missing 'type' field", i + 1));
            } else {
                let action_type = action["type"].as_str().unwrap();
                // Validate based on action type
                match action_type {
                    "click" => {
                        if !action["x"].is_number() && !action["image"].is_string() {
                            warnings.push(format!("Click action {} should have either x/y coordinates or image", i + 1));
                        }
                    }
                    "type" => {
                        if !action["text"].is_string() {
                            errors.push(format!("Type action {} missing 'text' field", i + 1));
                        }
                    }
                    "hotkey" => {
                        if !action["keys"].is_array() {
                            errors.push(format!("Hotkey action {} missing 'keys' array", i + 1));
                        }
                    }
                    "launch" => {
                        if !action["app"].is_string() {
                            errors.push(format!("Launch action {} missing 'app' field", i + 1));
                        }
                    }
                    _ => {
                        // Other action types are ok
                    }
                }
            }
        }
    }
    
    Ok(serde_json::json!({
        "valid": errors.is_empty(),
        "errors": errors,
        "warnings": warnings
    }))
}

#[tauri::command]
pub async fn execute_test_script(script: String, dry_run: bool) -> Result<serde_json::Value, String> {
    use std::process::Command;
    use tempfile::NamedTempFile;
    use std::io::{Write, Seek};
    
    // For dry run, just validate and return success
    if dry_run {
        let validation = validate_script(script.clone()).await?;
        if validation["valid"].as_bool().unwrap_or(false) {
            return Ok(serde_json::json!({
                "success": true,
                "results": [{
                    "action": "dry_run",
                    "status": "success",
                    "details": "Dry run completed - script is valid"
                }]
            }));
        } else {
            return Ok(serde_json::json!({
                "success": false,
                "error": "Script validation failed",
                "results": []
            }));
        }
    }
    
    // For actual execution, we'll use the Python script executor
    // First, save the script to a temporary file
    let mut temp_file = NamedTempFile::new()
        .map_err(|e| format!("Failed to create temp file: {}", e))?;
    
    temp_file.write_all(script.as_bytes())
        .map_err(|e| format!("Failed to write script: {}", e))?;
    
    let script_path = temp_file.path().to_string_lossy().to_string();
    
    // Check if script_executor.py exists - try parent directory first (main project dir)
    let parent_executor = PathBuf::from("../script_executor.py");
    let executor_path = if parent_executor.exists() {
        parent_executor
    } else {
        let current_executor = PathBuf::from("script_executor.py");
        if current_executor.exists() {
            current_executor
        } else {
            return Ok(serde_json::json!({
                "success": false,
                "error": "Script executor not found. Please ensure script_executor.py is in the project directory.",
                "results": []
            }));
        }
    };
    
    // For GUI testing, pass the script directly (no wrapping needed)
    // Just validate it's proper JSON
    let _parsed_script: serde_json::Value = serde_json::from_str(&script)
        .map_err(|e| format!("Failed to parse script: {}", e))?;
    
    // Write the script directly to temp file (already done above)
    temp_file.flush()
        .map_err(|e| format!("Failed to flush temp file: {}", e))?;
    
    // Try to use the virtual environment Python first
    let venv_python = PathBuf::from("../cpython-3.12.3-macos-aarch64-none/bin/python3");
    let python_cmd = if venv_python.exists() {
        eprintln!("Using virtual environment Python");
        venv_python.to_string_lossy().to_string()
    } else if cfg!(target_os = "windows") {
        eprintln!("Using system Python on Windows");
        "python".to_string()
    } else {
        eprintln!("Using system Python");
        "python3".to_string()
    };
    
    let executor_script = executor_path.to_string_lossy();
    
    eprintln!("Executing script with: {} {} {}", python_cmd, executor_script, script_path);
    
    let output = Command::new(&python_cmd)
        .arg(executor_script.as_ref())
        .arg(&script_path)
        .output();
    
    match output {
        Ok(output) => {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let stderr = String::from_utf8_lossy(&output.stderr);
            
            eprintln!("Script stdout: {}", stdout);
            eprintln!("Script stderr: {}", stderr);
            
            // Check if we have the expected output structure in stdout
            if let Ok(result) = serde_json::from_str::<serde_json::Value>(&stdout) {
                // Check if this is our wrapped response
                if let Some(input) = result.get("input") {
                    if let Some(script_output) = input.get("script_output") {
                        // Extract the success and results from script_output
                        return Ok(serde_json::json!({
                            "success": script_output["success"].as_bool().unwrap_or(false),
                            "results": script_output["results"].as_array().cloned().unwrap_or_default(),
                            "error": script_output.get("error").and_then(|e| e.as_str()).map(|s| s.to_string())
                        }));
                    }
                }
                // If not wrapped, return as is
                Ok(result)
            } else if output.status.success() {
                // No JSON output but command succeeded
                Ok(serde_json::json!({
                    "success": true,
                    "results": [{
                        "action": "execute",
                        "status": "success",
                        "details": "Script executed successfully"
                    }]
                }))
            } else {
                // Command failed
                Ok(serde_json::json!({
                    "success": false,
                    "error": if !stderr.is_empty() { stderr.to_string() } else { "Script execution failed".to_string() },
                    "results": []
                }))
            }
        }
        Err(e) => {
            Ok(serde_json::json!({
                "success": false,
                "error": format!("Failed to execute script: {}", e),
                "results": []
            }))
        }
    }
}

#[tauri::command]
pub async fn stop_script_execution() -> Result<(), String> {
    // TODO: Implement script execution stopping
    // This would need to track the running process and kill it
    Ok(())
}