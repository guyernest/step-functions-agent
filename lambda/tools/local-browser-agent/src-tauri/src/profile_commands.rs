use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tokio::process::Command;
use std::process::Stdio;
use std::sync::Arc;
use tauri::State;

use crate::config::Config;
use crate::nova_act_executor::NovaActExecutor;

#[derive(Debug, Serialize, Deserialize)]
pub struct Profile {
    pub name: String,
    pub description: String,
    pub tags: Vec<String>,
    pub auto_login_sites: Vec<String>,
    pub user_data_dir: String,
    pub created_at: String,
    pub last_used: Option<String>,
    pub usage_count: u32,
    pub requires_human_login: bool,
    pub login_notes: String,
    pub session_timeout_hours: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProfileListResponse {
    pub profiles: Vec<Profile>,
    pub total_count: usize,
}

/// Find profile_manager.py script
fn find_profile_manager() -> Result<PathBuf> {
    // Try relative to executable (release mode / app bundle)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            // For macOS app bundle
            #[cfg(target_os = "macos")]
            let script_paths = vec![
                exe_dir.join("../Resources/_up_/python/profile_manager.py"),
                exe_dir.join("../Resources/python/profile_manager.py"),
                exe_dir.join("../python/profile_manager.py"),
            ];

            // For Linux
            #[cfg(target_os = "linux")]
            let script_paths = vec![
                exe_dir.join("../python/profile_manager.py"),
            ];

            // For Windows
            #[cfg(target_os = "windows")]
            let script_paths = vec![
                exe_dir.join("..\\python\\profile_manager.py"),
            ];

            for script_path in &script_paths {
                log::info!("Checking for profile_manager.py at: {}", script_path.display());
                if script_path.exists() {
                    log::info!("✓ Found profile_manager.py at: {}", script_path.display());
                    return Ok(script_path.canonicalize()?);
                }
            }
        }
    }

    // Fallback: try current directory (for development)
    let current_dir = std::env::current_dir()
        .context("Failed to get current directory")?;

    let dev_locations = vec![
        current_dir.join("python/profile_manager.py"),
        current_dir.join("../python/profile_manager.py"),
        current_dir.join("../../python/profile_manager.py"),
    ];

    for path in &dev_locations {
        log::info!("Checking dev location for profile_manager.py at: {}", path.display());
        if path.exists() {
            log::info!("✓ Found profile_manager.py at dev location: {}", path.display());
            return Ok(path.canonicalize()?);
        }
    }

    anyhow::bail!("Could not find profile_manager.py in any expected location")
}

/// Find Python executable from venv
fn find_python_executable() -> Result<PathBuf> {
    if let Ok(exe_path) = std::env::current_exe() {
        log::info!("Executable path: {}", exe_path.display());

        if let Some(exe_dir) = exe_path.parent() {
            log::info!("Executable directory: {}", exe_dir.display());

            #[cfg(not(target_os = "windows"))]
            let venv_paths_release = vec![
                exe_dir.join("../Resources/_up_/python/.venv/bin/python"),
                exe_dir.join("../Resources/python/.venv/bin/python"),
                exe_dir.join("../python/.venv/bin/python"),
            ];

            #[cfg(target_os = "windows")]
            let venv_paths_release = vec![
                exe_dir.join("..\\Resources\\_up_\\python\\.venv\\Scripts\\python.exe"),
                exe_dir.join("..\\Resources\\python\\.venv\\Scripts\\python.exe"),
                exe_dir.join("..\\python\\.venv\\Scripts\\python.exe"),
            ];

            log::info!("Searching for Python venv in app bundle...");
            for venv_python in &venv_paths_release {
                log::info!("Checking: {}", venv_python.display());

                if venv_python.exists() {
                    log::info!("✓ Found Python venv at: {}", venv_python.display());
                    // DO NOT canonicalize - we need to use the venv symlink directly
                    // so that Python loads the venv's site-packages
                    return Ok(venv_python.clone());
                }
            }

            log::error!("None of the expected venv paths exist");
        }
    }

    // Fallback: try current directory (for development)
    let current_dir = std::env::current_dir()
        .context("Failed to get current directory")?;

    #[cfg(not(target_os = "windows"))]
    let dev_venv_paths = vec![
        current_dir.join("python/.venv/bin/python"),
        current_dir.join("../python/.venv/bin/python"),
        current_dir.join("../../python/.venv/bin/python"),
    ];

    #[cfg(target_os = "windows")]
    let dev_venv_paths = vec![
        current_dir.join("python\\.venv\\Scripts\\python.exe"),
        current_dir.join("..\\python\\.venv\\Scripts\\python.exe"),
        current_dir.join("..\\..\\python\\.venv\\Scripts\\python.exe"),
    ];

    for venv_python in &dev_venv_paths {
        log::info!("Checking dev venv: {}", venv_python.display());
        if venv_python.exists() {
            log::info!("✓ Found Python venv at dev location: {}", venv_python.display());
            return Ok(venv_python.clone());
        }
    }

    log::error!("Python venv not found in app bundle or dev locations");
    anyhow::bail!(
        "Python virtual environment not found. Please run setup:\n\
         Use the 'Setup Python Environment' button in the Configuration screen"
    )
}

