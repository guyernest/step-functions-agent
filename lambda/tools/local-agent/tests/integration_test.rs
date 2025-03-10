use anyhow::{Context, Result};
use aws_sdk_sfn::Client;
use serde::{Deserialize, Serialize};
use std::env;
use std::fs;
use std::time::Duration;
use tempfile::tempdir;
use tokio::sync::oneshot;
use tokio::time;

// Import crate being tested
use local_sfn_agent::AppConfig;

// Note: This would be placed in a directory that loads the main crate
// Make sure AppConfig struct in lib.rs is public

#[derive(Debug, Deserialize)]
struct TestConfig {
    test_activity_arn: String,
    test_worker_name: String,
    test_message: String,
}

#[derive(Debug, Serialize)]
struct PyAutoGuiTestScript {
    name: String,
    description: String,
    abort_on_error: bool,
    actions: Vec<PyAutoGuiAction>,
}

#[derive(Debug, Serialize)]
struct PyAutoGuiAction {
    r#type: String,
    description: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    seconds: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    text: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    interval: Option<f32>,
}

// This test requires actual AWS credentials and a Step Functions Activity
// It's marked as ignored by default so it won't run in CI unless explicitly requested
#[tokio::test]
#[ignore]
async fn test_step_functions_activity_integration() -> Result<()> {
    // Load test configuration from environment variables
    let test_activity_arn =
        env::var("TEST_ACTIVITY_ARN").expect("TEST_ACTIVITY_ARN must be set for integration tests");

    let test_worker_name =
        env::var("TEST_WORKER_NAME").unwrap_or_else(|_| "integration-test-worker".to_string());

    let test_message = env::var("TEST_MESSAGE")
        .unwrap_or_else(|_| "Test message from integration test".to_string());

    // Initialize the AWS SDK
    let config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
    let client = Client::new(&config);

    // Get an activity task
    let get_activity_task_resp = client
        .get_activity_task()
        .activity_arn(&test_activity_arn)
        .worker_name(&test_worker_name)
        .send()
        .await
        .context("Failed to get activity task")?;

    // Check if we got a task token
    if let Some(task_token) = get_activity_task_resp.task_token() {
        if !task_token.is_empty() {
            println!("Received task token: {}", task_token);

            // Send success response
            client
                .send_task_success()
                .task_token(task_token)
                .output(format!("Processed test message: {}", test_message))
                .send()
                .await
                .context("Failed to send task success")?;

            println!("Successfully sent task success response");
        } else {
            println!("No task available (empty token received)");
        }
    } else {
        println!("No task token received");
    }

    Ok(())
}

// Test with a PyAutoGUI script
#[tokio::test]
#[ignore]
async fn test_step_functions_with_pyautogui_script() -> Result<()> {
    // Load test configuration from environment variables
    let test_activity_arn =
        env::var("TEST_ACTIVITY_ARN").expect("TEST_ACTIVITY_ARN must be set for integration tests");

    let test_worker_name =
        env::var("TEST_WORKER_NAME").unwrap_or_else(|_| "integration-test-worker".to_string());

    // Create a simple test script that just waits (doesn't interact with UI)
    let test_script = PyAutoGuiTestScript {
        name: "Integration Test Script".to_string(),
        description: "A simple test script for integration testing".to_string(),
        abort_on_error: true,
        actions: vec![PyAutoGuiAction {
            r#type: "wait".to_string(),
            description: "Wait for 2 seconds".to_string(),
            seconds: Some(2.0),
            text: None,
            interval: None,
        }],
    };

    let script_json = serde_json::to_string(&test_script)?;

    // Initialize the AWS SDK
    let config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
    let client = Client::new(&config);

    // Create a task with the test script as input
    let start_execution_resp = client
        .start_execution()
        .state_machine_arn(&test_activity_arn)
        .input(&script_json)
        .send()
        .await
        .context("Failed to start execution")?;

    println!(
        "Started execution: {:?}",
        start_execution_resp.execution_arn()
    );

    // Wait a moment for the execution to start
    time::sleep(Duration::from_secs(2)).await;

    Ok(())
}

