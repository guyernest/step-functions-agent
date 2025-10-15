use anyhow::{Context, Result};
use log::{info, error, debug};
use serde_json::{json, Value};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::io::Write;
use std::sync::Arc;

use crate::config::Config;

/// Nova Act executor that spawns Python subprocess to execute browser commands
pub struct NovaActExecutor {
    config: Arc<Config>,
    python_wrapper_path: PathBuf,
}

impl NovaActExecutor {
    /// Create a new Nova Act executor
    pub fn new(config: Arc<Config>) -> Result<Self> {
        // Find Python wrapper script
        let python_wrapper_path = Self::find_python_wrapper()
            .context("Failed to find Nova Act Python wrapper")?;

        info!("Nova Act executor initialized with wrapper: {}", python_wrapper_path.display());

        Ok(Self {
            config,
            python_wrapper_path,
        })
    }

    /// Find Python wrapper script
    fn find_python_wrapper() -> Result<PathBuf> {
        // Try relative path from current directory (for dev mode)
        let current_dir = std::env::current_dir()
            .context("Failed to get current directory")?;

        // Dev mode: current dir might be ui/ or project root
        // Use Path::join which handles platform-specific separators automatically
        let locations = vec![
            current_dir.join("python").join("nova_act_wrapper.py"),
            current_dir.join("..").join("python").join("nova_act_wrapper.py"),
            current_dir.join("..").join("..").join("python").join("nova_act_wrapper.py"),
        ];

        for path in &locations {
            if path.exists() {
                debug!("Found Python wrapper at: {}", path.display());
                return Ok(path.canonicalize()?);
            }
        }

        // Try relative path from executable (for release builds)
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                let wrapper_path = exe_dir.join("..").join("python").join("nova_act_wrapper.py");
                if wrapper_path.exists() {
                    debug!("Found Python wrapper at: {}", wrapper_path.display());
                    return Ok(wrapper_path.canonicalize()?);
                }
            }
        }

        anyhow::bail!("Could not find nova_act_wrapper.py in expected locations")
    }

    /// Check if uvx is available
    fn is_uvx_available() -> bool {
        Command::new("uvx")
            .arg("--version")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .map(|status| status.success())
            .unwrap_or(false)
    }

    /// Find Python executable or use uvx
    fn find_python_executable() -> Result<PathBuf> {
        // First check if uvx is available (best option for automatic dependency management)
        if Self::is_uvx_available() {
            debug!("Using uvx for automatic dependency management");
            return Ok(PathBuf::from("uvx"));
        }

        // Try to find venv Python
        let current_dir = std::env::current_dir()
            .context("Failed to get current directory")?;

        // Platform-specific venv paths
        #[cfg(target_os = "windows")]
        let venv_paths = vec![
            current_dir.join("python\\.venv\\Scripts\\python.exe"),
            current_dir.join("..\\python\\.venv\\Scripts\\python.exe"),
            current_dir.join("..\\..\\python\\.venv\\Scripts\\python.exe"),
        ];

        #[cfg(not(target_os = "windows"))]
        let venv_paths = vec![
            current_dir.join("python/.venv/bin/python"),
            current_dir.join("../python/.venv/bin/python"),
            current_dir.join("../../python/.venv/bin/python"),
        ];

        for path in &venv_paths {
            if path.exists() {
                debug!("Found Python venv at: {}", path.display());
                return Ok(path.canonicalize()?);
            }
        }

        // Try relative to executable (for release builds)
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                #[cfg(target_os = "windows")]
                let venv_python = exe_dir.join("..\\python\\.venv\\Scripts\\python.exe");

                #[cfg(not(target_os = "windows"))]
                let venv_python = exe_dir.join("../python/.venv/bin/python");

                if venv_python.exists() {
                    debug!("Found Python venv at: {}", venv_python.display());
                    return Ok(venv_python.canonicalize()?);
                }
            }
        }

        // Fallback to system python (platform-specific command)
        #[cfg(target_os = "windows")]
        {
            debug!("Using system python");
            Ok(PathBuf::from("python"))
        }

        #[cfg(not(target_os = "windows"))]
        {
            debug!("Using system python3");
            Ok(PathBuf::from("python3"))
        }
    }

    /// Execute a browser automation command
    pub async fn execute(&self, input: Value) -> Result<Value> {
        info!("Executing Nova Act command");

        // Build command input
        let command = self.build_command(input)?;

        // Spawn Python subprocess
        let output = self.spawn_python_subprocess(command).await?;

        // Parse output
        let result: Value = serde_json::from_str(&output)
            .context("Failed to parse Nova Act output as JSON")?;

        // Check if execution was successful
        if let Some(success) = result.get("success").and_then(|v| v.as_bool()) {
            if !success {
                let error = result.get("error")
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown error");

                anyhow::bail!("Nova Act execution failed: {}", error);
            }
        }

        Ok(result)
    }

    /// Build command for Python wrapper
    fn build_command(&self, mut input: Value) -> Result<Value> {
        // Add config values
        if let Some(obj) = input.as_object_mut() {
            // Add S3 bucket
            obj.insert("s3_bucket".to_string(), json!(self.config.s3_bucket));

            // Add AWS profile
            obj.insert("aws_profile".to_string(), json!(self.config.aws_profile));

            // Add user data dir if configured
            if let Some(ref user_data_dir) = self.config.user_data_dir {
                obj.insert(
                    "user_data_dir".to_string(),
                    json!(user_data_dir.to_string_lossy())
                );
            }

            // Add headless mode
            obj.insert("headless".to_string(), json!(self.config.headless));

            // Add record_video (always true for Activity pattern)
            obj.insert("record_video".to_string(), json!(true));

            // Default command type if not specified
            if !obj.contains_key("command_type") {
                obj.insert("command_type".to_string(), json!("act"));
            }

            // Add max_steps with default if not specified
            if !obj.contains_key("max_steps") {
                obj.insert("max_steps".to_string(), json!(50));  // Increased from 30 for complex flows
            }

            // Add timeout with default if not specified (in seconds)
            if !obj.contains_key("timeout") {
                obj.insert("timeout".to_string(), json!(600));  // 10 minutes for complex flows
            }
        }

        Ok(input)
    }

    /// Spawn Python subprocess and execute command
    async fn spawn_python_subprocess(&self, command: Value) -> Result<String> {
        let command_json = serde_json::to_string(&command)
            .context("Failed to serialize command to JSON")?;

        debug!("Spawning Python subprocess with command: {}", command_json);

        // Set NOVA_ACT_API_KEY environment variable
        let nova_act_api_key = self.config.get_nova_act_api_key()
            .context("Failed to get Nova Act API key")?;

        // Find Python executable (prefer uvx for automatic dependency management)
        let python_executable = Self::find_python_executable()?;
        let use_uvx = python_executable.file_name().and_then(|s| s.to_str()) == Some("uvx");
        debug!("Using Python executable: {} (uvx: {})", python_executable.display(), use_uvx);

        // Build command based on execution method
        let mut cmd = Command::new(python_executable);

        if use_uvx {
            // Use uvx to automatically install and run with nova-act package
            cmd.arg("--from").arg("nova-act").arg("python").arg(&self.python_wrapper_path);
        } else {
            // Direct Python execution
            cmd.arg(&self.python_wrapper_path);
        }

        // Spawn Python process
        let mut child = cmd
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .env("NOVA_ACT_API_KEY", nova_act_api_key)
            .env("AWS_PROFILE", &self.config.aws_profile)
            .spawn()
            .context("Failed to spawn Python subprocess")?;

        // Write command to stdin
        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(command_json.as_bytes())
                .context("Failed to write to Python subprocess stdin")?;
        }

        // Wait for process to complete
        let output = child.wait_with_output()
            .context("Failed to wait for Python subprocess")?;

        // Check exit status
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            error!("Python subprocess failed with stderr: {}", stderr);
            anyhow::bail!("Python subprocess failed: {}", stderr);
        }

        // Get stdout
        let stdout = String::from_utf8(output.stdout)
            .context("Failed to parse Python subprocess stdout as UTF-8")?;

        debug!("Python subprocess output: {}", stdout);

        // The Python script may output S3 upload logs to stdout before the JSON result
        // Extract only the last line which contains the JSON result
        let json_result = stdout.lines()
            .filter(|line| line.trim().starts_with("{"))
            .last()
            .unwrap_or(&stdout);

        debug!("Extracted JSON result: {}", json_result);

        Ok(json_result.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    #[tokio::test]
    async fn test_build_command() {
        let config = Arc::new(Config {
            activity_arn: "arn:aws:states:us-west-2:123456789:activity:browser-remote-prod".to_string(),
            aws_profile: "browser-agent".to_string(),
            s3_bucket: "browser-agent-recordings-prod".to_string(),
            user_data_dir: None,
            ui_port: 3000,
            nova_act_api_key: Some("test-key".to_string()),
            headless: false,
            heartbeat_interval: 60,
            aws_region: None,
        });

        let executor = NovaActExecutor {
            config,
            python_wrapper_path: PathBuf::from("/tmp/nova_act_wrapper.py"),
        };

        let input = json!({
            "prompt": "Navigate to example.com"
        });

        let command = executor.build_command(input).unwrap();

        assert_eq!(command.get("prompt").unwrap(), "Navigate to example.com");
        assert_eq!(command.get("s3_bucket").unwrap(), "browser-agent-recordings-prod");
        assert_eq!(command.get("aws_profile").unwrap(), "browser-agent");
        assert_eq!(command.get("record_video").unwrap(), true);
        assert_eq!(command.get("command_type").unwrap(), "act");
    }
}
