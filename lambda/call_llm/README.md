# Call LLM Lambda Function

This directory contains the implementation of the various lambda functions used to call the different LLM (Anthropic, OpenAI, AI21, etc.) with messages history and tools.

## Folder structure

```txt
├── lambda/
    └── call_llm/   
        ├── __init__.py
        ├── lambda_layer/ (the common layer for all the LLM Lambda functions)
        │   ├── python/
        │   │   ├── __init__.py
        │   │   ├── common/
        │   │   │   ├── __init__.py
        │   │   │   ├── base_llm.py (abstract class to define the interface for the LLM handlers)
        │   │   │   └── config.py
        ├── functions/
        │   ├── __init__.py
        │   ├── anthropic_llm/ 
        │   │   ├── claude_handler.py (implementation of the Claude LLM handler)
        │   │   ├── claude_lambda.py (implementation of the Claude LLM Lambda function)
        │   │   ├── requirements.txt
        │   │   └── template.yaml (for SAM local testing) (optional)
        │   ├── bedrock_llm/ (implementation of the Bedrock models)
        │   │   ├── nova_handler.py
        │   │   ├── nova_lambda.py
        │   │   ├── bedrock_handler.py
        │   │   ├── bedrock_lambda.py
        │   │   ├── requirements.txt
        │   │   └── template.yaml 
        │   ├── gemini_llm/
        │   │   ├── gemini_lambda.py
        │   │   ├── gemini_handler.py
        │   │   ├── requirements.txt
        │   │   └── template.yaml 
        │   └── openai_llm/
        │       ├── openai_handler.py
        │       ├── openai_lambda.py
        │       ├── deepseek_handler.py
        │       ├── deepseek_lambda.py
        │       ├── requirements.txt
        │       └── template.yaml
        ├── tests/
        │   ├── conftest.py
        │   ├── test_claude_handler.py (unit tests for the Claude LLM handler)
        │   ├── test_openai_handler.py
        │   ├── test_gemini_handler.py
        │   ├── test_nova_handler.py
        │   ├── test_bedrock_handler.py
        │   ├── requirements-test.txt
        │   └── events/
        │       └── multiple-places-weather-event.json (example event for SAM local testing)
        ├── README.md (this file)
        └── template.yaml (for SAM) (optional)
```

## Building the LLM caller

The LLM caller is implemented using a Lambda function. It calls the LLM API, with the tools option ("function calling"), and returns the LLM response.

- [Claude](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) models from Anthropic.
- [GPT](https://platform.openai.com/docs/guides/function-calling) models from OpenAI.
- [Jamba](https://docs.ai21.com/reference/jamba-15-api-ref) models from AI21, through [AWS Bedrock InvokeModel API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModel.html#API_runtime_InvokeModel_RequestBody).
- [Gemini](https://gemini.google.com/) models from Google.
- [Nova](https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova.html) models from Amazon.
- [DeepSeek](https://platform.deepseek.com/) models from DeepSeek. (Note: DeepSeek does not support function calling yet [Issue](https://github.com/deepseek-ai/DeepSeek-V3/issues/15).)

However, the tool usage is very similar to other LLM, such as FAIR [Llama](https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/prompt_format.md#json-based-tool-calling), and others.

## LLM Interface

The LLM interface is defined in the [`base_llm.py`](lambda/call_llm/common/base_llm.py) file. The interface defines the following methods:

- `prepare_messages`: Prepare messages for the specific LLM format.
- `generate_response`: Generates a response from the LLM given a list of messages and the history of the conversation.
- `convert_to_json`: Convert LLM response to standardized JSON format to be used by the agent state machine.

## Lambda Handler Flow

The Lambda function for calling the LLM receives an event with the input as a JSON object, and return the output as a JSON object.

```python
def lambda_handler(event, context):
    try:
        system = event.get('system')
        messages = event.get('messages', [])
        tools = event.get('tools', [])
        
        llm = ClaudeLLM()
        assistant_message = llm.generate_response(system, messages, tools)
        
        # Update messages with assistant's response
        messages.append(assistant_message["message"])
        
        return {
            'statusCode': 200,
            'body': {
                'messages': messages,
                'metadata': assistant_message["metadata"]
            }
        }
    except Exception as e:
        logger.error(e)
        raise e # Raise the exception to trigger a retry
```

## API Key

The API key for the LLM is stored in AWS Secrets Manager.

The following code snippet is implemented in the LLM implementation class and shows how to initialize the API key.

```python
class ClaudeLLM(BaseLLM):
    def __init__(self):
        api_keys = get_api_keys()
        self.client = anthropic.Anthropic(api_key=api_keys["ANTHROPIC_API_KEY"])
```

## Testing

### Unit Tests

Add a test file to the `tests` folder. The test file should contain the unit tests for the LLM handler.

```python
# tests/test_claude_handler.py
import json
import pytest
from handlers.claude_lambda import lambda_handler

@pytest.fixture
def claude_event():
    return {
        "system": "You are a helpful AI assistant.",
        "messages": [
            {
                "role": "user",
                "content": "What is 2+2?"
            }
        ],
        "tools": [
            {
                "name": "calculator",
                "description": "Use the calculator for mathematical operations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        ]
    }

def test_claude_handler(claude_event):
    # Test the handler
    response = lambda_handler(claude_event, None)
    
    # Assert response structure
    assert response["statusCode"] == 200
    assert "messages" in response["body"]
    assert "metadata" in response["body"]
    
    # Assert response content
    messages = response["body"]["messages"]
    assert len(messages) > 1  # Original message plus response
    assert messages[-1]["role"] == "assistant"  # Last message should be from assistant
```

To run the unit tests, you can use the following command:

```bash
pytest tests/
```

### Testing using SAM CLI

1. Add a to the `template.yaml` file to define the Lambda function.

    ```yaml
    ...
    OpenAILambda:
        Type: AWS::Serverless::Function
        Properties:
        CodeUri: lambda/call_llm
        Handler: handlers.openai_lambda.lambda_handler
        Runtime: python3.12
        Timeout: 90
        MemorySize: 256
        Environment:
            Variables:
            POWERTOOLS_SERVICE_NAME: openai-llm
        Architectures:
            - arm64
        Policies:
            - SecretsManagerReadWrite
            - AWSLambdaBasicExecutionRole
    ```

1. Add a test event to the `tests/events` folder.

    ```json
    {
    "messages": [
        {"role": "user", "content": "Do I need a jacket for today in Boston, MA?"}
    ],
    "tools": [
        {
          "name": "get_current_weather",
          "description": "Get the current weather in a given location",
          "input_schema": {
              "type": "object",
              "properties": {
                  "location": {
                      "type": "string",
                      "description": "The city and state, e.g. San Francisco, CA."
                  }
              },
              "required": ["location"]
          }
      },
      ...
    ]
    }
    ```

1. To test the Lambda function locally, you can use the following command:

    ```bash
    cd lambda/call_llm/functions/openai
    sam build && sam local invoke OpenAILambda -e tests/events/multiple-places-weather-event.json
    ```

## Deployment

Using CDK:

```python
        # Creating the Call LLM lambda function for Claude only 
        call_llm_lambda_function_claude = _lambda_python.PythonFunction(
            self, "CallLLMLambdaClaude",
            function_name="CallClaudeLLM", 
            description="Lambda function to Call LLM (Anthropic) with messages history and tools.",
            entry="lambda/call_llm/functions/anthropic",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=256,
            index="claude_lambda.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            role=call_llm_lambda_role,
            tracing= _lambda.Tracing.ACTIVE,
        )
```
