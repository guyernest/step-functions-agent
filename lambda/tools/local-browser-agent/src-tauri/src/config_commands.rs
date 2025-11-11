use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use anyhow::Result;
use log::{info, error};

use crate::config::Config;

/// List available AWS profiles by reading both credentials and config files
/// Automatically handles platform-specific paths (Windows: %USERPROFILE%\.aws, Unix: ~/.aws)
#[tauri::command]
pub async fn list_aws_profiles() -> Result<Vec<String>, String> {
    let mut profiles = Vec::new();

    // Detect operating system
    let os = std::env::consts::OS;
    info!("Listing AWS profiles on OS: {}", os);

    // Get home directory using platform-appropriate method
    let home = std::env::var("HOME")
        .or_else(|_| std::env::var("USERPROFILE"))
        .map_err(|e| format!("Failed to get home directory: {}", e))?;

    info!("Home directory: {}", home);

    // Try both credentials and config files
    let credentials_path = PathBuf::from(&home).join(".aws").join("credentials");
    let config_path = PathBuf::from(&home).join(".aws").join("config");

    info!("Looking for AWS credentials at: {}", credentials_path.display());
    info!("Looking for AWS config at: {}", config_path.display());

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

    info!("Found {} AWS profiles: {:?}", profiles.len(), profiles);

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
        browser_channel: config.browser_channel,
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
    info!("Testing AWS connection with profile: {}, region: {:?}", aws_profile, aws_region);

    // Set AWS_PROFILE environment variable for the SDK
    std::env::set_var("AWS_PROFILE", &aws_profile);

    // Try to manually load credentials from the profile to work around Windows parsing issues
    info!("Loading AWS configuration...");

    // Use environment variables if they exist, otherwise fall back to profile
    let aws_config = if std::env::var("AWS_ACCESS_KEY_ID").is_ok() {
        info!("Using credentials from environment variables");
        aws_config::from_env().load().await
    } else {
        info!("Loading credentials from profile: {}", aws_profile);
        let mut config_builder = aws_config::from_env().profile_name(&aws_profile);

        if let Some(ref region) = aws_region {
            info!("Using region: {}", region);
            config_builder = config_builder.region(aws_sdk_sfn::config::Region::new(region.clone()));
        }

        config_builder.load().await
    };

    info!("Creating Step Functions client...");
    let sfn_client = aws_sdk_sfn::Client::new(&aws_config);

    info!("Testing connection by listing activities...");

    // Try to list activities with timeout (this requires minimal permissions)
    let list_result = tokio::time::timeout(
        std::time::Duration::from_secs(30),
        sfn_client.list_activities().max_results(1).send()
    ).await;

    match list_result {
        Ok(Ok(_)) => {
            info!("✓ AWS connection test successful");
            Ok(ConnectionTestResult {
                success: true,
                message: "Successfully connected to AWS Step Functions".to_string(),
                error: None,
            })
        },
        Ok(Err(e)) => {
            let error_msg = format!("{}", e);
            let error_debug = format!("{:?}", e);
            info!("✗ AWS API error: {}", error_msg);
            info!("✗ AWS API error (debug): {}", error_debug);

            // Check for common Windows issues
            let user_message = if error_msg.contains("dispatch failure") {
                "AWS connection failed. This may be due to:\n\
                 1. Network connectivity issues\n\
                 2. Windows firewall blocking the connection\n\
                 3. Proxy settings\n\
                 4. TLS/SSL certificate issues\n\n\
                 Try running: aws sts get-caller-identity --profile CGI-PoC\n\
                 from PowerShell to verify AWS CLI works."
            } else {
                "Failed to connect to AWS"
            };

            Ok(ConnectionTestResult {
                success: false,
                message: user_message.to_string(),
                error: Some(format!("{}\n\nDetailed error: {}", error_msg, error_debug)),
            })
        },
        Err(_) => {
            info!("✗ AWS connection test timed out after 30 seconds");
            Ok(ConnectionTestResult {
                success: false,
                message: "Connection test timed out".to_string(),
                error: Some("Request timed out after 30 seconds. Check your network connection and AWS credentials.".to_string()),
            })
        }
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
    let mut profiles = Vec::new();

    // macOS Chrome profiles
    #[cfg(target_os = "macos")]
    {
        let home = dirs::home_dir().ok_or_else(|| "Failed to get home directory".to_string())?;
        let chrome_dir = home.join("Library/Application Support/Google/Chrome");
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
    pub browser_channel: Option<String>,
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
    let os = std::env::consts::OS;
    info!("Checking Python environment status on OS: {}", os);

    let mut steps = Vec::new();

    // Step 1: Find app path (platform-aware)
    let exe_path = std::env::current_exe()
        .map_err(|e| format!("Failed to get executable path: {}", e))?;

    info!("Current executable: {}", exe_path.display());

    // Determine app root based on platform
    let app_path = if os == "macos" {
        exe_path.parent()
            .and_then(|p| p.parent())
            .and_then(|p| p.parent())
            .ok_or_else(|| "Failed to determine app bundle path on macOS".to_string())?
            .to_path_buf()
    } else if os == "windows" {
        exe_path.parent()
            .ok_or_else(|| "Failed to determine app directory on Windows".to_string())?
            .to_path_buf()
    } else {
        exe_path.parent()
            .ok_or_else(|| "Failed to determine app directory on Linux".to_string())?
            .to_path_buf()
    };

    info!("App root directory: {}", app_path.display());

    steps.push(SetupStep {
        name: "Locate application".to_string(),
        status: "success".to_string(),
        details: format!("Found app at {}", app_path.display()),
    });

    // Step 2: Check Python directory (platform-aware)
    let python_dir = if os == "macos" {
        app_path.join("Contents").join("Resources").join("_up_").join("python")
    } else {
        // Windows/Linux: Try multiple possible locations
        let candidates = vec![
            app_path.join("python"),
            app_path.join("resources").join("python"),
            app_path.join("_up_").join("python"),
        ];

        info!("Searching for Python directory in Windows/Linux...");
        let mut found_path = None;
        for candidate in &candidates {
            info!("  Trying: {}", candidate.display());
            if candidate.exists() {
                info!("  ✓ Found at: {}", candidate.display());
                found_path = Some(candidate.clone());
                break;
            } else {
                info!("  ✗ Not found");
            }
        }

        found_path.unwrap_or_else(|| app_path.join("python"))
    };

    info!("Looking for Python scripts at: {}", python_dir.display());

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
        details: format!("Found Python scripts at {}", python_dir.display()),
    });

    // Step 3: Check venv (platform-aware)
    let venv_python = if os == "windows" {
        python_dir.join(".venv").join("Scripts").join("python.exe")
    } else {
        python_dir.join(".venv").join("bin").join("python")
    };

    info!("Checking for Python at: {}", venv_python.display());

    if !venv_python.exists() {
        steps.push(SetupStep {
            name: "Check Python virtual environment".to_string(),
            status: "failed".to_string(),
            details: format!("Python venv not found at {}. Please run setup.", venv_python.display()),
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
        details: format!("Python venv found at {}", venv_python.display()),
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
    let os = std::env::consts::OS;
    info!("Starting Python environment setup on OS: {}", os);

    let mut steps = Vec::new();

    // Step 1: Find app bundle path (platform-aware)
    let exe_path = std::env::current_exe()
        .map_err(|e| format!("Failed to get executable path: {}", e))?;

    info!("Current executable: {}", exe_path.display());

    // Determine app root based on platform
    let app_path = if os == "macos" {
        // On macOS: exe is at /Applications/Local Browser Agent.app/Contents/MacOS/Local Browser Agent
        // We need: /Applications/Local Browser Agent.app
        exe_path.parent()  // Contents/MacOS
            .and_then(|p| p.parent())  // Contents
            .and_then(|p| p.parent())  // Local Browser Agent.app
            .ok_or_else(|| "Failed to determine app bundle path on macOS".to_string())?
            .to_path_buf()
    } else if os == "windows" {
        // On Windows: exe is at C:\Program Files\Local Browser Agent\Local Browser Agent.exe
        // We need: C:\Program Files\Local Browser Agent
        exe_path.parent()
            .ok_or_else(|| "Failed to determine app directory on Windows".to_string())?
            .to_path_buf()
    } else {
        // Linux: similar to Windows
        exe_path.parent()
            .ok_or_else(|| "Failed to determine app directory on Linux".to_string())?
            .to_path_buf()
    };

    info!("App root directory: {}", app_path.display());

    if !app_path.exists() {
        error!("App path not found: {}", app_path.display());
        return Ok(SetupResult {
            success: false,
            message: format!("Application directory not found: {}", app_path.display()),
            steps,
        });
    }

    steps.push(SetupStep {
        name: "Locate application".to_string(),
        status: "success".to_string(),
        details: format!("Found app at: {}", app_path.display()),
    });

    // Step 2: Find or install uv
    info!("Checking for uv package manager");

    // Get HOME directory for uv path (platform-aware)
    let home = std::env::var("HOME")
        .or_else(|_| std::env::var("USERPROFILE"))
        .map_err(|_| "Failed to get home directory (HOME or USERPROFILE)".to_string())?;

    info!("Home directory for uv: {}", home);

    // On Windows, uv.exe is in .cargo\bin\uv.exe; on Unix it's .cargo/bin/uv
    let uv_binary = if os == "windows" { "uv.exe" } else { "uv" };
    let uv_path = PathBuf::from(&home).join(".cargo").join("bin").join(uv_binary);

    info!("Looking for uv at: {}", uv_path.display());

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
        // Try to find uv in PATH as fallback (platform-aware)
        info!("Checking if uv is in PATH...");
        let which_cmd = if os == "windows" { "where" } else { "which" };
        let which_arg = if os == "windows" { "uv.exe" } else { "uv" };

        let uv_in_path = Command::new(which_cmd)
            .arg(which_arg)
            .output()
            .ok()
            .and_then(|output| {
                if output.status.success() {
                    let path_str = String::from_utf8(output.stdout).ok()?;
                    // On Windows, 'where' might return multiple paths, take the first
                    let path = PathBuf::from(path_str.lines().next()?.trim());

                    // Verify this one works too
                    let test = Command::new(&path).arg("--version").output().ok()?;
                    if test.status.success() {
                        info!("Found working uv in PATH: {}", path.display());
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
            // uv not found or doesn't work, install it (platform-aware)
            info!("uv not found or not working, installing for OS: {}", os);

            let install_result = if os == "windows" {
                // Windows: Use PowerShell
                Command::new("powershell")
                    .arg("-ExecutionPolicy")
                    .arg("ByPass")
                    .arg("-Command")
                    .arg("irm https://astral.sh/uv/install.ps1 | iex")
                    .status()
            } else {
                // Unix: Use sh with curl
                Command::new("sh")
                    .arg("-c")
                    .arg("curl -LsSf https://astral.sh/uv/install.sh | sh")
                    .status()
            };

            if install_result.is_err() || !install_result.as_ref().unwrap().success() {
                let install_cmd = if os == "windows" {
                    "powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
                } else {
                    "curl -LsSf https://astral.sh/uv/install.sh | sh"
                };

                steps.push(SetupStep {
                    name: "Install uv package manager".to_string(),
                    status: "failed".to_string(),
                    details: format!("Failed to install uv. Please install manually: {}", install_cmd),
                });

                return Ok(SetupResult {
                    success: false,
                    message: "Failed to install uv package manager".to_string(),
                    steps,
                });
            }

            // After successful installation, find where UV actually installed
            // Check known installation locations directly since PATH may not be refreshed
            let actual_uv_path = if cfg!(target_os = "windows") {
                let home_dir = dirs::home_dir().unwrap_or_default();
                let known_locations = vec![
                    home_dir.join(".local\\bin\\uv.exe"),      // New default location
                    home_dir.join(".cargo\\bin\\uv.exe"),      // Old location
                ];

                info!("Searching for UV in known locations after installation...");
                let mut found_path = None;
                for location in &known_locations {
                    info!("  Checking: {}", location.display());
                    if location.exists() {
                        info!("  ✓ Found UV at: {}", location.display());
                        found_path = Some(location.clone());
                        break;
                    }
                }

                // If not found in known locations, try 'where' command as fallback
                found_path.or_else(|| {
                    info!("  UV not in known locations, trying 'where' command...");
                    Command::new("where")
                        .arg("uv.exe")
                        .output()
                        .ok()
                        .and_then(|output| {
                            if output.status.success() {
                                let path_str = String::from_utf8(output.stdout).ok()?;
                                let first_path = path_str.lines().next()?.trim();
                                info!("  ✓ Found UV via 'where': {}", first_path);
                                Some(PathBuf::from(first_path))
                            } else {
                                None
                            }
                        })
                }).unwrap_or_else(|| {
                    info!("  Could not locate UV, using assumed path");
                    uv_path.clone()
                })
            } else {
                // On Unix systems, check known locations first
                let home_dir = dirs::home_dir().unwrap_or_default();
                let known_locations = vec![
                    home_dir.join(".local/bin/uv"),
                    home_dir.join(".cargo/bin/uv"),
                    PathBuf::from("/usr/local/bin/uv"),
                ];

                info!("Searching for UV in known locations after installation...");
                let mut found_path = None;
                for location in &known_locations {
                    info!("  Checking: {}", location.display());
                    if location.exists() {
                        info!("  ✓ Found UV at: {}", location.display());
                        found_path = Some(location.clone());
                        break;
                    }
                }

                // If not found in known locations, try 'which' command as fallback
                found_path.or_else(|| {
                    info!("  UV not in known locations, trying 'which' command...");
                    Command::new("which")
                        .arg("uv")
                        .output()
                        .ok()
                        .and_then(|output| {
                            if output.status.success() {
                                let path_str = String::from_utf8(output.stdout).ok()?;
                                let first_path = path_str.trim();
                                info!("  ✓ Found UV via 'which': {}", first_path);
                                Some(PathBuf::from(first_path))
                            } else {
                                None
                            }
                        })
                }).unwrap_or_else(|| {
                    info!("  Could not locate UV, using assumed path");
                    uv_path.clone()
                })
            };

            steps.push(SetupStep {
                name: "Install uv package manager".to_string(),
                status: "success".to_string(),
                details: format!("uv installed successfully at {}", actual_uv_path.display()),
            });

            info!("Installed uv at: {}", actual_uv_path.display());
            actual_uv_path
        }
    } else {
        uv_command
    };

    // Step 3: Locate Python scripts directory (platform-aware)
    let python_dir = if os == "macos" {
        // macOS: inside .app bundle at Contents/Resources/_up_/python
        app_path.join("Contents").join("Resources").join("_up_").join("python")
    } else {
        // Windows/Linux: Try multiple possible locations
        let candidates = vec![
            app_path.join("python"),
            app_path.join("resources").join("python"),
            app_path.join("_up_").join("python"),
        ];

        info!("Searching for Python directory in Windows/Linux...");
        let mut found_path = None;
        for candidate in &candidates {
            info!("  Trying: {}", candidate.display());
            if candidate.exists() {
                info!("  ✓ Found at: {}", candidate.display());
                found_path = Some(candidate.clone());
                break;
            } else {
                info!("  ✗ Not found");
            }
        }

        found_path.unwrap_or_else(|| app_path.join("python"))
    };

    info!("Looking for Python scripts at: {}", python_dir.display());

    if !python_dir.exists() {
        error!("Python directory not found at {:?}", python_dir);
        steps.push(SetupStep {
            name: "Locate Python scripts".to_string(),
            status: "failed".to_string(),
            details: format!("Python scripts not found at {}. App may not be properly installed.", python_dir.display()),
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
        details: format!("Python scripts found at {}", python_dir.display()),
    });

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

    // Platform-aware venv Python path
    let venv_python = if os == "windows" {
        python_dir.join(".venv").join("Scripts").join("python.exe")
    } else {
        python_dir.join(".venv").join("bin").join("python")
    };

    info!("Using Python at: {}", venv_python.display());

    let requirements_txt = python_dir.join("requirements.txt");

    // Disable UV debug logging to avoid buffer overflow
    let install_result = Command::new(&uv_command)
        .arg("pip")
        .arg("install")
        .arg("--python")
        .arg(&venv_python)
        .arg("-r")
        .arg(&requirements_txt)
        .arg("--quiet")  // Reduce UV verbosity
        .current_dir(&python_dir)
        .env("UV_NO_PROGRESS", "1")  // Disable progress bars
        .env_remove("RUST_LOG")  // Remove any debug logging env vars
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output();

    match install_result {
        Ok(output) if output.status.success() => {
            info!("✓ Python dependencies installed successfully");
            // Success
        }
        Ok(output) => {
            let stderr = String::from_utf8_lossy(&output.stderr);
            let stdout = String::from_utf8_lossy(&output.stdout);

            // Extract last 2000 characters of stderr (avoid UI overflow with debug logs)
            let stderr_trimmed = if stderr.len() > 2000 {
                format!("...(truncated {} chars)...\n{}", stderr.len() - 2000, &stderr[stderr.len() - 2000..])
            } else {
                stderr.to_string()
            };

            info!("✗ UV pip install failed");
            info!("Exit code: {:?}", output.status.code());
            info!("Stderr (last 500 chars): {}", &stderr[stderr.len().saturating_sub(500)..]);
            if !stdout.is_empty() {
                info!("Stdout: {}", stdout);
            }

            steps.push(SetupStep {
                name: "Install Python dependencies".to_string(),
                status: "failed".to_string(),
                details: format!("Failed to install Python packages.\nExit code: {:?}\n\nError output (end):\n{}",
                    output.status.code(),
                    stderr_trimmed),
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

    // Step 5: Install Playwright Chromium (not Chrome - Chromium doesn't need admin on Windows)
    info!("Installing Playwright Chromium browser");

    let playwright_result = Command::new(&venv_python)
        .arg("-m")
        .arg("playwright")
        .arg("install")
        .arg("chromium")  // Use chromium instead of chrome (no admin needed)
        .arg("--with-deps")  // Install system dependencies
        .current_dir(&python_dir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output();

    match playwright_result {
        Ok(output) if output.status.success() => {
            info!("✓ Playwright Chromium installed successfully");
            steps.push(SetupStep {
                name: "Install Chromium browser".to_string(),
                status: "success".to_string(),
                details: "Playwright Chromium installed successfully".to_string(),
            });
        }
        Ok(output) => {
            let stderr = String::from_utf8_lossy(&output.stderr);
            let stdout = String::from_utf8_lossy(&output.stdout);

            info!("✗ Playwright install failed");
            info!("Exit code: {:?}", output.status.code());
            info!("Stderr: {}", stderr);
            if !stdout.is_empty() {
                info!("Stdout: {}", stdout);
            }

            // Extract last 1000 chars of combined output
            let combined_output = format!("STDOUT:\n{}\n\nSTDERR:\n{}", stdout, stderr);
            let error_details = if combined_output.len() > 1000 {
                format!("...(truncated)...\n{}", &combined_output[combined_output.len() - 1000..])
            } else {
                combined_output
            };

            steps.push(SetupStep {
                name: "Install Chromium browser".to_string(),
                status: "failed".to_string(),
                details: format!("Failed to install Playwright Chromium.\nExit code: {:?}\n\n{}",
                    output.status.code(),
                    error_details),
            });

            return Ok(SetupResult {
                success: false,
                message: "Failed to install Chromium browser".to_string(),
                steps,
            });
        }
        Err(e) => {
            info!("✗ Failed to execute playwright install: {}", e);
            steps.push(SetupStep {
                name: "Install Chromium browser".to_string(),
                status: "failed".to_string(),
                details: format!("Failed to execute playwright command: {}", e),
            });

            return Ok(SetupResult {
                success: false,
                message: "Failed to install Chromium browser".to_string(),
                steps,
            });
        }
    }

    info!("Python environment setup completed successfully");

    Ok(SetupResult {
        success: true,
        message: "Python environment setup completed successfully! You can now run browser automation scripts.".to_string(),
        steps,
    })
}
