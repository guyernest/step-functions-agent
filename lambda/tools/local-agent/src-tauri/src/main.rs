// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod rust_automation;

use commands::*;

fn main() {
    env_logger::init();
    
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            load_config,
            save_config,
            list_aws_profiles,
            test_connection,
            get_polling_status,
            get_logs,
            clear_logs,
            start_polling,
            stop_polling,
            list_example_scripts,
            load_example_script,
            validate_script,
            execute_test_script,
            stop_script_execution,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
