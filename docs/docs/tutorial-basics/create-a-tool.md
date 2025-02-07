---
sidebar_position: 1
---

# Building a New Tool

This tutorial will guide you through the process of creating a new tool for the AI agents system using Python. While Python is used in this example, the system supports multiple languages including TypeScript, Java, and Rust. Future tutorials will cover these languages.

## Prerequisites

- AWS Account
- AWS CDK installed
- Python 3.12 or later
- Basic understanding of AWS Lambda

## Step 1: Create the Tool Directory Structure

Create a new directory for your tool in the `lambda/tools` directory:

```bash
mkdir -p lambda/tools/my-new-tool
cd lambda/tools/my-new-tool
```

## Step 2: Set Up the Python Environment

1. Create a requirements.in file for your tool's dependencies:

  ```bash
  touch requirements.in
  ```

1. Add your dependencies to requirements.in. For example:

  ```plaintext title="requirements.in"
  requests
  boto3
  ```

1. Generate requirements.txt using uv:

  ```bash
  uv pip compile requirements.in -o requirements.txt
  ```

## Step 3: Implement the Tool Handler

1. Create an index.py file in your tool directory with this basic structure:

```python title="index.py"
import json
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Extract tool information from the event
    tool_use = event
    tool_name = tool_use['name']
    tool_input = tool_use['input']
    
    try:
        # Implement your tool logic here
        match tool_name:
            case 'my_tool_function':
                result = handle_my_tool(tool_input)
            case _:
                result = json.dumps({
                    'error': f"Unknown tool name: {tool_name}"
                })
                
        # Return the result in the expected format
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        }
        
    except Exception as e:
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": json.dumps({
                'error': str(e)
            })
        }

def handle_my_tool(input_data: Dict[str, Any]) -> str:
    # Implement your specific tool logic here
    return json.dumps({
        'result': 'Tool execution successful',
        'data': input_data
    })
```

## Step 4: Add Unit Tests

1. Create a tests directory:

  ```bash
  mkdir tests
  ```

1. Create a test file `tests/test_my_tool.py` with the following content:

  ```python title="tests/test_my_tool.py"
  import pytest
  from my_new_tool.index import lambda_handler

  def test_my_tool():
      event = {
          "name": "my_tool_function",
          "id": "test_execution_id",
          "input": {"test": "data"},
          "type": "tool_use"
      }
      
      response = lambda_handler(event, None)
      
      assert response["type"] == "tool_result"
      assert response["name"] == "my_tool_function"
      assert response["tool_use_id"] == "test_execution_id"
      assert "content" in response
  ```

## Step 5: Configure SAM Template

1. Add your function to the `template.yaml` file:

  ```yaml title="template.yaml"
  MyNewToolFunction:
      Type: AWS::Serverless::Function
      Properties:
        CodeUri: lambda/tools/my-new-tool
        Handler: index.lambda_handler
        Runtime: python3.12
        Timeout: 90
        MemorySize: 128
        Environment:
          Variables:
            POWERTOOLS_SERVICE_NAME: ai-agents-tools
        Architectures:
          - arm64
        Policies:
          - AWSLambdaBasicExecutionRole
  ```

## Step 6: Deploy Using CDK

1. Add the following to your CDK stack:

  ```python title="cdk_stack.py"
  from aws_cdk import (
      aws_lambda as _lambda,
      aws_lambda_python_alpha as _lambda_python,
      Duration,
  )

  # Create the Lambda function
  my_new_tool_lambda = _lambda_python.PythonFunction(
      self, 
      "MyNewToolFunction",
      function_name="MyNewToolFunction",
      description="My new tool Lambda function for AI agents",
      entry="lambda/tools/my-new-tool",
      runtime=_lambda.Runtime.PYTHON_3_12,
      timeout=Duration.seconds(90),
      memory_size=128,
      index="index.py",
      handler="lambda_handler",
      architecture=_lambda.Architecture.ARM_64,
  )
  ```

## Step 7: Test Locally

1. Create a test event file `tests/my-tool-event.json`:

  ```json title="tests/my-tool-event.json"
  {
      "name": "my_tool_function",
      "id": "test_execution_id",
      "input": {
        "test": "data"
      },
      "type": "tool_use"
  }
  ```

1. Test using SAM CLI:

  ```bash
  sam build
  sam local invoke MyNewToolFunction -e tests/my-tool-event.json
  ```

## Step 8: Deploy

Deploy your changes using CDK:

```bash
cdk deploy
```

## Next Steps

Add more sophisticated error handling
Implement additional tool functions
Add integration tests
Consider adding CloudWatch logs and metrics
Document the tool's API for LLM consumption
Future tutorials will cover implementing tools in other supported languages like TypeScript, Java, and Rust.
