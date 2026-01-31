use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::Command;
use tokio::task::JoinHandle;

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
        // IMPORTANT: Set environment variables FIRST, before finding script executor
        // The script executor selection depends on USE_COMPUTER_AGENT env var
        Self::configure_environment(&config)?;

        // Find Python executable
        let python_path = Self::find_python_executable()
            .context("Failed to find Python executable")?;

        // Find script_executor.py (now that env vars are set)
        let script_executor_path = Self::find_script_executor()
            .context("Failed to find script_executor.py")?;

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
        log::info!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        log::info!("Configuring Environment for Script Execution:");
        log::info!("  Config browser_engine: '{}'", config.browser_engine);

        // Determine which browser engine to use
        let use_computer_agent = config.browser_engine == "computer_agent";
        log::info!("  Computed use_computer_agent: {}", use_computer_agent);

        std::env::set_var("USE_COMPUTER_AGENT", use_computer_agent.to_string());
        log::info!("  Set USE_COMPUTER_AGENT env var to: {}", use_computer_agent);

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

        // Execute subprocess with real-time output streaming
        log::info!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        log::info!("Spawning Python subprocess...");
        log::info!("  Python: {}", self.python_path.display());
        log::info!("  Script: {}", self.script_executor_path.display());
        log::info!("  Temp file: {}", temp_file.path().display());
        log::info!("  Command: {} {} --script {} --aws-profile {} --navigation-timeout {}{}{}{}{}",
            self.python_path.display(),
            self.script_executor_path.display(),
            temp_file.path().display(),
            exec_config.aws_profile,
            exec_config.navigation_timeout,
            if exec_config.headless { " --headless" } else { "" },
            if let Some(ref bucket) = exec_config.s3_bucket { format!(" --s3-bucket {}", bucket) } else { String::new() },
            if let Some(ref channel) = exec_config.browser_channel { format!(" --browser-channel {}", channel) } else { String::new() },
            if let Some(ref user_data_dir) = exec_config.user_data_dir { format!(" --user-data-dir {}", user_data_dir.display()) } else { String::new() }
        );
        log::info!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

        // Spawn process and stream output in real-time
        log::info!("Attempting to spawn process...");
        let mut child = match cmd
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
        {
            Ok(child) => {
                log::info!("✓ Process spawned successfully with PID: {}", child.id().unwrap_or(0));
                child
            }
            Err(e) => {
                log::error!("✗ Failed to spawn Python subprocess: {}", e);
                log::error!("  Python path exists: {}", self.python_path.exists());
                log::error!("  Script path exists: {}", self.script_executor_path.exists());
                log::error!("  Temp file exists: {}", temp_file.path().exists());
                return Err(anyhow::anyhow!("Failed to spawn Python subprocess: {}", e));
            }
        };

        // Get handles for stdout and stderr
        let stdout = child.stdout.take().context("Failed to get stdout")?;
        let stderr = child.stderr.take().context("Failed to get stderr")?;

        // Stream stdout in real-time
        let stdout_handle = tokio::spawn(async move {
            use tokio::io::{AsyncBufReadExt, BufReader};
            let mut reader = BufReader::new(stdout).lines();
            let mut output = Vec::new();

            while let Ok(Some(line)) = reader.next_line().await {
                // Log each line immediately for real-time feedback
                log::info!("[Python stdout] {}", line);
                output.push(line);
            }

            output.join("\n")
        });

        // Stream stderr in real-time
        let stderr_handle = tokio::spawn(async move {
            use tokio::io::{AsyncBufReadExt, BufReader};
            let mut reader = BufReader::new(stderr).lines();
            let mut output = Vec::new();

            while let Ok(Some(line)) = reader.next_line().await {
                // Log each line immediately - this catches early Python errors!
                log::info!("[Python stderr] {}", line);
                output.push(line);
            }

            output.join("\n")
        });

        // Wait for process to complete
        let status = child.wait().await
            .context("Failed to wait for Python subprocess")?;

        // Collect all output
        let stdout_output = stdout_handle.await
            .context("Failed to join stdout task")?;
        let stderr_output = stderr_handle.await
            .context("Failed to join stderr task")?;

        log::debug!("Python subprocess completed with status: {:?}", status);

        // Return results
        if status.success() {
            log::info!("✓ Script execution completed successfully!");
            Ok(ExecutionResult {
                success: true,
                output: Some(stdout_output),
                error: None,
            })
        } else {
            log::error!("✗ Script execution failed with exit code: {:?}", status.code());

            Ok(ExecutionResult {
                success: false,
                output: Some(stdout_output),
                error: Some(stderr_output),
            })
        }
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
        let use_computer_agent_str = std::env::var("USE_COMPUTER_AGENT")
            .unwrap_or_else(|_| "not set".to_string());
        let use_computer_agent = use_computer_agent_str.parse::<bool>().unwrap_or(false);

        log::info!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        log::info!("Script Executor Selection:");
        log::info!("  USE_COMPUTER_AGENT env var: {}", use_computer_agent_str);
        log::info!("  Parsed value: {}", use_computer_agent);

        // Route to wrapper files which handle format detection and routing
        // - nova_act_wrapper.py: Routes Nova Act format scripts
        // - computer_agent_wrapper.py: Routes both legacy Computer Agent and new OpenAI Playwright formats
        let script_name = if use_computer_agent {
            "computer_agent_wrapper.py"
        } else {
            "nova_act_wrapper.py"
        };

        log::info!("  Selected wrapper: {}", script_name);
        log::info!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

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

