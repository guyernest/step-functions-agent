use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::fs;
use std::sync::Arc;
use jsonschema::JSONSchema;
use url::Url;
use tauri::State;

use crate::config::Config;
use crate::paths::AppPaths;

#[derive(Debug, Serialize, Deserialize)]
pub struct BrowserScript {
    pub name: String,
    pub description: String,
    pub starting_page: String,
    pub abort_on_error: bool,
    pub steps: Vec<BrowserStep>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "action", rename_all = "snake_case")]
pub enum BrowserStep {
    Act {
        prompt: String,
        description: Option<String>,
    },
    ActWithSchema {
        prompt: String,
        schema: serde_json::Value,
        description: Option<String>,
    },
    Screenshot {
        description: Option<String>,
    },
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ValidationResult {
    pub valid: bool,
    pub errors: Option<Vec<String>>,
    pub warnings: Option<Vec<String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub success: bool,
    pub output: Option<String>,
    pub error: Option<String>,
}

/// Find examples directory
fn find_examples_dir() -> Result<PathBuf> {
    // Try AppPaths first (recommended for production)
    if let Ok(paths) = AppPaths::new() {
        let examples_dir = paths.examples_dir();
        if examples_dir.exists() {
            log::info!("Found examples via AppPaths at: {}", examples_dir.display());
            return Ok(examples_dir);
        }
    }

    // Try relative to executable (release mode / app bundle - fallback)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            // For macOS app bundle
            #[cfg(target_os = "macos")]
            let example_paths = vec![
                exe_dir.join("../Resources/examples"),
                exe_dir.join("../examples"),
            ];

            // For Linux - check same locations as Python scripts
            #[cfg(target_os = "linux")]
            let example_paths = vec![
                exe_dir.join("examples"),
                exe_dir.join("resources/examples"),
                exe_dir.join("_up_/examples"),
                exe_dir.join("../examples"),
            ];

            // For Windows - check same locations as Python scripts
            #[cfg(target_os = "windows")]
            let example_paths = vec![
                exe_dir.join("examples"),                    // Same directory as exe
                exe_dir.join("resources\\examples"),         // resources subdirectory
                exe_dir.join("_up_\\examples"),              // _up_ subdirectory (matches Python)
                exe_dir.join("..\\examples"),                // parent directory
            ];

            for examples_path in &example_paths {
                log::info!("Checking for examples at: {}", examples_path.display());
                if examples_path.exists() && examples_path.is_dir() {
                    log::info!("✓ Found examples at: {}", examples_path.display());
                    return Ok(examples_path.canonicalize()?);
                }
            }
        }
    }

    // Fallback: try current directory (for development)
    let current_dir = std::env::current_dir()
        .context("Failed to get current directory")?;

    let dev_locations = vec![
        current_dir.join("examples"),
        current_dir.join("../examples"),
        current_dir.join("../../examples"),
    ];

    for path in &dev_locations {
        if path.exists() && path.is_dir() {
            return Ok(path.canonicalize()?);
        }
    }

    anyhow::bail!("Could not find examples directory")
}

/// Tauri command to list example browser scripts
#[tauri::command]
pub fn list_browser_examples() -> Result<Vec<String>, String> {
    let examples_dir = find_examples_dir()
        .map_err(|e| format!("Failed to find examples directory: {}", e))?;

    let mut examples = Vec::new();

    let entries = fs::read_dir(&examples_dir)
        .map_err(|e| format!("Failed to read examples directory: {}", e))?;

    for entry in entries {
        if let Ok(entry) = entry {
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("json") {
                if let Some(filename) = path.file_name().and_then(|s| s.to_str()) {
                    examples.push(filename.to_string());
                }
            }
        }
    }

    examples.sort();
    Ok(examples)
}

/// Tauri command to load an example browser script
#[tauri::command]
pub fn load_browser_example(filename: String) -> Result<String, String> {
    let examples_dir = find_examples_dir()
        .map_err(|e| format!("Failed to find examples directory: {}", e))?;

    let script_path = examples_dir.join(&filename);

    if !script_path.exists() {
        return Err(format!("Example file not found: {}", filename));
    }

    fs::read_to_string(&script_path)
        .map_err(|e| format!("Failed to read example file: {}", e))
}

