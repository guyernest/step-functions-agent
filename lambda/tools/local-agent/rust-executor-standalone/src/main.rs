use std::env;
use std::fs;
use std::process;

// Include the rust_automation module inline
include!("../../src-tauri/src/rust_automation.rs");

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Rust Executor v0.2.0 - Standalone GUI Automation");
        eprintln!("Usage: {} <script.json>", args[0]);
        eprintln!("\nExample:");
        eprintln!("  {} examples/windows_simple_test.json", args[0]);
        process::exit(1);
    }
    
    let script_path = &args[1];
    
    println!("Loading script: {}", script_path);
    
    let script = match fs::read_to_string(script_path) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Failed to read script file: {}", e);
            process::exit(1);
        }
    };
    
    println!("Executing automation script...");
    
    let mut executor = RustScriptExecutor::new();
    let result = executor.execute_script(&script);
    
    // Print results
    println!("\n=== Execution Results ===");
    for action_result in &result.results {
        let status_symbol = if action_result.status == "success" { "✓" } else { "✗" };
        println!("{} {} - {} ({}ms)", 
            status_symbol,
            action_result.action,
            action_result.details,
            action_result.duration_ms.unwrap_or(0)
        );
    }
    
    if result.success {
        println!("\n✅ Script executed successfully!");
        process::exit(0);
    } else {
        eprintln!("\n❌ Script execution failed!");
        if let Some(error) = result.error {
            eprintln!("Error: {}", error);
        }
        process::exit(1);
    }
}