/// Persistent script executor that keeps the browser alive between workflow runs.
///
/// Uses NDJSON protocol over stdin/stdout to communicate with the Python server mode:
/// - Writes one JSON line to stdin = one workflow request
/// - Reads one JSON line from stdout = result
/// - Stderr is streamed in real-time via a background task
/// - EOF on stdin (drop) = shutdown signal
pub struct PersistentScriptExecutor {
    child: Option<tokio::process::Child>,
    stdin: Option<tokio::process::ChildStdin>,
    stdout_lines: Option<tokio::io::Lines<BufReader<tokio::process::ChildStdout>>>,
    stderr_handle: Option<JoinHandle<()>>,
}

impl PersistentScriptExecutor {
    /// Start a persistent Python session in server mode.
    ///
    /// Spawns the Python process with `--server-mode`, sends the first script
    /// to initialize the browser, and waits for the `{"status": "ready"}` signal.
    ///
    /// Returns the executor and the result of the first script execution.
    pub async fn start(
        config: Arc<Config>,
        exec_config: ScriptExecutionConfig,
    ) -> Result<(Self, ExecutionResult)> {
        // Configure environment (same as ScriptExecutor)
        ScriptExecutor::configure_environment(&config)?;

        let python_path = ScriptExecutor::find_python_executable()
            .context("Failed to find Python executable")?;
        let script_executor_path = ScriptExecutor::find_script_executor()
            .context("Failed to find script_executor.py")?;

        // Build command with --server-mode
        let mut cmd = Command::new(&python_path);
        cmd.arg(&script_executor_path);
        cmd.arg("--server-mode");
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

        log::info!("Starting persistent Python session in server mode...");
        log::info!("  Python: {}", python_path.display());
        log::info!("  Script: {}", script_executor_path.display());

        let mut child = cmd
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .context("Failed to spawn Python subprocess in server mode")?;

        log::info!("✓ Persistent process spawned with PID: {}", child.id().unwrap_or(0));

        let stdin = child.stdin.take().context("Failed to get stdin")?;
        let stdout = child.stdout.take().context("Failed to get stdout")?;
        let stderr = child.stderr.take().context("Failed to get stderr")?;

        // Background task to stream stderr
        let stderr_handle = tokio::spawn(async move {
            let mut reader = BufReader::new(stderr).lines();
            while let Ok(Some(line)) = reader.next_line().await {
                log::info!("[Persistent Python stderr] {}", line);
            }
        });

        let mut stdout_lines = BufReader::new(stdout).lines();

        // Send the first script to trigger browser init
        let mut stdin_writer = stdin;
        let first_script_line = format!("{}\n", exec_config.script_content);
        stdin_writer
            .write_all(first_script_line.as_bytes())
            .await
            .context("Failed to write first script to stdin")?;
        stdin_writer.flush().await.context("Failed to flush stdin")?;

        // Wait for {"status": "ready"} signal
        log::info!("Waiting for ready signal from Python server...");
        let ready_line = stdout_lines
            .next_line()
            .await
            .context("Failed to read ready signal")?
            .context("Python process exited before sending ready signal")?;

        // Parse and validate the ready signal
        let ready_msg: serde_json::Value = serde_json::from_str(&ready_line)
            .context(format!("Failed to parse ready signal: {}", ready_line))?;

        if ready_msg.get("status").and_then(|s| s.as_str()) != Some("ready") {
            anyhow::bail!(
                "Expected {{\"status\": \"ready\"}} but got: {}",
                ready_line
            );
        }

        log::info!("✓ Persistent Python session is ready");

        // Now read the first script's result
        let first_result_line = stdout_lines
            .next_line()
            .await
            .context("Failed to read first script result")?
            .context("Python process exited before sending first result")?;

        log::info!("First script result received ({}B)", first_result_line.len());

        // Parse the first result
        let first_result_json: serde_json::Value = serde_json::from_str(&first_result_line)
            .context("Failed to parse first script result")?;
        let first_success = first_result_json.get("success").and_then(|v| v.as_bool()).unwrap_or(false);
        let first_result = ExecutionResult {
            success: first_success,
            output: Some(first_result_line),
            error: if !first_success {
                first_result_json.get("error").and_then(|e| e.as_str()).map(String::from)
            } else {
                None
            },
        };

        let executor = Self {
            child: Some(child),
            stdin: Some(stdin_writer),
            stdout_lines: Some(stdout_lines),
            stderr_handle: Some(stderr_handle),
        };

        Ok((executor, first_result))
    }

