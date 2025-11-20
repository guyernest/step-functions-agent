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

    // First parse as generic JSON to detect format
    let json_value: serde_json::Value = match serde_json::from_str(&script) {
        Ok(v) => v,
        Err(e) => {
            errors.push(format!("Invalid JSON: {}", e));
            return Ok(ValidationResult {
                valid: false,
                errors: Some(errors),
                warnings: None,
            });
        }
    };

    // Detect format by checking first step OR if any step has workflow types
    let is_workflow_format = if let Some(steps) = json_value.get("steps").and_then(|s| s.as_array()) {
        if steps.is_empty() {
            false
        } else {
            // Check if ANY step uses workflow "type" field OR workflow action types
            steps.iter().any(|step| {
                if let Some(step_type) = step.get("type").and_then(|t| t.as_str()) {
                    // Workflow step types
                    matches!(step_type, "if" | "try" | "sequence" | "switch" | "goto")
                } else if let Some(action_type) = step.get("action").and_then(|a| a.as_str()) {
                    // Workflow action types (not Nova Act actions)
                    !matches!(action_type, "act" | "act_with_schema" | "screenshot")
                } else {
                    false
                }
            })
        }
    } else {
        false
    };

    if is_workflow_format {
        // Workflow format (OpenAI Playwright) - do basic validation without strict typing
        warnings.push("Using workflow format with OpenAI Playwright executor (validation is basic)".to_string());

        // Validate basic structure
        if let Some(name) = json_value.get("name").and_then(|n| n.as_str()) {
            if name.is_empty() {
                errors.push("Script must have a name".to_string());
            }
        } else {
            errors.push("Script missing 'name' field".to_string());
        }

        // Accept both starting_page (Nova Act) and starting_url (Progressive Escalation)
        let starting_url = json_value.get("starting_url")
            .or_else(|| json_value.get("starting_page"))
            .and_then(|s| s.as_str());

        if let Some(url) = starting_url {
            if url.is_empty() {
                errors.push("Script must have a starting URL".to_string());
            } else if let Err(e) = Url::parse(url) {
                errors.push(format!("Starting URL is not valid: {}", e));
            }
        } else {
            errors.push("Script missing 'starting_url' or 'starting_page' field".to_string());
        }

        if let Some(steps) = json_value.get("steps").and_then(|s| s.as_array()) {
            if steps.is_empty() {
                errors.push("Script must have at least one step".to_string());
            }
        } else {
            errors.push("Script missing 'steps' field".to_string());
        }

        return Ok(ValidationResult {
            valid: errors.is_empty(),
            errors: if errors.is_empty() { None } else { Some(errors) },
            warnings: if warnings.is_empty() { None } else { Some(warnings) },
        });
    }

    // Old Nova Act format - use strict validation
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

            // Validate starting URL with proper URL parsing
            if browser_script.starting_page.is_empty() {
                errors.push("Script must have a starting URL".to_string());
            } else {
                match Url::parse(&browser_script.starting_page) {
                    Ok(url) => {
                        if url.scheme() != "http" && url.scheme() != "https" {
                            errors.push(format!("Starting URL must use HTTP or HTTPS protocol, got: {}", url.scheme()));
                        }
                        if url.host_str().is_none() {
                            errors.push("Starting URL must have a valid host".to_string());
                        }
                    }
                    Err(e) => {
                        errors.push(format!("Starting URL is not valid: {}", e));
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

/// Tauri command to execute a browser script
#[tauri::command]
pub async fn execute_browser_script(
    script: String,
    dry_run: bool,
    config: State<'_, Arc<Config>>
) -> Result<ExecutionResult, String> {
    // Validate the script is valid JSON first
    let _: serde_json::Value = serde_json::from_str(&script)
        .map_err(|e| format!("Failed to parse script as JSON: {}", e))?;

    // We don't need to parse into BrowserScript anymore - just pass raw JSON to Python
    // The Python executor will handle format detection

    // Try to reload config from file to get latest values
    // (in case user saved config without restarting app)
    let current_config = {
        let config_path = AppPaths::new().ok().map(|p| p.user_config_file());

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
        // Dry run: just validate and return basic info
        let json_value: serde_json::Value = serde_json::from_str(&script)
            .map_err(|e| format!("Failed to parse script: {}", e))?;

        let name = json_value.get("name").and_then(|n| n.as_str()).unwrap_or("Unnamed");
        let description = json_value.get("description").and_then(|d| d.as_str()).unwrap_or("");
        let starting_url = json_value.get("starting_url")
            .or_else(|| json_value.get("starting_page"))
            .and_then(|s| s.as_str())
            .unwrap_or("");
        let steps_count = json_value.get("steps").and_then(|s| s.as_array()).map(|a| a.len()).unwrap_or(0);

        let mut output = format!("[DRY RUN] Browser Script: {}\n", name);
        output.push_str(&format!("Description: {}\n", description));
        output.push_str(&format!("Starting URL: {}\n", starting_url));
        output.push_str(&format!("Steps to execute: {}\n\n", steps_count));
        output.push_str("[DRY RUN] Script validated successfully. Ready for execution.\n");

        Ok(ExecutionResult {
            success: true,
            output: Some(output),
            error: None,
        })
    } else {
        // Actual execution: use unified ScriptExecutor
        use crate::script_executor::{ScriptExecutor, ScriptExecutionConfig};

        // Extract script name for logging
        let json_value: serde_json::Value = serde_json::from_str(&script)
            .map_err(|e| format!("Failed to parse script: {}", e))?;
        let script_name = json_value.get("name").and_then(|n| n.as_str()).unwrap_or("Unnamed");

        log::info!("Executing browser script: {}", script_name);

        // Check if script specifies a profile in session.profile_name
        // If so, resolve it and override config.user_data_dir
        let resolved_user_data_dir = if let Some(session) = json_value.get("session") {
            if let Some(profile_name) = session.get("profile_name").and_then(|p| p.as_str()) {
                log::info!("Script specifies profile: {}", profile_name);

                // Resolve profile name to directory path
                if let Ok(app_paths) = AppPaths::new() {
                    let profile_path = app_paths.browser_profiles_dir().join(profile_name);
                    if profile_path.exists() {
                        log::info!("✓ Resolved profile to: {}", profile_path.display());
                        Some(profile_path)
                    } else {
                        log::warn!("⚠ Profile directory not found: {}. Browser will start without profile.", profile_path.display());
                        current_config.user_data_dir.clone()
                    }
                } else {
                    log::warn!("⚠ Failed to resolve profile path. Browser will start without profile.");
                    current_config.user_data_dir.clone()
                }
            } else {
                current_config.user_data_dir.clone()
            }
        } else {
            current_config.user_data_dir.clone()
        };

        // Create unified script executor (handles engine selection automatically)
        let executor = ScriptExecutor::new(Arc::clone(&current_config))
            .map_err(|e| format!("Failed to initialize script executor: {}", e))?;

        // Prepare execution configuration
        let exec_config = ScriptExecutionConfig {
            script_content: script.clone(),
            aws_profile: current_config.aws_profile.trim().to_string(),
            s3_bucket: if current_config.s3_bucket.is_empty() {
                None
            } else {
                Some(current_config.s3_bucket.trim().to_string())
            },
            headless: current_config.headless,
            browser_channel: current_config.browser_channel.clone(),
            navigation_timeout: 60000, // 60 seconds
            user_data_dir: resolved_user_data_dir, // Use resolved profile path
        };

        // Execute the script (ScriptExecutor will select the right engine)
        let script_result = executor.execute(exec_config).await
            .map_err(|e| format!("Script execution failed: {}", e))?;

        // Convert from script_executor::ExecutionResult to test_commands::ExecutionResult
        Ok(ExecutionResult {
            success: script_result.success,
            output: script_result.output,
            error: script_result.error,
        })
    }
}