/// Deep validation helper for JSON Schema
fn validate_json_schema(schema: &serde_json::Value, step_num: usize) -> Vec<String> {
    let mut errors = Vec::new();

    // Try to compile the schema with jsonschema
    match JSONSchema::compile(schema) {
        Ok(_) => {
            // Schema is valid JSON Schema
        }
        Err(e) => {
            errors.push(format!("Step {}: Invalid JSON Schema - {}", step_num, e));
        }
    }

    // Additional checks for common issues
    if schema.is_object() {
        let obj = schema.as_object().unwrap();

        // Check if it has a type field
        if !obj.contains_key("type") && !obj.contains_key("$ref") && !obj.contains_key("properties") {
            errors.push(format!("Step {}: Schema should have 'type', 'properties', or '$ref' field", step_num));
        }

        // Warn about overly complex schemas
        let complexity = count_schema_nodes(schema);
        if complexity > 50 {
            errors.push(format!("Step {}: Schema is very complex ({} nodes). Consider simplifying.", step_num, complexity));
        }
    }

    errors
}

/// Count nodes in a JSON schema for complexity estimation
fn count_schema_nodes(value: &serde_json::Value) -> usize {
    match value {
        serde_json::Value::Object(obj) => {
            1 + obj.values().map(count_schema_nodes).sum::<usize>()
        }
        serde_json::Value::Array(arr) => {
            1 + arr.iter().map(count_schema_nodes).sum::<usize>()
        }
        _ => 1,
    }
}

/// Tauri command to validate a browser script
#[tauri::command]
pub fn validate_browser_script(script: String) -> Result<ValidationResult, String> {
    let mut errors = Vec::new();
    let mut warnings = Vec::new();

    // Try to parse as JSON
    let parsed: Result<BrowserScript, _> = serde_json::from_str(&script);

    match parsed {
        Ok(browser_script) => {
            // Validate name and description
            if browser_script.name.is_empty() {
                errors.push("Script must have a name".to_string());
            } else if browser_script.name.len() > 100 {
                warnings.push(format!("Script name is very long ({} chars)", browser_script.name.len()));
            }

            if browser_script.description.is_empty() {
                warnings.push("Script should have a description".to_string());
            }

            // Validate starting_page with proper URL parsing
            if browser_script.starting_page.is_empty() {
                errors.push("Script must have a starting_page URL".to_string());
            } else {
                match Url::parse(&browser_script.starting_page) {
                    Ok(url) => {
                        if url.scheme() != "http" && url.scheme() != "https" {
                            errors.push(format!("starting_page must use HTTP or HTTPS protocol, got: {}", url.scheme()));
                        }
                        if url.host_str().is_none() {
                            errors.push("starting_page must have a valid host".to_string());
                        }
                    }
                    Err(e) => {
                        errors.push(format!("starting_page is not a valid URL: {}", e));
                    }
                }
            }

            // Check if there are steps
            if browser_script.steps.is_empty() {
                errors.push("Script must have at least one step".to_string());
            } else if browser_script.steps.len() > 50 {
                warnings.push(format!("Script has many steps ({}). Consider breaking into smaller scripts.", browser_script.steps.len()));
            }

            // Validate each step
            for (idx, step) in browser_script.steps.iter().enumerate() {
                let step_num = idx + 1;
                match step {
                    BrowserStep::Act { prompt, .. } => {
                        if prompt.is_empty() {
                            errors.push(format!("Step {}: Act prompt cannot be empty", step_num));
                        } else if prompt.len() < 5 {
                            warnings.push(format!("Step {}: Act prompt is very short ({} chars)", step_num, prompt.len()));
                        } else if prompt.len() > 1000 {
                            warnings.push(format!("Step {}: Act prompt is very long ({} chars)", step_num, prompt.len()));
                        }

                        // Check for potentially unsafe content
                        let lower_prompt = prompt.to_lowercase();
                        if lower_prompt.contains("password") || lower_prompt.contains("credit card") {
                            warnings.push(format!("Step {}: Prompt mentions sensitive data (password/credit card)", step_num));
                        }
                    }
                    BrowserStep::ActWithSchema { prompt, schema, .. } => {
                        if prompt.is_empty() {
                            errors.push(format!("Step {}: Act prompt cannot be empty", step_num));
                        } else if prompt.len() < 5 {
                            warnings.push(format!("Step {}: Act prompt is very short ({} chars)", step_num, prompt.len()));
                        } else if prompt.len() > 1000 {
                            warnings.push(format!("Step {}: Act prompt is very long ({} chars)", step_num, prompt.len()));
                        }

                        // Deep validation of JSON Schema
                        let schema_errors = validate_json_schema(schema, step_num);
                        errors.extend(schema_errors);

                        // Basic schema structure check
                        if !schema.is_object() && !schema.get("type").is_some() {
                            errors.push(format!("Step {}: Schema must be a JSON object or have a 'type' field", step_num));
                        }
                    }
                    BrowserStep::Screenshot { .. } => {
                        // Screenshots always valid
                    }
                }
            }

            Ok(ValidationResult {
                valid: errors.is_empty(),
                errors: if errors.is_empty() { None } else { Some(errors) },
                warnings: if warnings.is_empty() { None } else { Some(warnings) },
            })
        }
        Err(e) => {
            errors.push(format!("Invalid JSON: {}", e));
            Ok(ValidationResult {
                valid: false,
                errors: Some(errors),
                warnings: None,
            })
        }
    }
}

