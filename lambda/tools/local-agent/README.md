# Local Agent for GUI Automation with PyAutoGUI

This is an implementation of a local agent that runs on a local machine (Windows, macOS, or Linux) to poll commands to execute locally from the AI Agent. The local agent is implemented in Rust and uses the AWS SDK for Rust to interact with Step Functions Activities.

The AI agent analyzes the incoming requests from the users and decides what commands should be executed locally. These commands can be either:

1. Traditional application executions (original functionality)
2. PyAutoGUI automation scripts for GUI applications (new functionality)

The local agent polls the Step Functions Activity for messages, executes the commands or scripts, and sends the results back to the AI agent.

## Input and Output Format

### Input Format

The local agent expects input from Step Functions Activity in the following format:

```json
{
  "id": "toolu_01Q6nguQRXatf69aVjWtoaYt",
  "input": {
    "script": {
      "name": "Check Account ID Existence",
      "description": "Check if Account ID 1004 exists in the system",
      "abort_on_error": true,
      "actions": [
        {
          "type": "launch",
          "app": "local_application.exe",
          "wait": 1.5,
          "description": "Launch local application"
        },
        ...more actions...
      ]
    }
  },
  "name": "execute_automation_script"
}
```

The key elements are similar to other tool calls and are:

* `id`: A unique identifier for the task
* `input`: Contains the automation instructions
  * `script`: The script definition containing name, description, and actions
* `name`: The task name or action to perform

### Output Format

The local agent responds with an output that mirrors the input structure, but with `script_output` replacing the `script` element:

```json
{
  "id": "toolu_01Q6nguQRXatf69aVjWtoaYt",
  "input": {
    "script_output": {
      "success": true,
      "results": [
        {
          "action": "launch",
          "status": "success",
          "details": "Launched local_application.exe"
        },
        ...more results...
      ]
    }
  },
  "name": "execute_automation_script"
}
```

In case of errors, the `script_output` will contain error information:

```json
{
  "id": "toolu_01Q6nguQRXatf69aVjWtoaYt",
  "input": {
    "script_output": {
      "success": false,
      "error": "ScriptExecutionError",
      "details": "Failed to launch application"
    }
  },
  "name": "execute_automation_script"
}
```

## Getting Started

### Prerequisites

* Rust 1.70 or later [Rust documentations](https://doc.rust-lang.org/cargo/getting-started/installation.html)

    ```bash
    curl https://sh.rustup.rs -sSf | sh
    ```

* Python 3.6 or later (for PyAutoGUI scripts)
* uv package manager (for automatic dependency management) [uv documentation](https://docs.astral.sh/uv/getting-started/installation/)

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

#### Fine Grained IAM role

You need to create IAM role with Step Functions GetActivityTask and SendTaskSuccess permissions to read the activity task from the `daemon_config.json` file and send the task success back to the Step Functions Activity.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "states:GetActivityTask",
                "states:SendTaskSuccess"
            ],
            "Resource": "arn:aws:states:us-west-2:YOUR_ACCOUNT_ID:activity:YOUR_ACTIVITY_NAME"
        }
    ]
}
```

#### AWS credentials configured locally

Follow the [official documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) to configure your AWS credentials locally.

```text
[profile PROFILE_NAME]
aws_access_key_id=YOUR_ACCESS_KEY
aws_secret_access_key=YOUR_SECRET_KEY
region=eu-west-1
```

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/guyernest/step-functions-agent.git
   cd lambda/tools/local-agent
   ```

2. Build the Rust project:

   ```bash
   cargo build --release
   ```

