use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Browser session information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrowserSession {
    /// Session ID
    pub session_id: String,

    /// Session start time
    pub start_time: DateTime<Utc>,

    /// Last activity time
    pub last_activity: DateTime<Utc>,

    /// User data directory (Chrome profile)
    pub user_data_dir: Option<String>,

    /// Number of commands executed in this session
    pub command_count: u32,

    /// Current page URL (if known)
    pub current_url: Option<String>,

    /// S3 URIs for session recordings
    pub recording_uris: Vec<String>,
}

impl BrowserSession {
    /// Create a new browser session
    pub fn new(user_data_dir: Option<String>) -> Self {
        let session_id = Uuid::new_v4().to_string();
        let now = Utc::now();

        Self {
            session_id,
            start_time: now,
            last_activity: now,
            user_data_dir,
            command_count: 0,
            current_url: None,
            recording_uris: Vec::new(),
        }
    }

    /// Update session with command result
    pub fn update(&mut self, current_url: Option<String>, recording_uri: Option<String>) {
        self.last_activity = Utc::now();
        self.command_count += 1;

        if let Some(url) = current_url {
            self.current_url = Some(url);
        }

        if let Some(uri) = recording_uri {
            self.recording_uris.push(uri);
        }
    }

    /// Get session age in seconds
    pub fn age_seconds(&self) -> i64 {
        (Utc::now() - self.start_time).num_seconds()
    }

    /// Get idle time in seconds
    pub fn idle_seconds(&self) -> i64 {
        (Utc::now() - self.last_activity).num_seconds()
    }
}

/// Session manager that tracks active browser sessions
pub struct SessionManager {
    sessions: HashMap<String, BrowserSession>,
    max_idle_seconds: i64,
}

impl SessionManager {
    /// Create a new session manager
    pub fn new() -> Self {
        Self {
            sessions: HashMap::new(),
            max_idle_seconds: 3600, // 1 hour default
        }
    }

    /// Create a new session
    pub fn create_session(&mut self, user_data_dir: Option<String>) -> BrowserSession {
        let session = BrowserSession::new(user_data_dir);
        let session_id = session.session_id.clone();

        self.sessions.insert(session_id, session.clone());

        session
    }

    /// Get a session by ID
    pub fn get_session(&self, session_id: &str) -> Option<&BrowserSession> {
        self.sessions.get(session_id)
    }

    /// Get a mutable session by ID
    pub fn get_session_mut(&mut self, session_id: &str) -> Option<&mut BrowserSession> {
        self.sessions.get_mut(session_id)
    }

    /// Update session
    pub fn update_session(
        &mut self,
        session_id: &str,
        current_url: Option<String>,
        recording_uri: Option<String>,
    ) {
        if let Some(session) = self.sessions.get_mut(session_id) {
            session.update(current_url, recording_uri);
        }
    }

    /// End a session
    pub fn end_session(&mut self, session_id: &str) -> Option<BrowserSession> {
        self.sessions.remove(session_id)
    }

    /// Get all active sessions
    pub fn get_active_sessions(&self) -> Vec<&BrowserSession> {
        self.sessions.values().collect()
    }

    /// Clean up idle sessions
    pub fn cleanup_idle_sessions(&mut self) -> Vec<String> {
        let mut removed_sessions = Vec::new();

        self.sessions.retain(|session_id, session| {
            if session.idle_seconds() > self.max_idle_seconds {
                removed_sessions.push(session_id.clone());
                false
            } else {
                true
            }
        });

        removed_sessions
    }

    /// Get session count
    pub fn session_count(&self) -> usize {
        self.sessions.len()
    }

    /// Set max idle time
    pub fn set_max_idle_seconds(&mut self, seconds: i64) {
        self.max_idle_seconds = seconds;
    }
}

impl Default for SessionManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;
    use std::time::Duration;

    #[test]
    fn test_create_session() {
        let mut manager = SessionManager::new();
        let session = manager.create_session(Some("/tmp/chrome-profile".to_string()));

        assert!(!session.session_id.is_empty());
        assert_eq!(session.command_count, 0);
        assert_eq!(session.user_data_dir, Some("/tmp/chrome-profile".to_string()));
    }

    #[test]
    fn test_update_session() {
        let mut manager = SessionManager::new();
        let session = manager.create_session(None);
        let session_id = session.session_id.clone();

        manager.update_session(
            &session_id,
            Some("https://example.com".to_string()),
            Some("s3://bucket/recording.mp4".to_string()),
        );

        let updated_session = manager.get_session(&session_id).unwrap();
        assert_eq!(updated_session.command_count, 1);
        assert_eq!(updated_session.current_url, Some("https://example.com".to_string()));
        assert_eq!(updated_session.recording_uris.len(), 1);
    }

    #[test]
    fn test_end_session() {
        let mut manager = SessionManager::new();
        let session = manager.create_session(None);
        let session_id = session.session_id.clone();

        assert_eq!(manager.session_count(), 1);

        let removed = manager.end_session(&session_id);
        assert!(removed.is_some());
        assert_eq!(manager.session_count(), 0);
    }

    #[test]
    fn test_cleanup_idle_sessions() {
        let mut manager = SessionManager::new();
        manager.set_max_idle_seconds(1); // 1 second for testing

        let session = manager.create_session(None);
        let session_id = session.session_id.clone();

        // Wait for session to become idle
        thread::sleep(Duration::from_secs(2));

        let removed = manager.cleanup_idle_sessions();
        assert_eq!(removed.len(), 1);
        assert_eq!(removed[0], session_id);
        assert_eq!(manager.session_count(), 0);
    }
}