/// Find Python script executor
fn find_script_executor() -> Result<PathBuf> {
    // Try relative to executable (release mode / app bundle)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            // For macOS app bundle
            #[cfg(target_os = "macos")]
            let script_paths = vec![
                exe_dir.join("../Resources/_up_/python/script_executor.py"),
                exe_dir.join("../Resources/python/script_executor.py"),
                exe_dir.join("../python/script_executor.py"),
            ];

            // For Linux - check same locations as other Python scripts
            #[cfg(target_os = "linux")]
            let script_paths = vec![
                exe_dir.join("python/script_executor.py"),
                exe_dir.join("resources/python/script_executor.py"),
                exe_dir.join("_up_/python/script_executor.py"),
                exe_dir.join("../python/script_executor.py"),
            ];

            // For Windows - check same locations as other Python scripts
            #[cfg(target_os = "windows")]
            let script_paths = vec![
                exe_dir.join("python\\script_executor.py"),
                exe_dir.join("resources\\python\\script_executor.py"),
                exe_dir.join("_up_\\python\\script_executor.py"),
                exe_dir.join("..\\python\\script_executor.py"),
            ];

            for script_path in &script_paths {
                log::info!("Checking for script_executor.py at: {}", script_path.display());
                if script_path.exists() {
                    log::info!("✓ Found script_executor.py at: {}", script_path.display());
                    return Ok(script_path.canonicalize()?);
                }
            }
        }
    }

    // Fallback: try current directory (for development)
    let current_dir = std::env::current_dir()
        .context("Failed to get current directory")?;

    let dev_locations = vec![
        current_dir.join("python/script_executor.py"),
        current_dir.join("../python/script_executor.py"),
        current_dir.join("../../python/script_executor.py"),
    ];

    for path in &dev_locations {
        if path.exists() {
            return Ok(path.canonicalize()?);
        }
    }

    anyhow::bail!("Could not find script_executor.py")
}

