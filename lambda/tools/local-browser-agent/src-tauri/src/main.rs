#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod activity_poller;
mod commands;
mod config;
mod config_commands;
mod nova_act_executor;
mod profile_commands;
mod session_manager;
mod test_commands;

use anyhow::{Context, Result};
use log::info;
use std::path::PathBuf;
use std::sync::Arc;
use parking_lot::RwLock;

use activity_poller::ActivityPoller;
use config::Config;
use nova_act_executor::NovaActExecutor;
use session_manager::SessionManager;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .init();

    info!("Starting Local Browser Agent...");

    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();

    // Try to load config, but use defaults if it doesn't exist yet (for UI configuration)
    let config_result = parse_config_path(&args).and_then(|path| {
        Config::from_file(&path).map(|c| (c, path))
    });

    let (config, poller, session_manager) = if let Ok((cfg, path)) = config_result {
        info!("Configuration loaded from: {}", path.display());

        let config = Arc::new(cfg);
        let session_manager = Arc::new(RwLock::new(SessionManager::new()));
        let executor = Arc::new(NovaActExecutor::new(Arc::clone(&config))?);

        let poller = Arc::new(
            ActivityPoller::new(
                Arc::clone(&config),
                Arc::clone(&executor),
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

    // Default to config.yaml in ~/.local-browser-agent directory
    let default_path = Config::default_config_path()
        .context("Failed to get default config path")?;

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
