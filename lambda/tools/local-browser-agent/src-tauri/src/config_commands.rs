use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use anyhow::Result;

use crate::config::Config;

/// List available AWS profiles from ~/.aws/credentials
#[tauri::command]
pub async fn list_aws_profiles() -> Result<Vec<String>, String> {
    let home = std::env::var("HOME")
        .map_err(|e| format!("Failed to get HOME: {}", e))?;

    let credentials_path = PathBuf::from(home).join(".aws/credentials");

    if !credentials_path.exists() {
        return Ok(vec![]);
    }

    let contents = std::fs::read_to_string(&credentials_path)
        .map_err(|e| format!("Failed to read credentials: {}", e))?;

    let mut profiles = Vec::new();
    for line in contents.lines() {
        let line = line.trim();
        if line.starts_with('[') && line.ends_with(']') {
            let profile = line[1..line.len()-1].to_string();
            profiles.push(profile);
        }
    }

    Ok(profiles)
}

/// Load configuration from file
#[tauri::command]
pub async fn load_config_from_file(path: String) -> Result<ConfigData, String> {
    let config = Config::from_file(&PathBuf::from(path))
        .map_err(|e| format!("Failed to load config: {}", e))?;

    Ok(ConfigData {
        activity_arn: config.activity_arn,
        aws_profile: config.aws_profile,
        aws_region: config.aws_region,
        s3_bucket: config.s3_bucket,
        user_data_dir: config.user_data_dir.map(|p| p.to_string_lossy().to_string()),
        ui_port: config.ui_port,
        nova_act_api_key: config.nova_act_api_key,
        headless: config.headless,
        heartbeat_interval: config.heartbeat_interval,
    })
}

/// Save configuration to file
#[tauri::command]
pub async fn save_config_to_file(path: String, config: ConfigData) -> Result<(), String> {
    let yaml = serde_yaml::to_string(&config)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;

    std::fs::write(&path, yaml)
        .map_err(|e| format!("Failed to write config: {}", e))?;

    Ok(())
}

/// Test AWS connection
#[tauri::command]
pub async fn test_aws_connection(aws_profile: String, aws_region: Option<String>) -> Result<ConnectionTestResult, String> {
    // Create AWS config
    let mut config_builder = aws_config::from_env().profile_name(&aws_profile);

    if let Some(region) = aws_region {
        config_builder = config_builder.region(aws_sdk_sfn::config::Region::new(region));
    }

    let aws_config = config_builder.load().await;
    let sfn_client = aws_sdk_sfn::Client::new(&aws_config);

    // Try to list activities (this requires minimal permissions)
    match sfn_client.list_activities().max_results(1).send().await {
        Ok(_) => Ok(ConnectionTestResult {
            success: true,
            message: "Successfully connected to AWS Step Functions".to_string(),
            error: None,
        }),
        Err(e) => Ok(ConnectionTestResult {
            success: false,
            message: "Failed to connect to AWS".to_string(),
            error: Some(format!("{}", e)),
        }),
    }
}

/// Check if Activity ARN is valid
#[tauri::command]
pub async fn validate_activity_arn(activity_arn: String, aws_profile: String) -> Result<ValidationResult, String> {
    let aws_config = aws_config::from_env()
        .profile_name(&aws_profile)
        .load()
        .await;

    let sfn_client = aws_sdk_sfn::Client::new(&aws_config);

    match sfn_client.describe_activity()
        .activity_arn(&activity_arn)
        .send()
        .await
    {
        Ok(response) => {
            let activity = response.activity_arn();
            let name = response.name().to_string();
            Ok(ValidationResult {
                valid: true,
                message: format!("Activity found: {}", activity),
                details: Some(name),
            })
        }
        Err(e) => Ok(ValidationResult {
            valid: false,
            message: format!("Failed to validate Activity ARN: {}", e),
            details: None,
        }),
    }
}

/// Get Chrome profile paths
#[tauri::command]
pub async fn list_chrome_profiles() -> Result<Vec<ChromeProfile>, String> {
    let home = std::env::var("HOME")
        .map_err(|e| format!("Failed to get HOME: {}", e))?;

    let mut profiles = Vec::new();

    // macOS Chrome profiles
    #[cfg(target_os = "macos")]
    {
        let chrome_dir = PathBuf::from(&home).join("Library/Application Support/Google/Chrome");
        if chrome_dir.exists() {
            if let Ok(entries) = std::fs::read_dir(&chrome_dir) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.is_dir() {
                        let name = path.file_name().unwrap().to_string_lossy().to_string();
                        if name == "Default" || name.starts_with("Profile ") {
                            profiles.push(ChromeProfile {
                                name,
                                path: path.to_string_lossy().to_string(),
                            });
                        }
                    }
                }
            }
        }
    }

    // Linux Chrome profiles
    #[cfg(target_os = "linux")]
    {
        let chrome_dir = PathBuf::from(&home).join(".config/google-chrome");
        if chrome_dir.exists() {
            if let Ok(entries) = std::fs::read_dir(&chrome_dir) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.is_dir() {
                        let name = path.file_name().unwrap().to_string_lossy().to_string();
                        if name == "Default" || name.starts_with("Profile ") {
                            profiles.push(ChromeProfile {
                                name,
                                path: path.to_string_lossy().to_string(),
                            });
                        }
                    }
                }
            }
        }
    }

    Ok(profiles)
}

// Data structures

#[derive(Debug, Serialize, Deserialize)]
pub struct ConfigData {
    pub activity_arn: String,
    pub aws_profile: String,
    pub aws_region: Option<String>,
    pub s3_bucket: String,
    pub user_data_dir: Option<String>,
    pub ui_port: u16,
    pub nova_act_api_key: Option<String>,
    pub headless: bool,
    pub heartbeat_interval: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConnectionTestResult {
    pub success: bool,
    pub message: String,
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ValidationResult {
    pub valid: bool,
    pub message: String,
    pub details: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ChromeProfile {
    pub name: String,
    pub path: String,
}
