use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use anyhow::Result;
use log::{info, error, debug};

use crate::config::Config;

/// List available AWS profiles by reading both credentials and config files
/// Automatically handles platform-specific paths (Windows: %USERPROFILE%\.aws, Unix: ~/.aws)
#[tauri::command]
pub async fn list_aws_profiles() -> Result<Vec<String>, String> {
    let mut profiles = Vec::new();

    // Get home directory using platform-appropriate method
    let home = std::env::var("HOME")
        .or_else(|_| std::env::var("USERPROFILE"))
        .map_err(|e| format!("Failed to get home directory: {}", e))?;

    // Try both credentials and config files
    let credentials_path = PathBuf::from(&home).join(".aws").join("credentials");
    let config_path = PathBuf::from(&home).join(".aws").join("config");

    // Parse credentials file
    if credentials_path.exists() {
        if let Ok(contents) = std::fs::read_to_string(&credentials_path) {
            for line in contents.lines() {
                let line = line.trim();
                if line.starts_with('[') && line.ends_with(']') {
                    let profile = line[1..line.len()-1].to_string();
                    if !profiles.contains(&profile) {
                        profiles.push(profile);
                    }
                }
            }
        }
    }

    // Parse config file (profiles are named [profile xxx] in config)
    if config_path.exists() {
        if let Ok(contents) = std::fs::read_to_string(&config_path) {
            for line in contents.lines() {
                let line = line.trim();
                if line.starts_with("[profile ") && line.ends_with(']') {
                    // Extract profile name from [profile xxx]
                    if let Some(profile) = line.strip_prefix("[profile ").and_then(|s| s.strip_suffix(']')) {
                        let profile = profile.to_string();
                        if !profiles.contains(&profile) {
                            profiles.push(profile);
                        }
                    }
                }
            }
        }
    }

    // Always include "default" if files exist but it's not explicitly listed
    if (credentials_path.exists() || config_path.exists()) && !profiles.is_empty() && !profiles.contains(&"default".to_string()) {
        profiles.insert(0, "default".to_string());
    }

    Ok(profiles)
}

/// Resolve config path to absolute path in user's home directory
fn resolve_config_path(path: &str) -> Result<PathBuf, String> {
    // If path is "config.yaml" (the default), use the new default path
    if path == "config.yaml" {
        let default_path = Config::default_config_path()
            .map_err(|e| format!("Failed to get default config path: {}", e))?;
        info!("Using default config path: {}", default_path.display());
        return Ok(default_path);
    }

    // If path is already absolute, use it as-is
    let path_buf = PathBuf::from(path);
    if path_buf.is_absolute() {
        return Ok(path_buf);
    }

    // Otherwise, resolve relative to config directory
    let config_dir = Config::default_config_dir()
        .map_err(|e| format!("Failed to get config directory: {}", e))?;

    let config_path = config_dir.join(path);

    info!("Resolved config path: {} -> {}", path, config_path.display());

    Ok(config_path)
}

