#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod activity_poller;
mod commands;
mod config;
mod config_commands;
mod nova_act_executor;
mod paths;
mod profile_commands;
mod script_executor;
mod session_manager;
mod test_commands;

use anyhow::{Context, Result};
use log::{info, warn};
use std::path::PathBuf;
use std::sync::Arc;
use parking_lot::RwLock;

use activity_poller::ActivityPoller;
use config::Config;
use nova_act_executor::NovaActExecutor;
use paths::AppPaths;
use session_manager::SessionManager;

/// Initialize logging with both console (stderr) and file output.
///
/// On Windows release builds, the app runs as a GUI subsystem process
/// with no console attached, so file logging is essential for diagnostics.
/// Log files are written to the platform-specific logs directory:
///   - Windows: %LOCALAPPDATA%\Local Browser Agent\logs\
///   - macOS:   ~/Library/Application Support/Local Browser Agent/logs/
///   - Linux:   ~/.local/share/local-browser-agent/logs/
fn init_logging() -> Result<PathBuf> {
    let paths = AppPaths::new()
        .context("Failed to initialize application paths for logging")?;

    let logs_dir = paths.logs_dir();
    std::fs::create_dir_all(&logs_dir)
        .context(format!("Failed to create logs directory: {}", logs_dir.display()))?;

    // Daily log file: local-browser-agent_YYYY-MM-DD.log
    let today = chrono::Local::now().format("%Y-%m-%d").to_string();
    let log_file_path = logs_dir.join(format!("local-browser-agent_{}.log", today));

    let log_file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_file_path)
        .context(format!("Failed to open log file: {}", log_file_path.display()))?;

    // Determine log level from RUST_LOG env var, default to info
    let log_level = std::env::var("RUST_LOG")
        .ok()
        .and_then(|s| s.parse::<log::LevelFilter>().ok())
        .unwrap_or(log::LevelFilter::Info);

    fern::Dispatch::new()
        .format(|out, message, record| {
            out.finish(format_args!(
                "{} [{}] [{}] {}",
                chrono::Local::now().format("%Y-%m-%d %H:%M:%S%.3f"),
                record.level(),
                record.target(),
                message
            ))
        })
        .level(log_level)
        // Reduce noise from internal libraries
        .level_for("hyper", log::LevelFilter::Warn)
        .level_for("rustls", log::LevelFilter::Warn)
        .level_for("tungstenite", log::LevelFilter::Warn)
        .chain(std::io::stderr())
        .chain(log_file)
        .apply()
        .context("Failed to initialize logging")?;

    // Clean up old log files (keep last 7 days)
    cleanup_old_logs(&logs_dir, 7);

    Ok(log_file_path)
}

