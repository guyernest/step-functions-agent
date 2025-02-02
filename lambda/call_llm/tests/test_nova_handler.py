# tests/test_nova_handler.py
import pytest

from functions.bedrock_llm.nova_lambda import lambda_handler

@pytest.fixture
def input_event():
    return {
        "system": "You are a helpful AI assistant with a set of tools to answer user questions. Please call the tools in parallel to reduce latency.",
        "messages": [
            {
                "role": "user",
                "content": "What is the weather like in Boston, MA and in Seattle, WA?"
            }
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
            {
                "name": "get_current_UTC_time",
                "description": "Get the current time in UTC timezone",
                "input_schema": {
                    "type": "object",
                    "properties": {} # No input required
                }
            }
        ]
    }

def test_lambda_handler(input_event):
    # Test the handler
    response = lambda_handler(input_event, None)
    
    # Assert response structure
    assert response["statusCode"] == 200
    assert "messages" in response["body"]
    assert "metadata" in response["body"]
    
    # Assert response content
    messages = response["body"]["messages"]
    assert len(messages) > 1  # Original message plus response
    last_message = messages[-1]  # Last message should be from assistant
    assert last_message["role"] == "assistant"  # Last message should be from assistant
    assert "content" in messages[-1]
    # Check the the content includes two calls with type "tool_use"
    assert len(last_message["content"]) > 0
    assert "toolUse" in last_message["content"][-1] 
    assert "toolUse" in last_message["content"][-2] 

    # Test the metadata
    metadata = response["body"]["metadata"]
    assert "usage" in metadata
    assert "stop_reason" in metadata
    usage = metadata["usage"]
    assert "input_tokens" in usage
    assert "output_tokens" in usage

    # Test the tool/function call output
    function_calls = response["body"]["function_calls"]
    assert len(function_calls) > 0
    assert function_calls[0]["name"] == "get_current_weather"

    # populate the tool response
    tool_response = {
        "role": "user",
        "content": [] 
    }
    for function_call in function_calls:
        tool_response["content"].append({
            "type": "tool_result",
            "name": function_call["name"],
            "tool_use_id": function_call["id"],
            "content": f"The weather in {function_call['input']['location']} is sunny.",
        }
    )

    # Test the tool result messages
    input_event["messages"].append(tool_response)
    print(input_event)
    response = lambda_handler(input_event, None)
    
    assert response["statusCode"] == 200
    assert "messages" in response["body"]
    assert "metadata" in response["body"]

    messages = response["body"]["messages"]
    assert len(messages) > 1
    last_message = messages[-1]

    assert last_message["role"] == "assistant"
    assert "content" in last_message
    assert "sunny" in last_message["content"][0]['text'].lower()
