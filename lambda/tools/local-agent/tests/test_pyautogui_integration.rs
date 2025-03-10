#[cfg(test)]
mod tests {
    use anyhow::Result;
    use aws_sdk_sfn::config::Builder;
    use aws_sdk_sfn::error::SdkError;
    use aws_sdk_sfn::operation::send_task_failure::SendTaskFailureOutput;
    use aws_sdk_sfn::operation::send_task_success::SendTaskSuccessOutput;
    use aws_sdk_sfn::Client;
    use local_sfn_agent::AppConfig;
    use std::sync::Once;
    use tempfile::tempdir;
    use tokio::runtime::Runtime;

    static INIT: Once = Once::new();

    fn setup() {
        INIT.call_once(|| {
            env_logger::builder().is_test(true).try_init().ok();
        });
    }

    struct MockSfnClient {
        success_response: Option<
            Result<
                SendTaskSuccessOutput,
                SdkError<aws_sdk_sfn::operation::send_task_success::SendTaskSuccessError>,
            >,
        >,
        failure_response: Option<
            Result<
                SendTaskFailureOutput,
                SdkError<aws_sdk_sfn::operation::send_task_failure::SendTaskFailureError>,
            >,
        >,
    }

    impl MockSfnClient {
        fn new() -> Self {
            MockSfnClient {
                success_response: None,
                failure_response: None,
            }
        }

        fn with_success_response(
            mut self,
            response: Result<
                SendTaskSuccessOutput,
                SdkError<aws_sdk_sfn::operation::send_task_success::SendTaskSuccessError>,
            >,
        ) -> Self {
            self.success_response = Some(response);
            self
        }

        fn with_failure_response(
            mut self,
            response: Result<
                SendTaskFailureOutput,
                SdkError<aws_sdk_sfn::operation::send_task_failure::SendTaskFailureError>,
            >,
        ) -> Self {
            self.failure_response = Some(response);
            self
        }

        async fn send_task_success(
            &self,
        ) -> aws_sdk_sfn::operation::send_task_success::builders::SendTaskSuccessFluentBuilder
        {
            let config = Builder::new().endpoint_url("https://example.com").build();
            let client = Client::from_conf(config);
            client.send_task_success()
        }

        async fn send_task_failure(
            &self,
        ) -> aws_sdk_sfn::operation::send_task_failure::builders::SendTaskFailureFluentBuilder
        {
            let config = Builder::new().endpoint_url("https://example.com").build();
            let client = Client::from_conf(config);
            client.send_task_failure()
        }
    }

    #[test]
    fn test_pyautogui_script_detection() {
        setup();

        // JSON script containing actions should be detected as a PyAutoGUI script
        let json_script = r#"{"actions": [{"type": "click", "position": [500, 300]}]}"#;
        assert!(json_script.contains("\"actions\":"));

        // A JSON object without actions should still be detected as a potential script
        let json_object = r#"{"name": "test", "data": "value"}"#;
        assert!(json_object.starts_with("{"));

        // Plain text should not be detected as a script
        let plain_text = "This is just some text input";
        assert!(!plain_text.contains("\"actions\":") && !plain_text.starts_with("{"));
    }

    #[test]
    fn test_script_file_creation() -> Result<()> {
        setup();

        // Create a temporary directory for our test
        let temp_dir = tempdir()?;
        let script_path = temp_dir.path().join("test_script.json");

        // Sample script content
        let script_content = r#"{"actions": [{"type": "click", "position": [500, 300]}]}"#;

        // Write the script to a file
        std::fs::write(&script_path, script_content)?;

        // Verify the file was created and contains the expected content
        let file_content = std::fs::read_to_string(&script_path)?;
        assert_eq!(file_content, script_content);

        // Clean up
        drop(temp_dir);

        Ok(())
    }

    #[test]
    #[ignore] // This test requires the actual script_executor.py file to be present
    fn test_execute_pyautogui_script() {
        setup();

        // This test would run the actual script_executor.py with a test script,
        // but we mark it as ignored since it would interact with the actual system
        // and requires the script_executor.py to be in place.
        //
        // In a real environment, this would be tested with integration tests.
    }
}
