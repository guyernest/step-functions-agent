/// Quick test to verify Activity polling connection
/// Usage: cargo run --example test_activity_connection

use aws_config;
use aws_sdk_sfn::Client as SfnClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize simple logging
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .init();

    println!("Testing Activity Connection");
    println!("============================");

    // Configuration
    let profile = "local-browser";
    let activity_arn = "arn:aws:states:eu-west-1:923154134542:activity:browser-remote-prod";
    let region = "eu-west-1";

    println!("Profile: {}", profile);
    println!("Activity ARN: {}", activity_arn);
    println!("Region: {}", region);
    println!();

    // Load AWS config
    println!("Loading AWS credentials...");
    let aws_config = aws_config::from_env()
        .profile_name(profile)
        .region(aws_sdk_sfn::config::Region::new(region.to_string()))
        .load()
        .await;

    let sfn_client = SfnClient::new(&aws_config);
    println!("✓ AWS client initialized");
    println!();

    // Test polling (with short timeout)
    println!("Attempting to poll for task (will timeout after ~60s if no tasks available)...");
    println!("Press Ctrl+C to cancel");
    println!();

    match sfn_client
        .get_activity_task()
        .activity_arn(activity_arn)
        .worker_name("test-connection")
        .send()
        .await
    {
        Ok(response) => {
            if let (Some(task_token), Some(_input)) = (response.task_token(), response.input()) {
                if !task_token.is_empty() {
                    println!("✓ SUCCESS: Received a task!");
                    println!("  Task token length: {}", task_token.len());
                    println!();
                    println!("NOTE: We won't execute this task in the test.");
                    return Ok(());
                }
            }

            println!("✓ SUCCESS: Connection works!");
            println!("  No tasks currently available (this is normal)");
            println!("  The poller is able to connect and poll for tasks.");
        }
        Err(e) => {
            println!("✗ ERROR: Failed to poll for activity task");
            println!();

            // Extract detailed error information
            if let Some(service_err) = e.as_service_error() {
                let code = service_err.meta().code().unwrap_or("Unknown");
                let message = service_err.meta().message().unwrap_or("No message");

                println!("Error Type: AWS Service Error");
                println!("Error Code: {}", code);
                println!("Error Message: {}", message);
                println!();

                // Provide troubleshooting based on error
                match code {
                    "AccessDeniedException" | "UnauthorizedOperation" => {
                        println!("TROUBLESHOOTING:");
                        println!("  This is a permission error. Check that:");
                        println!("  1. Your AWS credentials have 'states:GetActivityTask' permission");
                        println!("  2. The IAM policy allows access to this Activity ARN");
                        println!("  3. The AWS profile '{}' has the correct permissions", profile);
                    }
                    "InvalidArn" | "ActivityDoesNotExist" => {
                        println!("TROUBLESHOOTING:");
                        println!("  The Activity ARN appears to be invalid or doesn't exist:");
                        println!("  1. Verify the Activity ARN in your configuration");
                        println!("  2. Ensure the Activity exists in region '{}'", region);
                        println!("  3. Check the ARN format matches expected pattern");
                    }
                    _ => {
                        println!("TROUBLESHOOTING:");
                        println!("  Check the AWS documentation for error code: {}", code);
                    }
                }
            } else {
                println!("Error Type: SDK/Network Error");
                println!("Error: {}", e);
                println!();
                println!("TROUBLESHOOTING:");
                println!("  1. Check your internet connection");
                println!("  2. Verify the AWS region '{}' is correct", region);
                println!("  3. Check firewall/proxy settings");
            }

            return Err(e.into());
        }
    }

    Ok(())
}
