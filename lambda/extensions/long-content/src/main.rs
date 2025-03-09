//! Lambda Extension application to proxy Lambda Runtime API requests between
//! the Application Runtime and the Lambda host.
//!
//! This extension uses Hyper, Tokio, and Rust futures
//!
//!

#[allow(unused_imports)]
use std::{
    convert::Infallible,
    io::{Read, Write},
    net::SocketAddr,
    process::Stdio,
    sync::Arc,
};

#[allow(unused_imports)]
use hyper::{Body, Request, Response, Server};

use tokio::{self};

// Using modules from the lib crate
use aws_lambda_runtime_api_proxy_rs::{
    env, route, sandbox, stats, DEFAULT_PROXY_PORT
};

// This environment variable will be used by the extension to override the Lambda runtime API
pub const WRAPPER_ENV_VAR: &str = "AWS_LAMBDA_RUNTIME_API";
pub const WRAPPER_ENDPOINT: &str = "127.0.0.1:9009";

/// Implement the Runtime API Proxy for Lambda:
///
/// 1. create a hyper server on the LRAP endpoint
///
/// 2. create a Tower service for the Lambda Runtime API to serve HTTP requests
///
/// 3. register as an Extension, allowing Application runtime to begin initializing
///
/// 4. request `next` event from Extension API, fulfilling lifecycle contract
///   
///
#[tokio::main]
async fn main() {
    // Very simple early logging to verify extension is starting
    eprintln!("LAMBDA RUNTIME API PROXY EXTENSION STARTING");
    
    stats::init_start();

    println!(
        "[LRAP] start; path={}",
        std::env::current_exe().unwrap().to_str().unwrap()
    );
    println!(
        "[LRAP] commandline arguments: {}",
        std::env::args()
            .map(|v| format!("\"{}\"", v))
            .collect::<Vec<String>>()
            .join(", ")
    );

    env::latch_runtime_env();

    let addr: SocketAddr = env::lrap_api()
        .parse()
        .expect("Invalid IP specification from Lambda Runtime API endpoint");
    println!("[LRAP] listening on {}", addr);

    // Add an important debug message
    println!("[LRAP] *** IMPORTANT: Lambda functions should connect to {} to use our proxy! ***", addr);
    println!("[LRAP] * Check if AWS_LAMBDA_RUNTIME_API environment variable is correctly set *");

    // bind the server to the Lambda Runtime API Router service
    let server = Server::bind(&addr).serve(route::make_route().into_service());

    // launch the Proxy server task
    let server_join_handle = tokio::spawn(server);

    // The key issue is ensuring proper environment variable setup and connectivity
    // Get the original Lambda Runtime API value
    let original_api = std::env::var(WRAPPER_ENV_VAR).unwrap_or_else(|_| "127.0.0.1:9001".to_string());
    println!("[LRAP] Detected original Lambda Runtime API: {}", original_api);
    
    // Store the original API for our proxy to use
    env::set_original_runtime_api(&original_api);
    
    // Set the environment variable for the Lambda process to use our proxy
    println!("[LRAP] SETTING AWS_LAMBDA_RUNTIME_API=127.0.0.1:9009 - THIS IS CRITICAL");
    std::env::set_var(WRAPPER_ENV_VAR, format!("127.0.0.1:{}", DEFAULT_PROXY_PORT));
    
    // Verify what it's set to now
    let current_api = std::env::var(WRAPPER_ENV_VAR).unwrap_or_else(|_| "NOT SET".to_string());
    println!("[LRAP] Current AWS_LAMBDA_RUNTIME_API setting: {}", current_api);
    println!("[LRAP] We will proxy requests from {} to {}", 
             current_api, original_api);
    
    // No connectivity test - Lambda environment doesn't have curl
    // Just log the configuration and proceed
    println!("[LRAP] Will connect to original Lambda Runtime API at: {}", original_api);
             
    // Print an important message
    println!("[LRAP] ***** PROXY CONFIGURATION SUMMARY *****");
    println!("[LRAP] * Lambda should connect to: 127.0.0.1:{}", DEFAULT_PROXY_PORT);
    println!("[LRAP] * Proxy will forward to: {}", original_api);
    println!("[LRAP] * Extension will connect to: {}", env::sandbox_runtime_api());
    println!("[LRAP] **************************************");
    
    // Initialize the extension and continually get next extension event.
    // We ignore extension events because all LRAP capability is in the Proxy.
    tokio::task::spawn(async {
        println!("[LRAP] Registering extension with Lambda Extensions API...");
        sandbox::extension::register().await;
        println!("[LRAP] Extension registered successfully. Lambda Application runtime should start now.");
        
        // Lambda Application runtime will start once our extension is registered
        stats::app_start();
        
        // At this point, the Lambda runtime should connect to our proxy using the environment variable
        println!("[LRAP] Lambda runtime should connect to proxy at {}", WRAPPER_ENDPOINT);

        println!("[LRAP] Starting extension event loop");
        loop {
            println!("[LRAP] Waiting for next extension event...");
            // Lambda Extension API requires we wait for next extension event
            match sandbox::extension::get_next().await {
                Ok(response) => {
                    // Log the body of the response for debugging
                    if let Ok(body_bytes) = hyper::body::to_bytes(response.into_body()).await {
                        if let Ok(body_str) = std::str::from_utf8(&body_bytes) {
                            println!("[LRAP] Extension event body: {}", body_str);
                            
                            // Try to parse the event as JSON for better debugging
                            if let Ok(json_value) = serde_json::from_str::<serde_json::Value>(body_str) {
                                if let Some(event_type) = json_value.get("eventType").and_then(|v| v.as_str()) {
                                    println!("[LRAP] Received extension event type: {}", event_type);
                                    
                                    // If this is a SHUTDOWN event, log it clearly
                                    if event_type == "SHUTDOWN" {
                                        println!("[LRAP] *** RECEIVED SHUTDOWN EVENT - Lambda environment is shutting down ***");
                                        if let Some(deadline_ms) = json_value.get("deadlineMs").and_then(|v| v.as_u64()) {
                                            println!("[LRAP] Shutdown deadline: {} ms", deadline_ms);
                                        }
                                        if let Some(shutdown_reason) = json_value.get("shutdownReason").and_then(|v| v.as_str()) {
                                            println!("[LRAP] Shutdown reason: {}", shutdown_reason);
                                        }
                                    }
                                }
                            }
                        } else {
                            println!("[LRAP] Extension event body is not valid UTF-8");
                        }
                    } else {
                        println!("[LRAP] Failed to read extension event body");
                    }
                    println!("[LRAP] Processed extension event");
                },
                Err(e) => {
                    eprintln!("[LRAP] Error getting next extension event: {}", e);
                    // Short sleep to avoid tight loop on failure
                    tokio::time::sleep(std::time::Duration::from_millis(100)).await;
                }
            }
        }
    });

    match server_join_handle
        .await
        .expect("Failed to join the server task")
    {
        Err(e) => {
            eprintln!("[LRAP] Hyper server error: {}", e);
        }
        Ok(_) => { /* never reached */ }
    }
}