/// Find Python executable from venv
fn find_python_executable() -> Result<PathBuf> {
    use log::{info, error};

    // Try relative to executable (for release builds)
    if let Ok(exe_path) = std::env::current_exe() {
        info!("Executable path: {}", exe_path.display());

        if let Some(exe_dir) = exe_path.parent() {
            info!("Executable directory: {}", exe_dir.display());

            #[cfg(not(target_os = "windows"))]
            let venv_paths_release = vec![
                exe_dir.join("../Resources/_up_/python/.venv/bin/python"),  // macOS bundle (primary)
                exe_dir.join("../Resources/python/.venv/bin/python"),       // macOS bundle (alternative)
                exe_dir.join("../python/.venv/bin/python"),                 // Linux
            ];

            #[cfg(target_os = "windows")]
            let venv_paths_release = vec![
                exe_dir.join("python\\.venv\\Scripts\\python.exe"),
                exe_dir.join("resources\\python\\.venv\\Scripts\\python.exe"),
                exe_dir.join("_up_\\python\\.venv\\Scripts\\python.exe"),
                exe_dir.join("..\\python\\.venv\\Scripts\\python.exe"),
            ];

            info!("Searching for Python venv in app bundle...");
            for venv_python in &venv_paths_release {
                info!("Checking: {}", venv_python.display());

                if venv_python.exists() {
                    info!("✓ Found Python venv at: {}", venv_python.display());
                    // DO NOT canonicalize - we need to use the venv symlink directly
                    // so that Python loads the venv's site-packages
                    return Ok(venv_python.clone());
                }
            }

            error!("None of the expected venv paths exist");
        }
    }

    // No venv found - this is an error
    error!("Python venv not found in app bundle");
    anyhow::bail!(
        "Python virtual environment not found. Please run setup:\n\
         Use the 'Setup Python Environment' button in the Configuration screen"
    )
}

