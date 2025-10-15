use serde::{Deserialize, Serialize};
use std::sync::Arc;
use parking_lot::RwLock;
use tauri::State;
use tokio::task::JoinHandle;

use crate::activity_poller::ActivityPoller;
use crate::session_manager::SessionManager;

// Global handle for the polling task and state
lazy_static::lazy_static! {
    static ref POLLING_HANDLE: parking_lot::Mutex<Option<JoinHandle<()>>> = parking_lot::Mutex::new(None);
    static ref IS_POLLING: parking_lot::RwLock<bool> = parking_lot::RwLock::new(false);
}

/// Tauri command to get poller status
#[tauri::command]
pub fn get_poller_status(poller: State<Arc<ActivityPoller>>) -> PollerStatusResponse {
    let status = poller.get_status();
    let current_task = poller.get_current_task();

    // Check if we're actually polling (background task is running)
    let is_polling = *IS_POLLING.read();

    PollerStatusResponse {
        status: format!("{:?}", status),
        current_task,
        is_running: is_polling,
    }
}

/// Tauri command to get active sessions
#[tauri::command]
pub fn get_active_sessions(
    session_manager: State<Arc<RwLock<SessionManager>>>
) -> Vec<BrowserSessionInfo> {
    let manager = session_manager.read();
    let sessions = manager.get_active_sessions();

    sessions.into_iter()
        .map(|s| BrowserSessionInfo {
            session_id: s.session_id.clone(),
            start_time: s.start_time.to_rfc3339(),
            last_activity: s.last_activity.to_rfc3339(),
            command_count: s.command_count,
            current_url: s.current_url.clone(),
            recording_count: s.recording_uris.len(),
            age_seconds: s.age_seconds(),
            idle_seconds: s.idle_seconds(),
        })
        .collect()
}

/// Tauri command to get session details
#[tauri::command]
pub fn get_session_details(
    session_id: String,
    session_manager: State<Arc<RwLock<SessionManager>>>
) -> Option<BrowserSessionDetails> {
    let manager = session_manager.read();
    let session = manager.get_session(&session_id)?;

    Some(BrowserSessionDetails {
        session_id: session.session_id.clone(),
        start_time: session.start_time.to_rfc3339(),
        last_activity: session.last_activity.to_rfc3339(),
        user_data_dir: session.user_data_dir.clone(),
        command_count: session.command_count,
        current_url: session.current_url.clone(),
        recording_uris: session.recording_uris.clone(),
        age_seconds: session.age_seconds(),
        idle_seconds: session.idle_seconds(),
    })
}

/// Tauri command to end a session
#[tauri::command]
pub fn end_session(
    session_id: String,
    session_manager: State<Arc<RwLock<SessionManager>>>
) -> Result<String, String> {
    let mut manager = session_manager.write();

    match manager.end_session(&session_id) {
        Some(_) => Ok(format!("Session {} ended", session_id)),
        None => Err(format!("Session {} not found", session_id)),
    }
}

/// Tauri command to cleanup idle sessions
#[tauri::command]
pub fn cleanup_idle_sessions(
    session_manager: State<Arc<RwLock<SessionManager>>>
) -> CleanupResult {
    let mut manager = session_manager.write();
    let removed = manager.cleanup_idle_sessions();

    CleanupResult {
        removed_count: removed.len(),
        removed_session_ids: removed,
    }
}

// Response types

#[derive(Debug, Serialize, Deserialize)]
pub struct PollerStatusResponse {
    pub status: String,
    pub current_task: Option<String>,
    pub is_running: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BrowserSessionInfo {
    pub session_id: String,
    pub start_time: String,
    pub last_activity: String,
    pub command_count: u32,
    pub current_url: Option<String>,
    pub recording_count: usize,
    pub age_seconds: i64,
    pub idle_seconds: i64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BrowserSessionDetails {
    pub session_id: String,
    pub start_time: String,
    pub last_activity: String,
    pub user_data_dir: Option<String>,
    pub command_count: u32,
    pub current_url: Option<String>,
    pub recording_uris: Vec<String>,
    pub age_seconds: i64,
    pub idle_seconds: i64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CleanupResult {
    pub removed_count: usize,
    pub removed_session_ids: Vec<String>,
}

/// Tauri command to start polling for activities
#[tauri::command]
pub async fn start_polling(poller: State<'_, Arc<ActivityPoller>>) -> Result<(), String> {
    // Check if already polling
    let handle_guard = POLLING_HANDLE.lock();
    if handle_guard.is_some() {
        return Err("Already polling".to_string());
    }
    drop(handle_guard);

    // Set polling state to true
    *IS_POLLING.write() = true;

    // Start polling in a background task
    let poller_clone = Arc::clone(&*poller);
    let handle = tokio::spawn(async move {
        if let Err(e) = poller_clone.start_polling().await {
            log::error!("Polling error: {}", e);
            // Reset state on error
            *IS_POLLING.write() = false;
        }
    });

    // Store the handle
    *POLLING_HANDLE.lock() = Some(handle);

    log::info!("Polling started");
    Ok(())
}

/// Tauri command to stop polling for activities
#[tauri::command]
pub async fn stop_polling() -> Result<(), String> {
    // Cancel the polling task if running
    let mut handle_guard = POLLING_HANDLE.lock();
    if let Some(handle) = handle_guard.take() {
        handle.abort();

        // Reset polling state
        *IS_POLLING.write() = false;

        log::info!("Polling stopped");
        Ok(())
    } else {
        Err("Not currently polling".to_string())
    }
}
