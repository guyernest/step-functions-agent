use anyhow::{Context, Result};
use log::{info, error, debug};
use serde_json::{json, Value};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::io::Write;
use std::sync::Arc;

use crate::config::Config;
use crate::paths::AppPaths;

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
        // Try AppPaths first (recommended for production)
        if let Ok(paths) = AppPaths::new() {
            let wrapper_path = paths.python_scripts_dir().join("nova_act_wrapper.py");
            if wrapper_path.exists() {
                debug!("Found Python wrapper via AppPaths at: {}", wrapper_path.display());
                return Ok(wrapper_path);
            }
        }

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
                debug!("Found Python wrapper (dev mode) at: {}", path.display());
                return Ok(path.canonicalize()?);
            }
        }

        // Try relative path from executable (for release builds - fallback)
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                // macOS .app bundle: executable is at Contents/MacOS/, resources are at Contents/Resources/
                #[cfg(target_os = "macos")]
                let wrapper_paths = vec![
                    exe_dir.join("..").join("Resources").join("_up_").join("python").join("nova_act_wrapper.py"),  // macOS bundle (primary)
                    exe_dir.join("..").join("Resources").join("python").join("nova_act_wrapper.py"),                // macOS bundle (alternative)
                    exe_dir.join("..").join("python").join("nova_act_wrapper.py"),                                  // fallback
                ];

                // For Linux - check same locations as other Python scripts
                #[cfg(target_os = "linux")]
                let wrapper_paths = vec![
                    exe_dir.join("python").join("nova_act_wrapper.py"),
                    exe_dir.join("resources").join("python").join("nova_act_wrapper.py"),
                    exe_dir.join("_up_").join("python").join("nova_act_wrapper.py"),
                    exe_dir.join("..").join("python").join("nova_act_wrapper.py"),
                ];

                // For Windows - check same locations as other Python scripts
                #[cfg(target_os = "windows")]
                let wrapper_paths = vec![
                    exe_dir.join("python").join("nova_act_wrapper.py"),
                    exe_dir.join("resources").join("python").join("nova_act_wrapper.py"),
                    exe_dir.join("_up_").join("python").join("nova_act_wrapper.py"),
                    exe_dir.join("..").join("python").join("nova_act_wrapper.py"),
                ];

                for wrapper_path in wrapper_paths {
                    if wrapper_path.exists() {
                        debug!("Found Python wrapper (fallback) at: {}", wrapper_path.display());
                        return Ok(wrapper_path.canonicalize()?);
                    }
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

    /// Find Python executable from venv
    fn find_python_executable() -> Result<PathBuf> {
        // IMPORTANT: Always use the venv we set up, NOT uvx
        // uvx downloads packages to its own cache with potentially incompatible versions
        // We need to use the venv created by "Setup Python Environment"

        // Try AppPaths first (recommended for production - venv in LOCALAPPDATA)
        if let Ok(paths) = AppPaths::new() {
            let venv_dir = paths.python_env_dir();

            #[cfg(target_os = "windows")]
            let venv_python = venv_dir.join("Scripts").join("python.exe");

            #[cfg(not(target_os = "windows"))]
            let venv_python = venv_dir.join("bin").join("python");

            if venv_python.exists() {
                info!("Found Python venv via AppPaths at: {}", venv_python.display());
                return Ok(venv_python);
            }

            info!("Python venv not found at AppPaths location: {}", venv_dir.display());
        }

        // Try to find venv Python (dev mode)
        let current_dir = std::env::current_dir()
            .context("Failed to get current directory")?;

        // Platform-specific venv paths (dev mode)
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
                info!("Found Python venv (dev mode) at: {}", path.display());
                return Ok(path.canonicalize()?);
            }
        }

        // Try relative to executable (for release builds - legacy fallback)
        if let Ok(exe_path) = std::env::current_exe() {
            info!("Executable path: {}", exe_path.display());

            if let Some(exe_dir) = exe_path.parent() {
                info!("Executable directory: {}", exe_dir.display());

                // For macOS app bundle:
                // exe_path = /Applications/Local Browser Agent.app/Contents/MacOS/Local Browser Agent
                // exe_dir = /Applications/Local Browser Agent.app/Contents/MacOS/
                // We need: /Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv/bin/python

                #[cfg(target_os = "windows")]
                let venv_paths_release = vec![
                    exe_dir.join("python\\.venv\\Scripts\\python.exe"),
                    exe_dir.join("resources\\python\\.venv\\Scripts\\python.exe"),
                    exe_dir.join("_up_\\python\\.venv\\Scripts\\python.exe"),
                    exe_dir.join("..\\python\\.venv\\Scripts\\python.exe"),
                ];

                #[cfg(not(target_os = "windows"))]
                let venv_paths_release = vec![
                    exe_dir.join("../Resources/_up_/python/.venv/bin/python"),  // macOS bundle (primary)
                    exe_dir.join("../Resources/python/.venv/bin/python"),       // macOS bundle (alternative)
                    exe_dir.join("../python/.venv/bin/python"),                 // Linux
                ];

                info!("Searching for Python venv in app bundle (legacy fallback)...");
                for venv_python in &venv_paths_release {
                    let absolute_path = std::fs::canonicalize(venv_python).ok();
                    info!("Checking: {} (absolute: {:?})", venv_python.display(), absolute_path);

                    if venv_python.exists() {
                        info!("✓ Found Python venv (legacy) at: {}", venv_python.display());
                        return Ok(venv_python.canonicalize()?);
                    }
                }

                error!("None of the expected venv paths exist");
            }
        }

        // No venv found - this is an error, user needs to run setup
        error!("Python venv not found in app bundle");
        error!("Please run the setup script or use the 'Setup Python Environment' button in the Configuration screen");

        anyhow::bail!(
            "Python virtual environment not found. Please run setup:\n\
             1. Use the 'Setup Python Environment' button in the Configuration screen, OR\n\
             2. Run: ./SETUP.sh from the deployment package"
        )
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

            // Add browser_channel - always provide a value, using platform default if not configured
            let browser_channel = self.config.browser_channel.as_ref()
                .map(|s| s.as_str())
                .unwrap_or_else(|| {
                    #[cfg(target_os = "windows")]
                    { "msedge" }
                    #[cfg(not(target_os = "windows"))]
                    { "chrome" }
                });
            obj.insert("browser_channel".to_string(), json!(browser_channel));
            info!("→ Passing browser_channel to Python: {} (config value: {:?})",
                  browser_channel, self.config.browser_channel);

            // Detect command type based on input structure
            if !obj.contains_key("command_type") {
                // If input has "steps" array, use script mode
                // Otherwise use prompt mode (act)
                let command_type = if obj.contains_key("steps") {
                    "script"
                } else {
                    "act"
                };

                obj.insert("command_type".to_string(), json!(command_type));
                debug!("Auto-detected command_type: {}", command_type);
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

        // Log Python stderr (contains INFO logs and debug output)
        let stderr = String::from_utf8_lossy(&output.stderr);
        if !stderr.is_empty() {
            // Log each line of stderr to preserve formatting
            for line in stderr.lines() {
                info!("Python: {}", line);
            }
        }

        // Check exit status
        if !output.status.success() {
            error!("Python subprocess failed with exit code: {:?}", output.status.code());
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
    async fn test_build_command_prompt_mode() {
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
            browser_channel: Some("chrome".to_string()),
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
        assert_eq!(command.get("browser_channel").unwrap(), "chrome");
    }

    #[tokio::test]
    async fn test_build_command_script_mode() {
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
            browser_channel: Some("chrome".to_string()),
        });

        let executor = NovaActExecutor {
            config,
            python_wrapper_path: PathBuf::from("/tmp/nova_act_wrapper.py"),
        };

        let input = json!({
            "name": "Test Script",
            "starting_page": "https://example.com",
            "steps": [
                {
                    "action": "act",
                    "prompt": "Click the button",
                    "description": "Click submit"
                }
            ]
        });

        let command = executor.build_command(input).unwrap();

        assert_eq!(command.get("name").unwrap(), "Test Script");
        assert_eq!(command.get("starting_page").unwrap(), "https://example.com");
        assert!(command.get("steps").unwrap().is_array());
        assert_eq!(command.get("s3_bucket").unwrap(), "browser-agent-recordings-prod");
        assert_eq!(command.get("aws_profile").unwrap(), "browser-agent");
        assert_eq!(command.get("record_video").unwrap(), true);
        assert_eq!(command.get("command_type").unwrap(), "script");
        assert_eq!(command.get("browser_channel").unwrap(), "chrome");
    }

    #[tokio::test]
    async fn test_browser_channel_defaults_to_platform() {
        // Test that browser_channel defaults to platform default when None
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
            browser_channel: None,  // Not configured
        });

        let executor = NovaActExecutor {
            config,
            python_wrapper_path: PathBuf::from("/tmp/nova_act_wrapper.py"),
        };

        let input = json!({
            "prompt": "Test prompt"
        });

        let command = executor.build_command(input).unwrap();

        // Should default to platform-specific browser
        #[cfg(target_os = "windows")]
        assert_eq!(command.get("browser_channel").unwrap(), "msedge");

        #[cfg(not(target_os = "windows"))]
        assert_eq!(command.get("browser_channel").unwrap(), "chrome");
    }
}
