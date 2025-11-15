use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;
use tokio::process::Command;

use crate::config::Config;
use crate::paths::AppPaths;

/// Result of script execution
#[derive(Debug, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub success: bool,
    pub output: Option<String>,
    pub error: Option<String>,
}

/// Configuration for a single script execution
#[derive(Debug, Clone)]
pub struct ScriptExecutionConfig {
    pub script_content: String,
    pub aws_profile: String,
    pub s3_bucket: Option<String>,
    pub headless: bool,
    pub browser_channel: Option<String>,
    pub navigation_timeout: u64,
    pub user_data_dir: Option<PathBuf>,
}

/// Unified script executor for both Activity Poller and Test UI
///
/// This provides a single source of truth for:
/// - Browser engine selection (Nova Act vs OpenAI Computer Agent)
/// - Environment variable configuration
/// - Python subprocess execution
/// - Result parsing
pub struct ScriptExecutor {
    config: Arc<Config>,
    python_path: PathBuf,
    script_executor_path: PathBuf,
}

impl ScriptExecutor {
    /// Create new script executor
    ///
    /// This will:
    /// 1. Find the Python executable from the venv
    /// 2. Find the script_executor.py file
    /// 3. Configure environment variables based on config.browser_engine
    pub fn new(config: Arc<Config>) -> Result<Self> {
        // Find Python executable
        let python_path = Self::find_python_executable()
            .context("Failed to find Python executable")?;

        // Find script_executor.py
        let script_executor_path = Self::find_script_executor()
            .context("Failed to find script_executor.py")?;

        // Set environment variables based on config
        Self::configure_environment(&config)?;

        log::info!("✓ ScriptExecutor initialized");
        log::debug!("  Python: {}", python_path.display());
        log::debug!("  Script executor: {}", script_executor_path.display());

        Ok(Self {
            config,
            python_path,
            script_executor_path,
        })
    }

    /// Configure environment variables for Python subprocess
    ///
    /// Sets environment variables based on config.browser_engine:
    /// - For "computer_agent": Sets OPENAI_API_KEY, OPENAI_MODEL, etc.
    /// - For "nova_act": Sets NOVA_ACT_API_KEY
    fn configure_environment(config: &Config) -> Result<()> {
        // Determine which browser engine to use
        let use_computer_agent = config.browser_engine == "computer_agent";
        std::env::set_var("USE_COMPUTER_AGENT", use_computer_agent.to_string());

        if use_computer_agent {
            // Set OpenAI Computer Agent configuration
            if let Some(ref api_key) = config.openai_api_key {
                std::env::set_var("OPENAI_API_KEY", api_key);
            } else {
                log::warn!("OpenAI API key not set in config, Python will check environment");
            }

            std::env::set_var("OPENAI_MODEL", &config.openai_model);
            std::env::set_var("ENABLE_REPLANNING", config.enable_replanning.to_string());
            std::env::set_var("MAX_REPLANS", config.max_replans.to_string());

            log::info!("✓ Configured OpenAI Computer Agent");
            log::info!("  Model: {}", config.openai_model);
            log::info!("  Replanning: {} (max: {})",
                config.enable_replanning,
                config.max_replans
            );
        } else {
            // Set Nova Act configuration
            if let Some(ref api_key) = config.nova_act_api_key {
                std::env::set_var("NOVA_ACT_API_KEY", api_key);
            } else {
                log::warn!("Nova Act API key not set in config, Python will check environment");
            }

            log::info!("✓ Configured Nova Act");
        }

        Ok(())
    }

    /// Execute a browser automation script
    pub async fn execute(&self, exec_config: ScriptExecutionConfig) -> Result<ExecutionResult> {
        // Write script to temp file
        let temp_file = tempfile::NamedTempFile::new()
            .context("Failed to create temporary file for script")?;

        std::fs::write(temp_file.path(), &exec_config.script_content)
            .context("Failed to write script to temporary file")?;

        // Build command
        let mut cmd = Command::new(&self.python_path);
        cmd.arg(&self.script_executor_path);
        cmd.arg("--script").arg(temp_file.path());
        cmd.arg("--aws-profile").arg(&exec_config.aws_profile);
        cmd.arg("--navigation-timeout").arg(exec_config.navigation_timeout.to_string());

        if exec_config.headless {
            cmd.arg("--headless");
        }

        if let Some(ref bucket) = exec_config.s3_bucket {
            cmd.arg("--s3-bucket").arg(bucket);
        }

        if let Some(ref channel) = exec_config.browser_channel {
            cmd.arg("--browser-channel").arg(channel);
        }

        if let Some(ref user_data_dir) = exec_config.user_data_dir {
            cmd.arg("--user-data-dir").arg(user_data_dir);
        }

        // Log execution details
        self.log_execution_details(&exec_config);

        // Execute subprocess
        log::debug!("Spawning Python subprocess...");
        let output = cmd
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .await
            .context("Failed to execute Python subprocess")?;

        log::debug!("Python subprocess completed");

        // Parse and return results
        self.parse_output(output)
    }

    /// Log execution details for debugging
    fn log_execution_details(&self, exec_config: &ScriptExecutionConfig) {
        log::info!("═══ Script Execution ═══");

        let engine_name = match self.config.browser_engine.as_str() {
            "computer_agent" => format!("OpenAI Computer Agent ({})", self.config.openai_model),
            _ => "Nova Act".to_string(),
        };
        log::info!("Engine: {}", engine_name);

        log::info!("AWS Profile: {}", exec_config.aws_profile);
        log::info!("Headless: {}", exec_config.headless);

        if let Some(ref channel) = exec_config.browser_channel {
            log::info!("Browser: {}", channel);
        }

        if let Some(ref bucket) = exec_config.s3_bucket {
            log::info!("S3 Bucket: {}", bucket);
        }

        if let Some(ref user_data_dir) = exec_config.user_data_dir {
            log::info!("User Data Dir: {}", user_data_dir.display());
        }

        log::info!("Navigation Timeout: {}ms", exec_config.navigation_timeout);
        log::info!("═════════════════════");
    }