/// Remove log files older than `keep_days` days
fn cleanup_old_logs(logs_dir: &std::path::Path, keep_days: i64) {
    let cutoff = chrono::Local::now() - chrono::Duration::days(keep_days);

    if let Ok(entries) = std::fs::read_dir(logs_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                // Match files like local-browser-agent_2025-01-20.log
                if name.starts_with("local-browser-agent_") && name.ends_with(".log") {
                    let date_str = name
                        .trim_start_matches("local-browser-agent_")
                        .trim_end_matches(".log");
                    if let Ok(file_date) = chrono::NaiveDate::parse_from_str(date_str, "%Y-%m-%d") {
                        if file_date < cutoff.date_naive() {
                            if let Err(e) = std::fs::remove_file(&path) {
                                eprintln!("Failed to remove old log file {}: {}", path.display(), e);
                            }
                        }
                    }
                }
            }
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging to both console and file
    let log_file_path = match init_logging() {
        Ok(path) => {
            info!("Logging to file: {}", path.display());
            Some(path)
        }
        Err(e) => {
            // Fall back to console-only logging if file logging fails
            env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
                .init();
            warn!("File logging unavailable ({}), using console only", e);
            None
        }
    };

    info!("Starting Local Browser Agent...");
    if let Some(ref path) = log_file_path {
        info!("Log file: {}", path.display());
    }

    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();

    // Try to load config, but use defaults if it doesn't exist yet (for UI configuration)
    let config_result = parse_config_path(&args).and_then(|path| {
        Config::from_file(&path).map(|c| (c, path))
    });

    let (config, poller, session_manager) = if let Ok((mut cfg, path)) = config_result {
        info!("Configuration loaded from: {}", path.display());

        // Validate and auto-fix configuration issues
        cfg.validate_and_fix();

        // Save fixed configuration back to file
        if let Err(e) = cfg.save_to_file(&path) {
            warn!("Failed to save auto-corrected config: {}", e);
        }

        let config = Arc::new(cfg);
        let session_manager = Arc::new(RwLock::new(SessionManager::new()));

        let poller = Arc::new(
            ActivityPoller::new(
                Arc::clone(&config),
                Arc::clone(&session_manager),
            )
            .await?
        );

        // Don't auto-start polling - let user control via UI
        info!("Activity poller initialized - use UI to start listening");

        (config, Some(poller), Some(session_manager))
    } else {
        info!("No configuration file found - using defaults. Use UI to configure.");

        // Create a minimal default config so commands don't crash
        let config = Arc::new(Config::default_minimal());

        (config, None, None)
    };

    // Start Tauri application
    let mut builder = tauri::Builder::default();

    if let Some(p) = poller {
        builder = builder.manage(p);
    }
    if let Some(sm) = session_manager {
        builder = builder.manage(sm);
    }
    // Always manage config (even if it's a default minimal one)
    builder = builder.manage(config);

    builder
        .invoke_handler(tauri::generate_handler![
            commands::get_poller_status,
            commands::get_active_sessions,
            commands::get_session_details,
            commands::end_session,
            commands::cleanup_idle_sessions,
            commands::start_polling,
            commands::stop_polling,
            config_commands::list_aws_profiles,
            config_commands::load_config_from_file,
            config_commands::save_config_to_file,
            config_commands::test_aws_connection,
            config_commands::test_s3_upload,
            config_commands::validate_activity_arn,
            config_commands::list_chrome_profiles,
            config_commands::check_python_environment,
            config_commands::setup_python_environment,
            test_commands::list_browser_examples,
            test_commands::load_browser_example,
            test_commands::validate_browser_script,
            test_commands::execute_browser_script,
            profile_commands::list_profiles,
            profile_commands::create_profile,
            profile_commands::delete_profile,
            profile_commands::update_profile_tags,
            profile_commands::setup_profile_login,
            profile_commands::validate_profile,
        ])
        .setup(|_app| {
            info!("Tauri application started");
            Ok(())
        })
        .run(tauri::generate_context!())
        .context("Error while running tauri application")?;

    Ok(())
}

/// Parse config path from command line arguments
fn parse_config_path(args: &[String]) -> Result<PathBuf> {
    // Look for --config argument
    for i in 0..args.len() {
        if args[i] == "--config" || args[i] == "-c" {
            if i + 1 < args.len() {
                return Ok(PathBuf::from(&args[i + 1]));
            }
        }
    }

    // Default to config.yaml using AppPaths (roaming config on Windows)
    let paths = AppPaths::new()
        .context("Failed to initialize application paths")?;
    let default_path = paths.user_config_file();

    info!("Looking for config at: {}", default_path.display());

    if !default_path.exists() {
        info!("Config file not found at: {}", default_path.display());
        anyhow::bail!("Config file not found at {}. Use UI to configure.", default_path.display());
    }

    Ok(default_path)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_config_path_with_flag() {
        let args = vec![
            "program".to_string(),
            "--config".to_string(),
            "/path/to/config.yaml".to_string(),
        ];

        let path = parse_config_path(&args).unwrap();
        assert_eq!(path, PathBuf::from("/path/to/config.yaml"));
    }

    #[test]
    fn test_parse_config_path_default() {
        let args = vec!["program".to_string()];

        // This will fail if config.yaml doesn't exist in current directory
        // That's expected behavior
        let result = parse_config_path(&args);

        // If config.yaml exists, it should succeed
        // If not, it should fail with appropriate error
        if PathBuf::from("config.yaml").exists() {
            assert!(result.is_ok());
        } else {
            assert!(result.is_err());
        }
    }
}
