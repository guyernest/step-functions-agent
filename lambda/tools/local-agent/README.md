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
        }
      ]
    }
  },
  "name": "execute_automation_script"
}
```

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
        }
      ]
    }
  },
  "name": "execute_automation_script"
}
```

## Getting Started

### Prerequisites

* Rust 1.70 or later
* Python 3.6 or later (for PyAutoGUI scripts)
* uv package manager (for automatic dependency management)

### Installation

1. Clone the repository and navigate to the local-agent directory
2. Build the Rust project: `cargo build --release`
3. Install uv package manager
4. Configure `daemon_config.json` with your Activity ARN and AWS profile
5. Run the daemon: `cargo run --release`

## PyAutoGUI Script Automation

The local agent supports PyAutoGUI scripts for GUI automation with actions like:

* **click**: Click at position or image
* **type**: Type text
* **hotkey**: Press key combinations
* **locateimage**: Find images on screen
* **launch**: Launch applications
* And many more...

For detailed documentation, examples, and troubleshooting, see the complete README content above.