    /// Parse Python subprocess output
    fn parse_output(&self, output: std::process::Output) -> Result<ExecutionResult> {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        log::debug!("Script execution stdout: {}", stdout);
        if !stderr.is_empty() {
            log::debug!("Script execution stderr: {}", stderr);
        }

        if output.status.success() {
            log::info!("✓ Script execution completed successfully!");
            Ok(ExecutionResult {
                success: true,
                output: Some(stdout.to_string()),
                error: None,
            })
        } else {
            log::error!("✗ Script execution failed with exit code: {:?}", output.status.code());
            log::error!("  stdout: {}", stdout);
            log::error!("  stderr: {}", stderr);

            Ok(ExecutionResult {
                success: false,
                output: Some(stdout.to_string()),
                error: Some(stderr.to_string()),
            })
        }
    }

    /// Find Python executable from venv
    fn find_python_executable() -> Result<PathBuf> {
        let paths = AppPaths::new()?;
        let venv_dir = paths.python_env_dir();

        #[cfg(target_os = "windows")]
        let python_path = venv_dir.join("Scripts").join("python.exe");

        #[cfg(not(target_os = "windows"))]
        let python_path = venv_dir.join("bin").join("python");

        if python_path.exists() {
            log::debug!("Found Python executable at: {}", python_path.display());
            Ok(python_path)
        } else {
            anyhow::bail!("Python venv not found at: {}", venv_dir.display());
        }
    }

    /// Find script_executor.py or computer_agent_script_executor.py based on config
    fn find_script_executor() -> Result<PathBuf> {
        // Determine which script to use based on USE_COMPUTER_AGENT env var
        let use_computer_agent = std::env::var("USE_COMPUTER_AGENT")
            .ok()
            .and_then(|v| v.parse::<bool>().ok())
            .unwrap_or(false);

        let script_name = if use_computer_agent {
            "computer_agent_script_executor.py"
        } else {
            "script_executor.py"
        };

        log::debug!("Looking for script executor: {}", script_name);

        // Try to find script in various locations
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                #[cfg(target_os = "macos")]
                let search_paths = vec![
                    exe_dir.join(format!("../Resources/python/{}", script_name)),
                    exe_dir.join(format!("../python/{}", script_name)),
                ];

                #[cfg(target_os = "linux")]
                let search_paths = vec![
                    exe_dir.join(format!("python/{}", script_name)),
                    exe_dir.join(format!("resources/python/{}", script_name)),
                    exe_dir.join(format!("_up_/python/{}", script_name)),
                    exe_dir.join(format!("../python/{}", script_name)),
                ];

                #[cfg(target_os = "windows")]
                let search_paths = vec![
                    exe_dir.join(format!("python\\{}", script_name)),
                    exe_dir.join(format!("resources\\python\\{}", script_name)),
                    exe_dir.join(format!("_up_\\python\\{}", script_name)),
                    exe_dir.join(format!("..\\python\\{}", script_name)),
                ];

                for path in &search_paths {
                    log::debug!("Checking for {} at: {}", script_name, path.display());
                    if path.exists() {
                        log::info!("✓ Found {} at: {}", script_name, path.display());
                        return Ok(path.canonicalize()?);
                    }
                }
            }
        }

        // Try AppPaths as fallback
        if let Ok(paths) = AppPaths::new() {
            let python_scripts_dir = paths.python_scripts_dir();
            let script_path = python_scripts_dir.join(script_name);
            if script_path.exists() {
                log::info!("✓ Found {} via AppPaths at: {}", script_name, script_path.display());
                return Ok(script_path);
            }
        }

        anyhow::bail!("Could not find {} in any expected location", script_name);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_environment_configuration() {
        // Test OpenAI Computer Agent config
        let config = Config {
            browser_engine: "computer_agent".to_string(),
            openai_api_key: Some("test-key".to_string()),
            openai_model: "gpt-4o-mini".to_string(),
            enable_replanning: true,
            max_replans: 2,
            ..Config::default_minimal()
        };

        ScriptExecutor::configure_environment(&Arc::new(config)).unwrap();

        assert_eq!(std::env::var("USE_COMPUTER_AGENT").unwrap(), "true");
        assert_eq!(std::env::var("OPENAI_API_KEY").unwrap(), "test-key");
        assert_eq!(std::env::var("OPENAI_MODEL").unwrap(), "gpt-4o-mini");
        assert_eq!(std::env::var("ENABLE_REPLANNING").unwrap(), "true");
        assert_eq!(std::env::var("MAX_REPLANS").unwrap(), "2");
    }

    #[test]
    fn test_nova_act_configuration() {
        let config = Config {
            browser_engine: "nova_act".to_string(),
            nova_act_api_key: Some("nova-key".to_string()),
            ..Config::default_minimal()
        };

        ScriptExecutor::configure_environment(&Arc::new(config)).unwrap();

        assert_eq!(std::env::var("USE_COMPUTER_AGENT").unwrap(), "false");
        assert_eq!(std::env::var("NOVA_ACT_API_KEY").unwrap(), "nova-key");
    }
}