3. Install uv if not already installed:

    For macOS/Linux:

    ```bash
    curl -sSf https://astral.sh/uv/install.sh | sh
    ```

    For Windows (PowerShell):

    ```powershell
    irm https://astral.sh/uv/install.ps1 | iex
    ```

    For more detailed installation options, see the [official documentation](
    https://docs.astral.sh/uv/getting-started/installation/)

4. Configure the daemon by editing the `daemon_config.json` file in the root directory:

   ```json
   {
       "activity_arn": "arn:aws:states:us-west-2:YOUR_ACCOUNT_ID:activity:YOUR_ACTIVITY_NAME",
       "app_path": "uv run script_executor.py",
       "poll_interval_ms": 5000,
       "worker_name": "local-agent-worker",
       "profile_name": "PROFILE_NAME"
   }
   ```

5. Run the daemon:

   ```shell
   cargo run --release
   ```

please note that you can change the log level of the daemon by setting the `RUST_LOG` environment variable.

```shell
RUST_LOG=info cargo run --release
```

## Using PyAutoGUI Script Automation

The local agent can now automatically execute PyAutoGUI scripts for automating GUI applications. These scripts are defined in JSON format and can control keyboard and mouse actions on the local machine.

### Script Format

Scripts must be in JSON format and include an `actions` array of automation steps. The script is included within the `input.script` property of the task input:

```json
{
  "id": "unique_task_id",
  "input": {
    "script": {
      "name": "Example Automation Script",
      "description": "Demonstrates PyAutoGUI automation",
      "abort_on_error": true,
      "actions": [
        {
          "type": "launch",
          "app": "notepad",
          "wait": 1.5,
          "description": "Launch Notepad application"
        },
        {
          "type": "type",
          "text": "Hello, world!",
          "interval": 0.05,
          "description": "Type text"
        },
        {
          "type": "hotkey",
          "keys": ["ctrl", "s"],
          "description": "Save the document"
        }
      ]
    }
  },
  "name": "execute_automation_script"
}
```

### Supported Actions

* **click**: Click at a specific position or image
* **rightclick**: Right-click at a specific position or image
* **doubleclick**: Double-click at a specific position or image
* **moveto**: Move the mouse cursor to a position
* **type**: Type text
* **press**: Press a specific keyboard key
* **hotkey**: Press a combination of keys (like Ctrl+C)
* **wait**: Wait for a specified time
* **locateimage**: Find an image on the screen
* **dragto**: Drag from current position to a new position
* **scroll**: Scroll the mouse wheel
* **launch**: Launch an application

### Image-Based Actions

The local agent supports powerful image-based automation for more reliable GUI interactions. There are two main ways to use image detection:

#### 1. Direct Image Clicking (Recommended Method)

The simplest way to click on a UI element is to include an image directly in a click action:

```json
{
  "type": "click",
  "image": "examples/button.png",
  "confidence": 0.9,
  "description": "Click on the button"
}
```

This is equivalent to `pyautogui.click('button.png')` in Python code. The same pattern works with `rightclick` and `doubleclick` actions.

#### 2. Two-Step Image Location and Action

For more complex workflows, you can first locate an image and then perform actions relative to it:

```json
{
  "type": "locateimage",
  "image": "examples/button.png",
  "confidence": 0.8,
  "move_cursor": true,
  "description": "Find the button image"
},
{
  "type": "click",
  "description": "Click at the located image position"
}
```

This approach is useful when you need to:

* Verify an element exists before acting on it
* Make decisions based on whether an image is found
* Perform multiple actions at the same location

#### Image Location Parameters

* **image**: Path to the image file (can be relative or absolute)
* **confidence**: Optional match threshold from 0.0 to 1.0 (default: 0.9)
* **move_cursor**: Whether to move the cursor to the found image (default: true)
* **click_after_locate**: Whether to click after finding the image (default: false)

#### Advanced Image Detection

The agent uses multiple strategies to find images:

1. First, it tries PyAutoGUI's standard image detection
2. If available, it falls back to OpenCV for more advanced detection with multiple algorithms
3. It supports both color and grayscale matching to maximize success rates

#### Image Path Resolution

The agent automatically searches for images in:

* Absolute paths if provided
* Current working directory
* Script directory
* Examples subdirectory

For best results, store your images in the same directory as your script or in the examples directory.

### Example Scripts

Example scripts are included in the `examples` directory:

* `image_detection_examples.json`: Demonstrates different patterns for image-based automation
* `textedit_mac_example.json`: Demonstrates automating TextEdit on macOS
* `notepad_windows_example.json`: Demonstrates automating Notepad on Windows

### Best Practices for Image-Based Automation

For reliable image detection, follow these guidelines:

1. **Use high-quality, distinctive images**:

   * Capture clean, high*resolution screenshots
   * Include enough context to make images unique
   * Avoid using very small images that might match in multiple places

2. **Optimize detection parameters**:

   * Start with confidence values around 0.9
   * Lower confidence (0.7*0.8) if you're having trouble with matches
   * Higher confidence (0.95+) if you're getting false positives

3. **Handle different screen resolutions**:

   * Test your automation on the target resolution
   * Prepare multiple image variants for different resolutions/themes if needed

4. **Add sufficient waiting times**:

   * Include wait actions between UI interactions
   * Allow time for animations and screen transitions

5. **Implement fallback strategies**:

   * Use alternative navigation methods when possible (keyboard shortcuts)
   * Have alternative images for the same UI element (light/dark mode)

6. **Troubleshooting tips**:

   * Check the `screenshots` directory for debug screenshots (created automatically)
   * View annotated matches in the debug images to understand detection issues
   * Try grayscale images if color matching is inconsistent

### How It Works

1. When the local agent receives a message in the format described above with a `script` element in the `input` object, it will automatically use the PyAutoGUI script executor
2. The extracted script content is saved to a temporary file
3. The agent executes the script using Python with the required PyAutoGUI dependencies
4. Results are captured and returned to the Step Functions Activity in the same structure as the input, but with `script_output` replacing the `script` element
5. The response maintains all other properties from the original input (such as `id` and `name`)

#### Dependency Management with uv

The system uses `uv run` to execute the Python script with its dependencies. This approach:

* Eliminates the need to pre*install PyAutoGUI and its dependencies
* Ensures each execution has the exact dependencies it needs
* Avoids conflicts with other Python packages in the system
* Works seamlessly across different operating systems

When execution starts, the agent will try:

```bash
uv run --pip=pyautogui --pip=pillow script_executor.py script.json
```

This creates an isolated environment with PyAutoGUI and Pillow installed, runs the script, and then cleans up automatically.

## Testing Guide

This document outlines the testing strategy for the Local Agent application, including unit tests, integration tests, and how to run them.

### Test Structure

The test suite includes:

1. **Unit Tests**: Test individual components in isolation
   * Configuration loading and parsing
   * Message processing logic
   * Error handling

2. **Mock Tests**: Test interactions with AWS using mocks
   * Step Functions Activity Task operations with mock responses
   * PyAutoGUI script execution with mocked components

3. **Integration Tests**: Test actual AWS interactions
   * Real Step Functions Activity operations (requires AWS credentials)
   * End-to-end daemon functionality
   * PyAutoGUI script executor testing

## Running the Tests

### Unit and Mock Tests

These tests don't require any AWS credentials and can be run with:

```bash
cargo test
```

### Integration Tests

These tests require valid AWS credentials and an actual SQS queue. They're marked with `#[ignore]` to prevent them from running in CI pipelines accidentally.

To run integration tests:

```bash
# Set up test environment variables for Step Functions Activity tests
export TEST_ACTIVITY_ARN="arn:aws:states:us-west-2:YOUR_ACCOUNT_ID:activity:YOUR_ACTIVITY_NAME"
export TEST_WORKER_NAME="integration-test-worker" 
export TEST_MESSAGE="Test message from integration test"

# Run the ignored tests
cargo test -- --ignored
```

These integration tests include:

1. Basic Step Functions Activity interaction
2. PyAutoGUI script execution via Step Functions
3. Local testing of the script_executor.py
4. End-to-end daemon testing with mocked components

## Setting Up Test Environment

### Local Testing Environment

1. Create a test Step Functions Activity in your AWS account
2. Set up AWS credentials locally (using `~/.aws/credentials` or environment variables)
3. Create a test config file with the proper Activity ARN and worker name
4. Make sure Python 3.6+ and uv are installed for PyAutoGUI script tests

### CI/CD Testing Environment

For CI/CD pipelines, consider:

1. Using temporary AWS resources for testing
2. Setting up IAM roles with minimal permissions
3. Cleaning up test resources after test runs

## Mocking Strategy

The tests use a simplified mock implementation for the Step Functions client and PyAutoGUI script executor. In a more robust implementation, you could use the `mockall` crate to create more sophisticated mocks with expectations.

## Test Coverage

To generate test coverage reports:

```bash
# Install cargo-tarpaulin if not already installed
cargo install cargo-tarpaulin

# Generate coverage report
cargo tarpaulin --out Html
```

## Expanding the Test Suite

When adding new features to the daemon, consider:

1. Adding unit tests for any new functions
2. Updating mock tests for AWS interactions
3. Adding integration tests for critical paths

## Troubleshooting Tests

Common issues:

* **AWS credential errors**: Make sure valid credentials are set up for integration tests
* **Step Functions permissions**: Ensure test credentials have proper permissions on Step Functions Activities
* **Python environment issues**: Ensure Python and uv are properly installed for script executor tests
* **Timing issues**: Some tests may fail due to timing; consider adding appropriate delays

## Best Practices

1. Keep unit tests fast and independent
2. Use meaningful assertions that test behavior, not implementation details
3. Mock external dependencies for predictable tests
4. Use integration tests sparingly for critical flows only
