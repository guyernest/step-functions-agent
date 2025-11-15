use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use anyhow::{Context, Result};

use crate::paths::AppPaths;

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

    /// Browser automation engine: "nova_act" or "computer_agent"
    #[serde(default = "default_browser_engine")]
    pub browser_engine: String,

    /// Nova Act API key (optional, can use env var)
    pub nova_act_api_key: Option<String>,

    /// OpenAI API key (required when browser_engine = "computer_agent")
    pub openai_api_key: Option<String>,

    /// OpenAI model: "gpt-4o-mini" or "gpt-4o"
    #[serde(default = "default_openai_model")]
    pub openai_model: String,

    /// Enable automatic replanning for OpenAI Computer Agent
    #[serde(default = "default_enable_replanning")]
    pub enable_replanning: bool,

    /// Maximum replanning attempts
    #[serde(default = "default_max_replans")]
    pub max_replans: u32,

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

fn default_browser_engine() -> String {
    // Default to Nova Act for backward compatibility
    "nova_act".to_string()
}

fn default_openai_model() -> String {
    "gpt-4o-mini".to_string()
}

fn default_enable_replanning() -> bool {
    true
}

fn default_max_replans() -> u32 {
    2
}

fn default_browser_channel() -> Option<String> {
    // Platform-specific defaults
    #[cfg(target_os = "windows")]
    return Some("msedge".to_string());

    #[cfg(not(target_os = "windows"))]
    return Some("chrome".to_string());
}

impl Config {
    /// Get the default config directory using AppPaths (recommended)
    ///
    /// Uses the new AppPaths system for proper Windows path separation.
    /// - Windows: `%APPDATA%\Local Browser Agent` (roaming config)
    /// - macOS: `~/Library/Application Support/Local Browser Agent`
    /// - Linux: `~/.config/local-browser-agent`
    pub fn default_config_dir_v2() -> Result<PathBuf> {
        let paths = AppPaths::new()?;
        Ok(paths.user_config_dir)
    }

    /// Get the default config file path using AppPaths (recommended)
    pub fn default_config_path_v2() -> Result<PathBuf> {
        let paths = AppPaths::new()?;
        Ok(paths.user_config_file())
    }

    /// Get the default config directory using OS-specific conventions (legacy)
    ///
    /// Uses:
    /// - Windows: `%LOCALAPPDATA%\Local Browser Agent`
    /// - macOS: `~/Library/Application Support/Local Browser Agent`
    /// - Linux: `~/.config/local-browser-agent`
    ///
    /// Falls back to `~/.local-browser-agent` if dirs crate fails
    ///
    /// Note: This is kept for backward compatibility. Use default_config_dir_v2() instead.
    pub fn default_config_dir() -> Result<PathBuf> {
        // Try to use OS-specific config directory via dirs crate
        let config_dir = if let Some(config_base) = dirs::config_dir() {
            // Linux: ~/.config/local-browser-agent
            // macOS/Windows will use data_local_dir below
            #[cfg(not(any(target_os = "windows", target_os = "macos")))]
            {
                config_base.join("local-browser-agent")
            }

            // macOS and Windows: use data_local_dir for consistency
            #[cfg(any(target_os = "windows", target_os = "macos"))]
            {
                dirs::data_local_dir()
                    .unwrap_or(config_base)
                    .join("Local Browser Agent")
            }
        } else {
            // Fallback to legacy path if dirs crate fails
            let home = std::env::var("HOME")
                .or_else(|_| std::env::var("USERPROFILE"))
                .context("Could not determine home directory (HOME or USERPROFILE not set)")?;
            PathBuf::from(home).join(".local-browser-agent")
        };

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
            browser_engine: default_browser_engine(),
            nova_act_api_key: None,
            openai_api_key: None,
            openai_model: default_openai_model(),
            enable_replanning: default_enable_replanning(),
            max_replans: default_max_replans(),
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

    /// Save configuration to YAML file
    pub fn save_to_file(&self, path: &PathBuf) -> Result<()> {
        let yaml = serde_yaml::to_string(self)
            .context("Failed to serialize config to YAML")?;

        std::fs::write(path, yaml)
            .context(format!("Failed to write config file: {}", path.display()))?;

        log::info!("✓ Configuration saved to: {}", path.display());

        Ok(())
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

    /// Validate and auto-fix configuration issues
    /// This method fixes common configuration problems automatically
    pub fn validate_and_fix(&mut self) {
        // Fix browser channel for platform
        self.fix_browser_channel();

        // Fix S3 bucket name if using old format
        self.fix_s3_bucket_name();

        // Log configuration for debugging
        self.log_configuration();
    }

    /// Fix browser channel to match platform
    fn fix_browser_channel(&mut self) {
        #[cfg(target_os = "windows")]
        {
            match &self.browser_channel {
                None => {
                    log::info!("ℹ Config missing browser_channel, setting to 'msedge' for Windows");
                    self.browser_channel = Some("msedge".to_string());
                }
                Some(channel) if channel == "chrome" || channel == "chromium" => {
                    log::warn!("⚠ Config has '{}' on Windows, auto-correcting to 'msedge'", channel);
                    log::warn!("  Reason: Browser profiles are typically set up for Edge on Windows");
                    self.browser_channel = Some("msedge".to_string());
                }
                _ => {} // Already correct
            }
        }

        #[cfg(not(target_os = "windows"))]
        {
            match &self.browser_channel {
                None => {
                    log::info!("ℹ Config missing browser_channel, setting to 'chrome' for non-Windows");
                    self.browser_channel = Some("chrome".to_string());
                }
                Some(channel) if channel == "msedge" => {
                    log::warn!("⚠ Config has 'msedge' on non-Windows, auto-correcting to 'chrome'");
                    log::warn!("  Reason: Edge is not typically available on macOS/Linux");
                    self.browser_channel = Some("chrome".to_string());
                }
                _ => {} // Already correct
            }
        }
    }

    /// Fix S3 bucket name if using old/incorrect format
    fn fix_s3_bucket_name(&mut self) {
        // Check for old bucket name pattern
        if self.s3_bucket.starts_with("nova-act-browser-results") {
            let old_name = self.s3_bucket.clone();
            // Extract account ID from old name
            if let Some(account_id) = old_name.split('-').last() {
                let new_name = format!("browser-agent-recordings-prod-{}", account_id);
                log::warn!("⚠ S3 bucket name is using old format, auto-correcting");
                log::warn!("  Old: {}", old_name);
                log::warn!("  New: {}", new_name);
                self.s3_bucket = new_name;
            }
        }
    }

    /// Log configuration with absolute paths for debugging
    fn log_configuration(&self) {
        log::info!("═══ Configuration ═══");
        log::info!("Activity ARN: {}", if self.activity_arn.is_empty() { "(not set)" } else { &self.activity_arn });
        log::info!("AWS Profile: {}", self.aws_profile);
        log::info!("AWS Region: {}", self.aws_region.as_deref().unwrap_or("(use profile default)"));
        log::info!("S3 Bucket: {}", if self.s3_bucket.is_empty() { "(not set)" } else { &self.s3_bucket });
        log::info!("Browser Channel: {}", self.browser_channel.as_deref().unwrap_or("(platform default)"));
        log::info!("Headless Mode: {}", self.headless);
        log::info!("Heartbeat Interval: {}s", self.heartbeat_interval);

        if let Some(ref user_data_dir) = self.user_data_dir {
            log::info!("User Data Dir: {}", user_data_dir.display());
        }

        log::info!("═════════════════════");
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