/// Tauri command to list browser profiles
#[tauri::command]
pub async fn list_profiles(tags: Option<Vec<String>>) -> Result<ProfileListResponse, String> {
    let profile_manager = find_profile_manager()
        .map_err(|e| format!("Failed to find profile_manager.py: {}", e))?;

    let python_exe = find_python_executable()
        .map_err(|e| format!("Failed to find Python executable: {}", e))?;

    log::info!("Listing profiles");
    log::debug!("Using Python: {}", python_exe.display());

    let mut cmd = Command::new(&python_exe);
    cmd.arg(&profile_manager);

    cmd.arg("list");

    if let Some(tag_list) = tags {
        if !tag_list.is_empty() {
            cmd.arg("--tags");
            for tag in tag_list {
                cmd.arg(&tag);
            }
        }
    }

    let output = cmd
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await
        .map_err(|e| format!("Failed to execute profile_manager.py: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    if !stderr.is_empty() {
        log::debug!("profile_manager stderr: {}", stderr);
    }

    if output.status.success() {
        // Parse JSON output
        let response: ProfileListResponse = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse profile list: {}", e))?;

        Ok(response)
    } else {
        Err(format!("Failed to list profiles: {}", stderr))
    }
}

/// Tauri command to create a new browser profile
#[tauri::command]
pub async fn create_profile(
    profile_name: String,
    description: String,
    tags: Vec<String>,
    auto_login_sites: Vec<String>,
    session_timeout_hours: u32,
) -> Result<String, String> {
    let profile_manager = find_profile_manager()
        .map_err(|e| format!("Failed to find profile_manager.py: {}", e))?;

    let python_exe = find_python_executable()
        .map_err(|e| format!("Failed to find Python executable: {}", e))?;

    log::info!("Creating profile: {}", profile_name);
    log::debug!("Using Python: {}", python_exe.display());

    let mut cmd = Command::new(&python_exe);
    cmd.arg(&profile_manager);

    cmd.arg("create");
    cmd.arg("--profile").arg(&profile_name);
    cmd.arg("--description").arg(&description);

    if !tags.is_empty() {
        cmd.arg("--tags");
        for tag in tags {
            cmd.arg(&tag);
        }
    }

    if !auto_login_sites.is_empty() {
        cmd.arg("--auto-login-sites");
        for site in auto_login_sites {
            cmd.arg(&site);
        }
    }

    cmd.arg("--timeout").arg(session_timeout_hours.to_string());

    let output = cmd
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await
        .map_err(|e| format!("Failed to execute profile_manager.py: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    if !stderr.is_empty() {
        log::debug!("profile_manager stderr: {}", stderr);
    }

    if output.status.success() {
        Ok(format!("Profile '{}' created successfully", profile_name))
    } else {
        Err(format!("Failed to create profile: {}", stderr))
    }
}

/// Tauri command to delete a browser profile
#[tauri::command]
pub async fn delete_profile(
    profile_name: String,
    keep_data: bool,
) -> Result<String, String> {
    let profile_manager = find_profile_manager()
        .map_err(|e| format!("Failed to find profile_manager.py: {}", e))?;

    let python_exe = find_python_executable()
        .map_err(|e| format!("Failed to find Python executable: {}", e))?;

    log::info!("Deleting profile: {}", profile_name);
    log::debug!("Using Python: {}", python_exe.display());

    let mut cmd = Command::new(&python_exe);
    cmd.arg(&profile_manager);

    cmd.arg("delete");
    cmd.arg("--profile").arg(&profile_name);

    if keep_data {
        cmd.arg("--keep-data");
    }

    let output = cmd
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await
        .map_err(|e| format!("Failed to execute profile_manager.py: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    if !stderr.is_empty() {
        log::debug!("profile_manager stderr: {}", stderr);
    }

    if output.status.success() {
        Ok(format!("Profile '{}' deleted successfully", profile_name))
    } else {
        Err(format!("Failed to delete profile: {}", stderr))
    }
}

/// Tauri command to setup login for a profile
/// This opens a browser window and waits for user to manually log in
#[tauri::command]
pub async fn setup_profile_login(
    profile_name: String,
    starting_url: String,
    config: State<'_, Arc<Config>>,
) -> Result<String, String> {
    log::info!("Setting up login for profile: {}", profile_name);
    log::info!("Starting URL: {}", starting_url);

    // Use NovaActExecutor with the setup_login command type
    // This is the same mechanism that works for validate_profile
    let executor = NovaActExecutor::new(Arc::clone(&config))
        .map_err(|e| format!("Failed to init NovaActExecutor: {}", e))?;

    let payload = serde_json::json!({
        "command_type": "setup_login",
        "profile_name": profile_name,
        "starting_url": starting_url,
        "timeout": 300,  // 5 minutes for user to complete login
    });

    log::info!("Executing setup_login command via NovaActExecutor");

    let result = executor.execute(payload).await
        .map_err(|e| format!("Login setup failed: {}", e))?;

    // Check if successful
    if let Some(success) = result.get("success").and_then(|v| v.as_bool()) {
        if success {
            let message = result.get("message")
                .and_then(|v| v.as_str())
                .unwrap_or("Login setup completed");
            Ok(message.to_string())
        } else {
            let error = result.get("error")
                .and_then(|v| v.as_str())
                .unwrap_or("Unknown error");
            Err(error.to_string())
        }
    } else {
        Err("Invalid response from setup_login command".to_string())
    }
}

/// Tauri command to validate a profile's user_data_dir
/// Supports static and runtime validation via nova_act_wrapper.py
#[tauri::command]
pub async fn validate_profile(
    user_data_dir: String,
    mode: Option<String>,                       // "static" | "runtime" | "both"
    starting_page: Option<String>,
    ui_prompt: Option<String>,
    cookie_domains: Option<Vec<String>>,
    cookie_names: Option<Vec<String>>,
    local_storage_keys: Option<Vec<String>>,
    clone_user_data_dir: Option<bool>,
    config: State<'_, Arc<Config>>,
) -> Result<serde_json::Value, String> {
    let executor = NovaActExecutor::new(Arc::clone(&config))
        .map_err(|e| format!("Failed to init NovaActExecutor: {}", e))?;

    let mut payload = serde_json::json!({
        "command_type": "validate_profile",
        "user_data_dir": user_data_dir,
        "mode": mode.unwrap_or_else(|| "static".to_string()),
    });

    if let Some(sp) = starting_page { payload["starting_page"] = serde_json::json!(sp); }
    if let Some(p) = ui_prompt { payload["ui_prompt"] = serde_json::json!(p); }
    if let Some(v) = cookie_domains { payload["cookie_domains"] = serde_json::json!(v); }
    if let Some(v) = cookie_names { payload["cookie_names"] = serde_json::json!(v); }
    if let Some(v) = local_storage_keys { payload["local_storage_keys"] = serde_json::json!(v); }
    if let Some(v) = clone_user_data_dir { payload["clone_user_data_dir"] = serde_json::json!(v); }

    let result = executor.execute(payload).await
        .map_err(|e| format!("Validation failed: {}", e))?;

    Ok(result)
}
