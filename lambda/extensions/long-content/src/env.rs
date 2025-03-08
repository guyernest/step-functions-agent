//
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
//

//! Access the ENV for the Extension (and Proxy)
//!
//! Utilities and other helper functions for thread-safe access and lazy initializers
//!

use once_cell::sync::OnceCell;

/// Sandbox's Runtime API endpoint
static LAMBDA_RUNTIME_API: OnceCell<String> = OnceCell::new();

/// Lambda Runtime API Proxy (LRAP), this endpoint
static LRAP_API: OnceCell<String> = OnceCell::new();

/// Original Runtime API endpoint for proxying
static ORIGINAL_RUNTIME_API: OnceCell<String> = OnceCell::new();

/// Latch in the API endpoints defined in ENV variables
///
#[allow(dead_code)]
pub fn latch_runtime_env() {
    use std::env::var;

    println!("[LRAP] Initializing environment variables...");
    
    // Print current env vars for debugging
    println!("[LRAP] Checking environment variables:");
    let lrap_env = var("LRAP_RUNTIME_API_ENDPOINT").ok();
    let aws_env = var("AWS_LAMBDA_RUNTIME_API").ok();
    
    println!("[LRAP]   LRAP_RUNTIME_API_ENDPOINT={:?}", lrap_env);
    println!("[LRAP]   AWS_LAMBDA_RUNTIME_API={:?}", aws_env);
    
    let aws_lambda_runtime_api =
        match var("LRAP_RUNTIME_API_ENDPOINT").or_else(|_| var("AWS_LAMBDA_RUNTIME_API")) {
            Ok(v) => {
                println!("[LRAP] Found runtime API endpoint: {}", v);
                v
            },
            Err(_) => {
                eprintln!("[LRAP] ERROR: LRAP_RUNTIME_API_ENDPOINT or AWS_LAMBDA_RUNTIME_API not found");
                panic!("LRAP_RUNTIME_API_ENDPOINT or AWS_LAMBDA_RUNTIME_API not found")
            },
        };

    // Latch in the ORIGIN we should proxy to the application
    println!("[LRAP] Setting LAMBDA_RUNTIME_API to: {}", aws_lambda_runtime_api);
    LAMBDA_RUNTIME_API.set(aws_lambda_runtime_api.clone())
        .expect("Expected that mutate_runtime_env() has not been called before, but AWS_LAMBDA_RUNTIME_API was already set");

    let listener_port = var("LRAP_LISTENER_PORT")
        .ok()
        .and_then(|v| {
            println!("[LRAP] LRAP_LISTENER_PORT from env: {}", v);
            v.parse::<u16>().ok()
        })
        .or_else(|| {
            // Find a base port to use - start with default and increment if needed
            let base_port = crate::DEFAULT_PROXY_PORT;
            println!("[LRAP] Trying to use default port: {}", base_port);
            
            // We'll just return the default port now, but will try to bind dynamically in the server
            Some(base_port)
        })
        .unwrap();

    let lrap_api = format!("127.0.0.1:{}", listener_port);
    println!("[LRAP] Setting LRAP_API to: {}", lrap_api);

    LRAP_API.set(lrap_api.clone()).expect("aws_lambda_runtime_api_proxy_rs::env::LRAP_API was previously initialized and should not be");
}

/// Gets the original AWS_LAMBDA_RUNTIME_API.
///
#[allow(dead_code)]
pub fn sandbox_runtime_api() -> &'static str {
    match LAMBDA_RUNTIME_API.get() {
        Some(val) => {
            println!("[LRAP] Using cached sandbox_runtime_api: {}", val);
            val
        },
        None => {
            println!("[LRAP] Initializing environment variables to get sandbox_runtime_api");
            latch_runtime_env();
            let api = LAMBDA_RUNTIME_API.get().expect(
                "Error in setting and mutating AWS_LAMBDA_RUNTIME_API environment variables.",
            );
            println!("[LRAP] Retrieved sandbox_runtime_api: {}", api);
            api
        }
    }
}

/// Gets the new LRAP_API.
///
pub fn lrap_api() -> &'static str {
    match LRAP_API.get() {
        Some(val) => {
            println!("[LRAP] Using cached LRAP_API: {}", val);
            val
        },
        None => {
            println!("[LRAP] Initializing environment variables to get LRAP_API");
            latch_runtime_env();
            let api = LRAP_API.get().expect("Error in setting and mutating AWS_LAMBDA_RUNTIME_API dependent LRAP_API host:port.");
            println!("[LRAP] Retrieved LRAP_API: {}", api);
            api
        }
    }
}

/// Set the original Lambda Runtime API endpoint for proxying
pub fn set_original_runtime_api(endpoint: &str) {
    if ORIGINAL_RUNTIME_API.get().is_none() {
        println!("[LRAP] Setting original Lambda Runtime API endpoint: {}", endpoint);
        ORIGINAL_RUNTIME_API.set(endpoint.to_string())
            .expect("Error setting original Lambda Runtime API endpoint");
    } else {
        println!("[LRAP] Original Lambda Runtime API endpoint already set");
    }
}

/// Get the original Lambda Runtime API endpoint for proxying
pub fn original_runtime_api() -> &'static str {
    match ORIGINAL_RUNTIME_API.get() {
        Some(val) => {
            println!("[LRAP] Using cached original Lambda Runtime API: {}", val);
            val
        },
        None => {
            println!("[LRAP WARN] Original Lambda Runtime API endpoint not set, using sandbox_runtime_api as fallback");
            sandbox_runtime_api()
        }
    }
}
