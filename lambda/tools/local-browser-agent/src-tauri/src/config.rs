use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use anyhow::{Context, Result};

/// Configuration for the local browser agent
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Step Functions Activity ARN to poll
    pub activity_arn: String,

    /// AWS profile name for credentials
    pub aws_profile: String,

    /// S3 bucket for browser session recordings
    pub s3_bucket: String,

    /// Chrome user data directory (optional, for session persistence)
    pub user_data_dir: Option<PathBuf>,

    /// Port for UI server
    #[serde(default = "default_ui_port")]
    pub ui_port: u16,

    /// Nova Act API key (optional, can use env var)
    pub nova_act_api_key: Option<String>,

    /// Run browser in headless mode
    #[serde(default)]
    pub headless: bool,

    /// Heartbeat interval in seconds
    #[serde(default = "default_heartbeat_interval")]
    pub heartbeat_interval: u64,

    /// AWS region (optional, defaults to profile region)
    pub aws_region: Option<String>,

    /// Browser channel: "msedge", "chrome", "chromium", or null for platform default
    #[serde(default = "default_browser_channel")]
    pub browser_channel: Option<String>,
}

fn default_ui_port() -> u16 {
    3000
}

fn default_heartbeat_interval() -> u64 {
    60
}

fn default_browser_channel() -> Option<String> {
    // Platform-specific defaults
    #[cfg(target_os = "windows")]
    return Some("msedge".to_string());

    #[cfg(not(target_os = "windows"))]
    return Some("chrome".to_string());
}

impl Config {
    /// Get the default config directory (~/.local-browser-agent)
    /// Cross-platform: works on macOS, Windows, and Linux
    pub fn default_config_dir() -> Result<PathBuf> {
        let home = std::env::var("HOME")
            .or_else(|_| std::env::var("USERPROFILE"))
            .context("Could not determine home directory (HOME or USERPROFILE not set)")?;

        let config_dir = PathBuf::from(home).join(".local-browser-agent");

        // Create directory if it doesn't exist
        if !config_dir.exists() {
            std::fs::create_dir_all(&config_dir)
                .context(format!("Failed to create config directory: {}", config_dir.display()))?;
        }

        Ok(config_dir)
    }

    /// Get the default config file path (~/.local-browser-agent/config.yaml)
    /// Cross-platform: works on macOS, Windows, and Linux
    pub fn default_config_path() -> Result<PathBuf> {
        let config_dir = Self::default_config_dir()?;
        Ok(config_dir.join("config.yaml"))
    }

    /// Create a default minimal config (for when no config file exists)
    pub fn default_minimal() -> Self {
        Config {
            activity_arn: String::new(),
            aws_profile: "default".to_string(),
            s3_bucket: String::new(),
            user_data_dir: None,
            ui_port: default_ui_port(),
            nova_act_api_key: None,
            headless: false,
            heartbeat_interval: default_heartbeat_interval(),
            aws_region: None,
            browser_channel: default_browser_channel(),
        }
    }

    /// Load configuration from YAML file
    pub fn from_file(path: &PathBuf) -> Result<Self> {
        let contents = std::fs::read_to_string(path)
            .context(format!("Failed to read config file: {}", path.display()))?;

        let config: Config = serde_yaml::from_str(&contents)
            .context("Failed to parse config file")?;

        // Don't validate here - allow incomplete configs for testing/configuration
        // Validation will happen when trying to use specific features

        Ok(config)
    }

    /// Validate configuration for activity polling
    /// This is stricter than basic validation - requires all fields for polling to work
    pub fn validate_for_polling(&self) -> Result<()> {
        if self.activity_arn.is_empty() {
            anyhow::bail!("activity_arn cannot be empty for activity polling");
        }

        if self.aws_profile.is_empty() {
            anyhow::bail!("aws_profile cannot be empty");
        }

        if self.s3_bucket.is_empty() {
            anyhow::bail!("s3_bucket cannot be empty for activity polling");
        }

        if self.heartbeat_interval == 0 {
            anyhow::bail!("heartbeat_interval must be greater than 0");
        }

        Ok(())
    }

    /// Basic validation - just ensures critical fields are valid
    fn validate(&self) -> Result<()> {
        if self.aws_profile.is_empty() {
            anyhow::bail!("aws_profile cannot be empty");
        }

        if self.heartbeat_interval == 0 {
            anyhow::bail!("heartbeat_interval must be greater than 0");
        }

        Ok(())
    }

    /// Get Nova Act API key from config or environment
    pub fn get_nova_act_api_key(&self) -> Result<String> {
        if let Some(ref key) = self.nova_act_api_key {
            return Ok(key.clone());
        }

        std::env::var("NOVA_ACT_API_KEY")
            .context("NOVA_ACT_API_KEY not found in config or environment")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_validation() {
        let config = Config {
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
        };

        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_config_validation_empty_arn() {
        let config = Config {
            activity_arn: "".to_string(),
            aws_profile: "browser-agent".to_string(),
            s3_bucket: "browser-agent-recordings-prod".to_string(),
            user_data_dir: None,
            ui_port: 3000,
            nova_act_api_key: Some("test-key".to_string()),
            headless: false,
            heartbeat_interval: 60,
            aws_region: None,
            browser_channel: Some("chrome".to_string()),
        };

        assert!(config.validate().is_err());
    }
}
