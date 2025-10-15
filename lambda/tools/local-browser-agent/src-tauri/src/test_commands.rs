use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::fs;
use std::sync::Arc;
use jsonschema::JSONSchema;
use url::Url;
use tauri::State;

use crate::config::Config;

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
    let current_dir = std::env::current_dir()
        .context("Failed to get current directory")?;

    // Try different possible locations
    let locations = vec![
        current_dir.join("examples"),
        current_dir.join("../examples"),
        current_dir.join("../../examples"),
    ];

    for path in &locations {
        if path.exists() && path.is_dir() {
            return Ok(path.canonicalize()?);
        }
    }

    // If not found in dev mode, try relative to executable (release mode)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let examples_path = exe_dir.join("../examples");
            if examples_path.exists() {
                return Ok(examples_path.canonicalize()?);
            }
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
    let current_dir = std::env::current_dir()
        .context("Failed to get current directory")?;

    let locations = vec![
        current_dir.join("python/script_executor.py"),
        current_dir.join("../python/script_executor.py"),
        current_dir.join("../../python/script_executor.py"),
    ];

    for path in &locations {
        if path.exists() {
            return Ok(path.canonicalize()?);
        }
    }

    // Try relative to executable (release mode)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let script_path = exe_dir.join("../python/script_executor.py");
            if script_path.exists() {
                return Ok(script_path.canonicalize()?);
            }
        }
    }

    anyhow::bail!("Could not find script_executor.py")
}

/// Check if uvx is available
fn is_uvx_available() -> bool {
    std::process::Command::new("uvx")
        .arg("--version")
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
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
        let aws_profile = config.aws_profile.trim().to_string();
        let s3_bucket = Some(config.s3_bucket.trim().to_string());
        let nova_act_api_key = config.nova_act_api_key.clone();
        let headless = config.headless;

        // Find Python script executor
        let script_executor = find_script_executor()
            .map_err(|e| format!("Failed to find script_executor.py: {}", e))?;

        // Write script to temporary file
        let temp_file = tempfile::NamedTempFile::new()
            .map_err(|e| format!("Failed to create temp file: {}", e))?;

        fs::write(temp_file.path(), &script)
            .map_err(|e| format!("Failed to write script to temp file: {}", e))?;

        // Check if uvx is available
        let use_uvx = is_uvx_available();

        log::info!("Executing browser script: {}", parsed.name);
        log::debug!("Using uvx: {}", use_uvx);
        log::debug!("AWS Profile: {}", aws_profile);
        log::debug!("Script executor: {:?}", script_executor);
        log::debug!("Script file: {:?}", temp_file.path());

        let mut cmd = if use_uvx {
            let mut c = Command::new("uvx");
            c.arg("--from").arg("nova-act").arg("python").arg(&script_executor);
            c
        } else {
            let mut c = Command::new("python3");
            c.arg(&script_executor);
            c
        };

        // Add common arguments
        cmd.arg("--script").arg(temp_file.path());
        cmd.arg("--aws-profile").arg(&aws_profile);

        // Only add --headless if config says to run headless
        if headless {
            cmd.arg("--headless");
        }

        if let Some(bucket) = s3_bucket {
            cmd.arg("--s3-bucket").arg(&bucket);
        }

        if let Some(api_key) = nova_act_api_key {
            if !api_key.trim().is_empty() {
                cmd.arg("--nova-act-api-key").arg(api_key.trim());
            }
        }

        let output = cmd
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .await
            .map_err(|e| {
                if use_uvx {
                    format!("Failed to execute via uvx: {}", e)
                } else {
                    format!("Failed to execute Python script: {}. Consider installing uv/uvx for automatic dependency management.", e)
                }
            })?;

        // Parse output
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        log::debug!("Script execution stdout: {}", stdout);
        if !stderr.is_empty() {
            log::debug!("Script execution stderr: {}", stderr);
        }

        if output.status.success() {
            Ok(ExecutionResult {
                success: true,
                output: Some(stdout.to_string()),
                error: None,
            })
        } else {
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

            Ok(ExecutionResult {
                success: false,
                output: if !stdout.is_empty() { Some(stdout.to_string()) } else { None },
                error: Some(error_msg),
            })
        }
    }
}