/// Tauri command to execute a browser script
#[tauri::command]
pub async fn execute_browser_script(
    script: String,
    dry_run: bool,
    config: State<'_, Arc<Config>>
) -> Result<ExecutionResult, String> {
    // Parse the script
    let parsed: BrowserScript = serde_json::from_str(&script)
        .map_err(|e| format!("Failed to parse script: {}", e))?;

    // Try to reload config from file to get latest values
    // (in case user saved config without restarting app)
    let current_config = {
        let config_path = Config::default_config_path().ok();

        if let Some(path) = config_path {
            if path.exists() {
                log::info!("Reloading config from file for script execution");
                match Config::from_file(&path) {
                    Ok(c) => Arc::new(c),
                    Err(e) => {
                        log::warn!("Failed to reload config from file, using startup config: {}", e);
                        Arc::clone(&config)
                    }
                }
            } else {
                Arc::clone(&config)
            }
        } else {
            log::info!("Config file not found, using startup config");
            Arc::clone(&config)
        }
    };

    if dry_run {
        // Dry run: just validate and return what would be executed
        let mut output = format!("[DRY RUN] Nova Act Script: {}\n", parsed.name);
        output.push_str(&format!("Description: {}\n", parsed.description));
        output.push_str(&format!("Starting Page: {}\n", parsed.starting_page));
        output.push_str(&format!("Steps to execute: {}\n\n", parsed.steps.len()));

        for (idx, step) in parsed.steps.iter().enumerate() {
            match step {
                BrowserStep::Act { prompt, description } => {
                    output.push_str(&format!("  {}. ACT: {}\n", idx + 1, prompt));
                    if let Some(desc) = description {
                        output.push_str(&format!("     ({})\n", desc));
                    }
                }
                BrowserStep::ActWithSchema { prompt, schema, description } => {
                    output.push_str(&format!("  {}. ACT_WITH_SCHEMA: {}\n", idx + 1, prompt));
                    output.push_str(&format!("     Schema: {}\n", serde_json::to_string_pretty(schema).unwrap_or_else(|_| "Invalid".to_string())));
                    if let Some(desc) = description {
                        output.push_str(&format!("     ({})\n", desc));
                    }
                }
                BrowserStep::Screenshot { description } => {
                    output.push_str(&format!("  {}. SCREENSHOT\n", idx + 1));
                    if let Some(desc) = description {
                        output.push_str(&format!("     ({})\n", desc));
                    }
                }
            }
            output.push_str("\n");
        }

        output.push_str("\n[DRY RUN] This script uses Nova Act for safe, high-level browser automation.\n");
        output.push_str("No Python code execution - only declarative prompts and JSON schemas.\n");

        Ok(ExecutionResult {
            success: true,
            output: Some(output),
            error: None,
        })
    } else {
        // Actual execution: call Python script executor
        use std::process::Stdio;
        use tokio::process::Command;

        // Get config to access AWS profile, Nova Act API key, and headless setting
        let aws_profile = current_config.aws_profile.trim().to_string();
        let s3_bucket = Some(current_config.s3_bucket.trim().to_string());
        let nova_act_api_key = current_config.nova_act_api_key.clone();
        let headless = current_config.headless;

        // Find Python script executor
        let script_executor = find_script_executor()
            .map_err(|e| format!("Failed to find script_executor.py: {}", e))?;

        // Write script to temporary file
        let temp_file = tempfile::NamedTempFile::new()
            .map_err(|e| format!("Failed to create temp file: {}", e))?;

        fs::write(temp_file.path(), &script)
            .map_err(|e| format!("Failed to write script to temp file: {}", e))?;

        // Find Python executable from venv
        log::info!("Executing browser script: {}", parsed.name);
        log::info!("Step 1: Finding Python executable...");
        let python_executable = find_python_executable()
            .map_err(|e| format!("Failed to find Python executable: {}", e))?;

        log::info!("✓ Found Python executable: {}", python_executable.display());
        log::debug!("AWS Profile: {}", aws_profile);
        log::debug!("Script executor: {:?}", script_executor);
        log::debug!("Script file: {:?}", temp_file.path());

        log::info!("Step 2: Preparing command...");
        let mut cmd = Command::new(python_executable);
        cmd.arg(&script_executor);

        // Add common arguments
        cmd.arg("--script").arg(temp_file.path());
        cmd.arg("--aws-profile").arg(&aws_profile);

        // Set navigation timeout to 60 seconds (60000 milliseconds)
        cmd.arg("--navigation-timeout").arg("60000");

        // Only add --headless if config says to run headless
        if headless {
            log::info!("Step 3: Running in headless mode");
            cmd.arg("--headless");
        } else {
            log::info!("Step 3: Running in visible mode (headless disabled)");
        }

        if let Some(bucket) = s3_bucket {
            log::info!("Step 4: S3 recording bucket configured: {}", bucket);
            cmd.arg("--s3-bucket").arg(&bucket);
        } else {
            log::info!("Step 4: No S3 recording bucket configured");
        }

        // Add browser channel if configured
        if let Some(ref browser_channel) = current_config.browser_channel {
            log::info!("Step 5: Browser channel: {}", browser_channel);
            cmd.arg("--browser-channel").arg(browser_channel);
        }

        if let Some(api_key) = nova_act_api_key {
            if !api_key.trim().is_empty() {
                log::info!("Step 6: Nova Act API key provided");
                cmd.arg("--nova-act-api-key").arg(api_key.trim());
            } else {
                log::info!("Step 5: Nova Act API key is empty, using environment variable");
            }
        } else {
            log::info!("Step 5: No Nova Act API key in config, using environment variable");
        }

        log::info!("Step 6: Spawning Python subprocess...");
        let output = cmd
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .await
            .map_err(|e| {
                log::error!("Failed to spawn Python subprocess: {}", e);
                format!("Failed to execute Python script: {}", e)
            })?;

        log::info!("Step 7: Python subprocess completed");

        // Parse output
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        log::info!("Step 8: Processing execution results...");
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

            // Combine stdout and stderr for better error visibility
            let mut error_msg = String::new();
            if !stderr.is_empty() {
                error_msg.push_str("STDERR:\n");
                error_msg.push_str(&stderr);
                error_msg.push_str("\n\n");
            }
            if !stdout.is_empty() {
                error_msg.push_str("STDOUT:\n");
                error_msg.push_str(&stdout);
                error_msg.push_str("\n\n");
            }
            error_msg.push_str(&format!("Exit code: {:?}", output.status.code()));

            log::error!("Error details: {}", error_msg);

            Ok(ExecutionResult {
                success: false,
                output: if !stdout.is_empty() { Some(stdout.to_string()) } else { None },
                error: Some(error_msg),
            })
        }
    }
}
