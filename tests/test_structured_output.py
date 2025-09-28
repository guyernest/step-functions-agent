"""
Test script for structured output functionality.
Demonstrates the flow from agent call to structured output extraction.
"""

import json
import boto3
from typing import Dict, Any

# Initialize AWS clients
stepfunctions = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

def test_broadband_structured_output():
    """Test the broadband checker with structured output."""

    # Input for the state machine
    input_data = {
        "agent": "broadband-checker",
        "messages": [
            {
                "role": "user",
                "content": "Check broadband availability for 10 Downing Street, London, SW1A 2AA"
            }
        ],
        "output_format": "broadband_check",  # Request structured output
        "model": "claude-3-sonnet",
        "temperature": 0.7,
        "max_tokens": 4096,
        "tools": [],  # Will be populated by PrepareAgentContext
        "system": ""   # Will be enhanced by PrepareAgentContext
    }

    print("Testing broadband checker with structured output...")
    print(f"Input: {json.dumps(input_data, indent=2)}")

    # Start execution
    response = stepfunctions.start_execution(
        stateMachineArn='arn:aws:states:us-east-1:xxx:stateMachine:broadband-checker-agent',
        input=json.dumps(input_data)
    )

    execution_arn = response['executionArn']
    print(f"Started execution: {execution_arn}")

    # Wait for completion
    import time
    while True:
        status = stepfunctions.describe_execution(executionArn=execution_arn)

        if status['status'] != 'RUNNING':
            break

        time.sleep(2)

    # Check results
    if status['status'] == 'SUCCEEDED':
        output = json.loads(status['output'])
        print("\n✅ Execution succeeded!")
        print("\nStructured output:")
        print(json.dumps(output.get('structured_output'), indent=2))

        # Validate the structured output
        structured_data = output.get('structured_output')
        if structured_data:
            print("\n📊 Extracted data:")
            print(f"  Exchange Station: {structured_data.get('exchange_station')}")
            print(f"  Download Speed: {structured_data.get('download_speed')} Mbps")
            print(f"  Upload Speed: {structured_data.get('upload_speed')} Mbps")
            print(f"  Screenshot URL: {structured_data.get('screenshot_url', 'Not provided')}")
    else:
        print(f"\n❌ Execution failed: {status['status']}")
        if 'error' in status:
            print(f"Error: {status['error']}")

def test_prepare_context_locally():
    """Test the PrepareAgentContext Lambda locally."""

    # Simulate the Lambda event
    event = {
        "agent": "broadband-checker",
        "messages": [{"role": "user", "content": "Check broadband"}],
        "tools": [],
        "system": "You are a helpful assistant.",
        "output_format": "broadband_check"
    }

    # Simulate agent registry entry
    agent_config = {
        "agentId": "broadband-checker",
        "structuredOutput": {
            "enabled": True,
            "enforced": True,
            "toolName": "return_broadband_data",
            "schemas": {
                "broadband_check": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "exchange_station": {"type": "string"},
                            "download_speed": {"type": "number"},
                            "upload_speed": {"type": "number"},
                            "screenshot_url": {"type": "string"}
                        },
                        "required": ["exchange_station", "download_speed", "upload_speed"]
                    },
                    "description": "Extract broadband availability information",
                    "examples": [
                        {
                            "exchange_station": "Kensington Exchange",
                            "download_speed": 67.0,
                            "upload_speed": 20.0,
                            "screenshot_url": "https://example.com/screenshot.png"
                        }
                    ]
                },
                "defaultSchema": "broadband_check"
            }
        }
    }

    print("\n📝 Testing PrepareAgentContext Lambda...")
    print(f"Input event: {json.dumps(event, indent=2)}")

    # Process (this would be the Lambda handler)
    from lambda_function import enhance_system_prompt, build_structured_output_tool

    schema_config = agent_config["structuredOutput"]["schemas"]["broadband_check"]
    tool = build_structured_output_tool(schema_config, "return_broadband_data")

    enhanced_system = enhance_system_prompt(
        event["system"],
        "return_broadband_data",
        "broadband_check",
        schema_config.get("examples", [])
    )

    print("\n🔧 Generated tool:")
    print(json.dumps(tool, indent=2))

    print("\n📜 Enhanced system prompt:")
    print(enhanced_system)

if __name__ == "__main__":
    # Test PrepareContext locally
    test_prepare_context_locally()

    # Uncomment to test with actual Step Functions
    # test_broadband_structured_output()