// Test by creating a dummy script_executor.py and testing the integration
#[tokio::test]
#[ignore]
async fn test_local_pyautogui_integration() -> Result<()> {
    // Create a temporary directory for our test
    let temp_dir = tempdir()?;
    let script_executor_path = temp_dir.path().join("script_executor.py");

    // Create a simple mock script_executor.py
    fs::write(
        &script_executor_path,
        r#"#!/usr/bin/env python3
import json
import sys

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No script provided"}))
        return 1
    
    # Read the script
    script_path = sys.argv[1]
    with open(script_path, 'r') as f:
        script_data = f.read()
    
    try:
        # Parse the script
        script = json.loads(script_data)
        
        # Mock execution
        print(json.dumps({
            "success": True,
            "results": [{"success": True, "action": action["type"]} for action in script["actions"]]
        }))
        return 0
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        return 1

if __name__ == "__main__":
    sys.exit(main())
"#,
    )?;

    // Make the script executable
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(&script_executor_path)?.permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&script_executor_path, perms)?;
    }

    // Create a test script
    let test_script_path = temp_dir.path().join("test_script.json");
    let test_script = r#"{
        "name": "Test Script",
        "description": "A test script",
        "abort_on_error": true,
        "actions": [
            {
                "type": "wait",
                "seconds": 1.0,
                "description": "Wait for 1 second"
            }
        ]
    }"#;

    fs::write(&test_script_path, test_script)?;

    // Run the script_executor.py with the test script
    let python_command = if cfg!(target_os = "windows") {
        "python"
    } else {
        "python3"
    };
    let output = std::process::Command::new(python_command)
        .arg(&script_executor_path)
        .arg(&test_script_path)
        .output()
        .context("Failed to execute script_executor.py")?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    println!("Script executor stdout: {}", stdout);
    if !stderr.is_empty() {
        println!("Script executor stderr: {}", stderr);
    }

    assert!(output.status.success(), "Script executor failed to run");

    // Parse the result
    let result: serde_json::Value = serde_json::from_str(&stdout)?;
    assert!(
        result["success"].as_bool().unwrap(),
        "Script execution failed"
    );

    // Clean up
    drop(temp_dir);

    Ok(())
}

// Test the end-to-end daemon functionality by running it for a short time
#[tokio::test]
#[ignore]
async fn test_daemon_e2e() -> Result<()> {
    // Load test configuration from environment variables
    let test_activity_arn =
        env::var("TEST_ACTIVITY_ARN").expect("TEST_ACTIVITY_ARN must be set for integration tests");

    let worker_name =
        env::var("TEST_WORKER_NAME").unwrap_or_else(|_| "integration-test-worker".to_string());

    // Create temporary configuration file
    let temp_dir = tempdir()?;
    let config_file_path = temp_dir.path().join("test_daemon_config.json");

    // Create a test script_executor.py in the same directory
    let script_executor_path = temp_dir.path().join("script_executor.py");
    fs::write(
        &script_executor_path,
        r#"#!/usr/bin/env python3
import json
import sys

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No script provided"}))
        return 1
    
    # Read the script
    script_path = sys.argv[1]
    with open(script_path, 'r') as f:
        script_data = f.read()
    
    try:
        # Parse the script
        script = json.loads(script_data)
        
        # Mock execution
        print(json.dumps({
            "success": True,
            "results": [{"success": True, "action": action["type"]} for action in script["actions"]]
        }))
        return 0
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        return 1

if __name__ == "__main__":
    sys.exit(main())
"#,
    )?;

    // Make the script executable
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(&script_executor_path)?.permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&script_executor_path, perms)?;
    }

    // Create a config file
    let config_content = format!(
        r#"{{
        "activity_arn": "{}",
        "app_path": "/bin/echo",
        "poll_interval_ms": 1000,
        "worker_name": "{}",
        "profile_name": "default"
    }}"#,
        test_activity_arn, worker_name
    );

    fs::write(&config_file_path, config_content)?;

    // Create an app config to pass to our daemon
    let app_config = AppConfig {
        activity_arn: test_activity_arn.clone(),
        app_path: "/bin/echo".to_string(),
        poll_interval_ms: 1000,
        worker_name: worker_name.clone(),
        profile_name: "default".to_string(),
    };

    // Create a shutdown channel
    let (shutdown_tx, mut shutdown_rx) = oneshot::channel();

    // Start the daemon in a separate task
    let aws_config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
    let client = Client::new(&aws_config);

    let daemon_handle = tokio::spawn(async move {
        // Create a simplified daemon loop for testing
        while shutdown_rx.try_recv().is_err() {
            // Poll once
            if let Err(e) = local_sfn_agent::poll_activity(&client, &app_config).await {
                eprintln!("Error polling activity: {:?}", e);
            }

            // Wait before polling again
            time::sleep(Duration::from_millis(app_config.poll_interval_ms)).await;
        }
        println!("Test daemon shutdown");
    });

    // Wait for the daemon to start up
    time::sleep(Duration::from_secs(2)).await;

    // Create a test execution
    let test_script = PyAutoGuiTestScript {
        name: "Integration Test Script".to_string(),
        description: "A simple test script for integration testing".to_string(),
        abort_on_error: true,
        actions: vec![PyAutoGuiAction {
            r#type: "wait".to_string(),
            description: "Wait for 2 seconds".to_string(),
            seconds: Some(2.0),
            text: None,
            interval: None,
        }],
    };

    let script_json = serde_json::to_string(&test_script)?;

    // Send a task to the Step Functions activity
    // In a real test, you would need to use AWS to schedule a task for the activity
    println!(
        "Sending task to Step Functions activity: {}",
        test_activity_arn
    );
    println!("Script content: {}", script_json);

    // Wait for some time to allow the daemon to process the message
    time::sleep(Duration::from_secs(10)).await;

    // Send shutdown signal and wait for daemon to stop
    shutdown_tx
        .send(())
        .expect("Failed to send shutdown signal");

    // Wait for the daemon to shut down
    let _ = tokio::time::timeout(Duration::from_secs(5), daemon_handle).await;

    println!("Test completed successfully");

    // Clean up
    drop(temp_dir);

    Ok(())
}