/// Load configuration from file
#[tauri::command]
pub async fn load_config_from_file(path: String) -> Result<ConfigData, String> {
    let config_path = resolve_config_path(&path)?;

    info!("Loading config from: {}", config_path.display());

    let config = Config::from_file(&config_path)
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
    let config_path = resolve_config_path(&path)?;

    info!("Saving config to: {}", config_path.display());

    let yaml = serde_yaml::to_string(&config)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;

    std::fs::write(&config_path, &yaml)
        .map_err(|e| format!("Failed to write config to {}: {}", config_path.display(), e))?;

    info!("Config saved successfully to: {}", config_path.display());

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

#[derive(Debug, Serialize, Deserialize)]
pub struct SetupResult {
    pub success: bool,
    pub message: String,
    pub steps: Vec<SetupStep>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SetupStep {
    pub name: String,
    pub status: String,  // "success", "failed", "skipped"
    pub details: String,
}

/// Check if Python environment is properly set up
#[tauri::command]
pub async fn check_python_environment() -> Result<SetupResult, String> {
    info!("Checking Python environment status");

    let mut steps = Vec::new();

    // Step 1: Check app bundle
    let app_path = PathBuf::from("/Applications/Local Browser Agent.app");

    if !app_path.exists() {
        return Ok(SetupResult {
            success: false,
            message: "Application not found in /Applications folder".to_string(),
            steps: vec![SetupStep {
                name: "Locate application".to_string(),
                status: "failed".to_string(),
                details: "App not found at /Applications/Local Browser Agent.app".to_string(),
            }],
        });
    }

    steps.push(SetupStep {
        name: "Locate application".to_string(),
        status: "success".to_string(),
        details: "Found app at /Applications/Local Browser Agent.app".to_string(),
    });

    // Step 2: Check Python directory
    let python_dir = app_path.join("Contents/Resources/_up_/python");

    if !python_dir.exists() {
        steps.push(SetupStep {
            name: "Locate Python scripts".to_string(),
            status: "failed".to_string(),
            details: format!("Python directory not found at {:?}", python_dir),
        });

        return Ok(SetupResult {
            success: false,
            message: "Python scripts not found in app bundle".to_string(),
            steps,
        });
    }

    steps.push(SetupStep {
        name: "Locate Python scripts".to_string(),
        status: "success".to_string(),
        details: format!("Found Python scripts at {:?}", python_dir),
    });

    // Step 3: Check venv
    let venv_python = python_dir.join(".venv/bin/python");

    if !venv_python.exists() {
        steps.push(SetupStep {
            name: "Check Python virtual environment".to_string(),
            status: "failed".to_string(),
            details: format!("Python venv not found at {:?}. Please run setup.", venv_python),
        });

        return Ok(SetupResult {
            success: false,
            message: "Python virtual environment not set up. Click 'Setup Python Environment' button.".to_string(),
            steps,
        });
    }

    steps.push(SetupStep {
        name: "Check Python virtual environment".to_string(),
        status: "success".to_string(),
        details: format!("Python venv found at {:?}", venv_python),
    });

    // Step 4: Check if Python executable works
    let python_check = Command::new(&venv_python)
        .arg("--version")
        .output();

    match python_check {
        Ok(output) if output.status.success() => {
            let version = String::from_utf8_lossy(&output.stdout).trim().to_string();
            steps.push(SetupStep {
                name: "Test Python executable".to_string(),
                status: "success".to_string(),
                details: format!("Python is working: {}", version),
            });
        }
        Ok(output) => {
            let stderr = String::from_utf8_lossy(&output.stderr);
            steps.push(SetupStep {
                name: "Test Python executable".to_string(),
                status: "failed".to_string(),
                details: format!("Python executable failed: {}", stderr),
            });

            return Ok(SetupResult {
                success: false,
                message: "Python executable is not working properly".to_string(),
                steps,
            });
        }
        Err(e) => {
            steps.push(SetupStep {
                name: "Test Python executable".to_string(),
                status: "failed".to_string(),
                details: format!("Could not run Python: {}", e),
            });

            return Ok(SetupResult {
                success: false,
                message: "Python executable is not working properly".to_string(),
                steps,
            });
        }
    }

    // Step 5: Check for required packages
    let packages_check = Command::new(&venv_python)
        .arg("-c")
        .arg("import nova_act; import boto3; import playwright")
        .output();

    match packages_check {
        Ok(output) if output.status.success() => {
            steps.push(SetupStep {
                name: "Check Python dependencies".to_string(),
                status: "success".to_string(),
                details: "All required packages installed (nova-act, boto3, playwright)".to_string(),
            });
        }
        Ok(output) => {
            let stderr = String::from_utf8_lossy(&output.stderr);
            steps.push(SetupStep {
                name: "Check Python dependencies".to_string(),
                status: "failed".to_string(),
                details: format!("Missing packages: {}", stderr),
            });

            return Ok(SetupResult {
                success: false,
                message: "Python dependencies are missing. Please run setup again.".to_string(),
                steps,
            });
        }
        Err(e) => {
            steps.push(SetupStep {
                name: "Check Python dependencies".to_string(),
                status: "failed".to_string(),
                details: format!("Could not check packages: {}", e),
            });

            return Ok(SetupResult {
                success: false,
                message: "Could not verify Python dependencies".to_string(),
                steps,
            });
        }
    }

    info!("Python environment check completed successfully");

    Ok(SetupResult {
        success: true,
        message: "Python environment is properly set up and ready to use!".to_string(),
        steps,
    })
}

/// Setup Python environment inside the app bundle
#[tauri::command]
pub async fn setup_python_environment() -> Result<SetupResult, String> {
    info!("Starting Python environment setup");

    let mut steps = Vec::new();

    // Step 1: Find app bundle path
    let app_path = PathBuf::from("/Applications/Local Browser Agent.app");

    if !app_path.exists() {
        error!("App not found at /Applications/Local Browser Agent.app");
        return Ok(SetupResult {
            success: false,
            message: "Application not found in /Applications folder. Please install the DMG first.".to_string(),
            steps,
        });
    }

    steps.push(SetupStep {
        name: "Locate application".to_string(),
        status: "success".to_string(),
        details: "Found app at /Applications/Local Browser Agent.app".to_string(),
    });

    // Step 2: Find or install uv
    info!("Checking for uv package manager");

    // Get HOME directory for uv path
    let home = std::env::var("HOME")
        .map_err(|_| "Failed to get HOME directory".to_string())?;

    let uv_path = PathBuf::from(&home).join(".cargo/bin/uv");

    // Check if uv exists at standard location AND is executable
    let uv_command = if uv_path.exists() {
        // Verify uv actually works by running --version
        let test_result = Command::new(&uv_path)
            .arg("--version")
            .output();

        if test_result.is_ok() && test_result.as_ref().unwrap().status.success() {
            steps.push(SetupStep {
                name: "Check uv package manager".to_string(),
                status: "success".to_string(),
                details: format!("uv found and verified at {}", uv_path.display()),
            });

            info!("Found and verified uv at: {}", uv_path.display());
            uv_path.clone()
        } else {
            // uv exists but doesn't work, try PATH or install
            info!("uv found at {} but not executable, will search PATH or install", uv_path.display());
            PathBuf::new() // Empty path to trigger fallback
        }
    } else {
        // uv doesn't exist at standard location, will try PATH or install
        info!("uv not found at standard location, will search PATH or install");
        PathBuf::new() // Empty path to trigger fallback
    };

    // If uv_command is empty (from failed verification), try PATH or install
    let uv_command = if uv_command.as_os_str().is_empty() {
        // Try to find uv in PATH as fallback
        let uv_in_path = Command::new("which")
            .arg("uv")
            .output()
            .ok()
            .and_then(|output| {
                if output.status.success() {
                    let path_str = String::from_utf8(output.stdout).ok()?;
                    let path = PathBuf::from(path_str.trim());

                    // Verify this one works too
                    let test = Command::new(&path).arg("--version").output().ok()?;
                    if test.status.success() {
                        Some(path)
                    } else {
                        None
                    }
                } else {
                    None
                }
            });

        if let Some(path) = uv_in_path {
            steps.push(SetupStep {
                name: "Check uv package manager".to_string(),
                status: "success".to_string(),
                details: format!("uv found and verified in PATH at {}", path.display()),
            });

            info!("Found and verified uv in PATH at: {}", path.display());
            path
        } else {
            // uv not found or doesn't work, install it
            info!("uv not found or not working, installing...");

            let install_result = Command::new("sh")
                .arg("-c")
                .arg("curl -LsSf https://astral.sh/uv/install.sh | sh")
                .status();

            if install_result.is_err() || !install_result.as_ref().unwrap().success() {
                steps.push(SetupStep {
                    name: "Install uv package manager".to_string(),
                    status: "failed".to_string(),
                    details: "Failed to install uv. Please install manually: curl -LsSf https://astral.sh/uv/install.sh | sh".to_string(),
                });

                return Ok(SetupResult {
                    success: false,
                    message: "Failed to install uv package manager".to_string(),
                    steps,
                });
            }

            steps.push(SetupStep {
                name: "Install uv package manager".to_string(),
                status: "success".to_string(),
                details: format!("uv installed successfully at {}", uv_path.display()),
            });

            info!("Installed uv at: {}", uv_path.display());
            uv_path
        }
    } else {
        uv_command
    };

    // Step 3: Create Python venv
    let python_dir = app_path.join("Contents/Resources/_up_/python");

    if !python_dir.exists() {
        error!("Python directory not found at {:?}", python_dir);
        steps.push(SetupStep {
            name: "Locate Python scripts".to_string(),
            status: "failed".to_string(),
            details: format!("Python scripts not found at {:?}. App may not be properly installed.", python_dir),
        });

        return Ok(SetupResult {
            success: false,
            message: "Python scripts not found in app bundle".to_string(),
            steps,
        });
    }

    info!("Creating Python venv at {:?}", python_dir);

    let venv_result = Command::new(&uv_command)
        .arg("venv")
        .arg("--python")
        .arg("3.11")
        .arg(".venv")
        .current_dir(&python_dir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output();

    match venv_result {
        Ok(output) if output.status.success() => {
            // Success
        }
        Ok(output) => {
            let stderr = String::from_utf8_lossy(&output.stderr);
            steps.push(SetupStep {
                name: "Create Python virtual environment".to_string(),
                status: "failed".to_string(),
                details: format!("Failed to create Python venv: {}", stderr),
            });

            return Ok(SetupResult {
                success: false,
                message: "Failed to create Python virtual environment".to_string(),
                steps,
            });
        }
        Err(e) => {
            steps.push(SetupStep {
                name: "Create Python virtual environment".to_string(),
                status: "failed".to_string(),
                details: format!("Failed to execute uv command: {}", e),
            });

            return Ok(SetupResult {
                success: false,
                message: "Failed to create Python virtual environment".to_string(),
                steps,
            });
        }
    }

    steps.push(SetupStep {
        name: "Create Python virtual environment".to_string(),
        status: "success".to_string(),
        details: "Python 3.11 venv created".to_string(),
    });

    // Step 4: Install dependencies
    info!("Installing Python dependencies from requirements.txt");

    let venv_python = python_dir.join(".venv/bin/python");
    let requirements_txt = python_dir.join("requirements.txt");

    let install_result = Command::new(&uv_command)
        .arg("pip")
        .arg("install")
        .arg("--python")
        .arg(&venv_python)
        .arg("-r")
        .arg(&requirements_txt)
        .current_dir(&python_dir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output();

    match install_result {
        Ok(output) if output.status.success() => {
            // Success
        }
        Ok(output) => {
            let stderr = String::from_utf8_lossy(&output.stderr);
            steps.push(SetupStep {
                name: "Install Python dependencies".to_string(),
                status: "failed".to_string(),
                details: format!("Failed to install Python packages: {}", stderr),
            });

            return Ok(SetupResult {
                success: false,
                message: "Failed to install Python dependencies".to_string(),
                steps,
            });
        }
        Err(e) => {
            steps.push(SetupStep {
                name: "Install Python dependencies".to_string(),
                status: "failed".to_string(),
                details: format!("Failed to execute uv pip command: {}", e),
            });

            return Ok(SetupResult {
                success: false,
                message: "Failed to install Python dependencies".to_string(),
                steps,
            });
        }
    }

    steps.push(SetupStep {
        name: "Install Python dependencies".to_string(),
        status: "success".to_string(),
        details: "All dependencies installed from requirements.txt".to_string(),
    });

    // Step 5: Install Playwright Chrome
    info!("Installing Playwright Chromium browser");

    let playwright_result = Command::new(&venv_python)
        .arg("-m")
        .arg("playwright")
        .arg("install")
        .arg("chrome")
        .current_dir(&python_dir)
        .status();

    if playwright_result.is_err() || !playwright_result.as_ref().unwrap().success() {
        steps.push(SetupStep {
            name: "Install Chromium browser".to_string(),
            status: "failed".to_string(),
            details: "Failed to install Playwright Chromium browser".to_string(),
        });

        return Ok(SetupResult {
            success: false,
            message: "Failed to install Chromium browser".to_string(),
            steps,
        });
    }

    steps.push(SetupStep {
        name: "Install Chromium browser".to_string(),
        status: "success".to_string(),
        details: "Playwright Chromium installed successfully".to_string(),
    });

    info!("Python environment setup completed successfully");

    Ok(SetupResult {
        success: true,
        message: "Python environment setup completed successfully! You can now run browser automation scripts.".to_string(),
        steps,
    })
}
