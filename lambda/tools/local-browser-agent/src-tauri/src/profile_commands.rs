use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::fs;
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
    let current_dir = std::env::current_dir()
        .context("Failed to get current directory")?;

    let locations = vec![
        current_dir.join("python/profile_manager.py"),
        current_dir.join("../python/profile_manager.py"),
        current_dir.join("../../python/profile_manager.py"),
    ];

    for path in &locations {
        if path.exists() {
            return Ok(path.canonicalize()?);
        }
    }

    // Try relative to executable (release mode)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let script_path = exe_dir.join("../python/profile_manager.py");
            if script_path.exists() {
                return Ok(script_path.canonicalize()?);
            }
        }
    }

    anyhow::bail!("Could not find profile_manager.py")
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

/// Tauri command to list browser profiles
#[tauri::command]
pub async fn list_profiles(tags: Option<Vec<String>>) -> Result<ProfileListResponse, String> {
    let profile_manager = find_profile_manager()
        .map_err(|e| format!("Failed to find profile_manager.py: {}", e))?;

    let use_uvx = is_uvx_available();

    log::info!("Listing profiles");
    log::debug!("Using uvx: {}", use_uvx);

    let mut cmd = if use_uvx {
        let mut c = Command::new("uvx");
        c.arg("--from").arg("nova-act").arg("python").arg(&profile_manager);
        c
    } else {
        let mut c = Command::new("python3");
        c.arg(&profile_manager);
        c
    };

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

    let use_uvx = is_uvx_available();

    log::info!("Creating profile: {}", profile_name);
    log::debug!("Using uvx: {}", use_uvx);

    let mut cmd = if use_uvx {
        let mut c = Command::new("uvx");
        c.arg("--from").arg("nova-act").arg("python").arg(&profile_manager);
        c
    } else {
        let mut c = Command::new("python3");
        c.arg(&profile_manager);
        c
    };

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

    let use_uvx = is_uvx_available();

    log::info!("Deleting profile: {}", profile_name);
    log::debug!("Using uvx: {}", use_uvx);

    let mut cmd = if use_uvx {
        let mut c = Command::new("uvx");
        c.arg("--from").arg("nova-act").arg("python").arg(&profile_manager);
        c
    } else {
        let mut c = Command::new("python3");
        c.arg(&profile_manager);
        c
    };

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
) -> Result<String, String> {
    let profile_manager = find_profile_manager()
        .map_err(|e| format!("Failed to find profile_manager.py: {}", e))?;

    let use_uvx = is_uvx_available();

    log::info!("Setting up login for profile: {}", profile_name);
    log::debug!("Using uvx: {}", use_uvx);
    log::debug!("Starting URL: {}", starting_url);

    let mut cmd = if use_uvx {
        let mut c = Command::new("uvx");
        c.arg("--from").arg("nova-act").arg("python").arg(&profile_manager);
        c
    } else {
        let mut c = Command::new("python3");
        c.arg(&profile_manager);
        c
    };

    cmd.arg("login");
    cmd.arg("--profile").arg(&profile_name);
    cmd.arg("--url").arg(&starting_url);

    // This command needs to be run in a way that allows the user to see the browser window
    // and interact with it. We'll inherit the parent's stdio so the user can interact.
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
        Ok(format!("Login setup completed for profile '{}'", profile_name))
    } else {
        Err(format!("Failed to setup login: {}", stderr))
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