    /// Execute a script on the persistent browser session.
    ///
    /// Writes the script JSON as a single line to stdin, reads the result
    /// JSON line from stdout.
    pub async fn execute(&mut self, script_json: &str) -> Result<ExecutionResult> {
        let stdin = self.stdin.as_mut().context("Persistent session not started or already stopped")?;
        let stdout_lines = self.stdout_lines.as_mut().context("Persistent session not started or already stopped")?;

        // Write script as single JSON line
        let line = format!("{}\n", script_json.trim());
        stdin
            .write_all(line.as_bytes())
            .await
            .context("Failed to write script to persistent session")?;
        stdin.flush().await.context("Failed to flush stdin")?;

        log::info!("Sent script to persistent session, waiting for result...");

        // Read result line
        let result_line = stdout_lines
            .next_line()
            .await
            .context("Failed to read result from persistent session")?
            .context("Python process exited unexpectedly")?;

        log::info!("Received result from persistent session ({}B)", result_line.len());

        // Parse the result
        let result: serde_json::Value = serde_json::from_str(&result_line)
            .context(format!("Failed to parse result JSON: {}", &result_line[..result_line.len().min(200)]))?;

        let success = result.get("success").and_then(|v| v.as_bool()).unwrap_or(false);

        Ok(ExecutionResult {
            success,
            output: Some(result_line),
            error: if !success {
                result.get("error").and_then(|e| e.as_str()).map(String::from)
            } else {
                None
            },
        })
    }

    /// Stop the persistent session.
    ///
    /// Drops stdin (sends EOF to Python), waits for the process to exit.
    pub async fn stop(&mut self) -> Result<()> {
        log::info!("Stopping persistent Python session...");

        // Drop stdin to signal EOF
        self.stdin.take();
        self.stdout_lines.take();

        // Wait for process to exit
        if let Some(mut child) = self.child.take() {
            match tokio::time::timeout(
                std::time::Duration::from_secs(30),
                child.wait(),
            )
            .await
            {
                Ok(Ok(status)) => {
                    log::info!("Persistent Python process exited with status: {:?}", status);
                }
                Ok(Err(e)) => {
                    log::error!("Error waiting for persistent Python process: {}", e);
                }
                Err(_) => {
                    log::warn!("Persistent Python process did not exit within 30s, killing...");
                    let _ = child.kill().await;
                }
            }
        }

        // Wait for stderr reader to finish
        if let Some(handle) = self.stderr_handle.take() {
            let _ = handle.await;
        }

        log::info!("✓ Persistent session stopped");
        Ok(())
    }

    /// Check if the persistent session is still running.
    pub fn is_running(&mut self) -> bool {
        if let Some(ref mut child) = self.child {
            // try_wait returns Ok(Some(status)) if exited, Ok(None) if still running
            match child.try_wait() {
                Ok(Some(_)) => false,
                Ok(None) => true,
                Err(_) => false,
            }
        } else {
            false
        }
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
