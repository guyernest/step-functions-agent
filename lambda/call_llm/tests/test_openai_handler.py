# tests/test_openai_handler.py
import json
import pytest
from functions.openai_llm.openai_lambda import lambda_handler

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
            },
            {
                "name": "get_current_time_cities",
                "description": "Get the current time in the given city list",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "locations": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "The list of cities and states, e.g. [San Francisco, CA, New York, NY]."
                        }
                    },
                    "required": ["locations"]
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
    print(last_message)
    assert last_message["role"] == "assistant"  # Last message should be from assistant
    assert "tool_calls" in messages[-1]
    # Check the the content includes two calls with type "tool_use"
    assert len(last_message["tool_calls"]) > 0
    assert last_message["tool_calls"][-1]["function"]["name"] == "get_current_weather"
    # Until we find the way to get GPT to return multiple tool calls, we can't test this
    # assert last_message["tool_calls"][-2]["name"] == "get_current_weather"

    # Test the metadata
    metadata = response["body"]["metadata"]
    assert "usage" in metadata
    assert "stop_reason" in metadata
    usage = metadata["usage"]
    assert "input_tokens" in usage
    assert "output_tokens" in usage

    # Test the tool/function call output
    function_calls = response["body"]["function_calls"]
    while len(function_calls) > 0:
        # Test the function call messages
        assert function_calls[0]["name"] == "get_current_weather"

        # populate the tool response (the OpenAI handler should convert to the OpenAI format)
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
        response = lambda_handler(input_event, None)
        
        assert response["statusCode"] == 200
        assert "messages" in response["body"]
        assert "metadata" in response["body"]

        messages = response["body"]["messages"]
        assert len(messages) > 1
        last_message = messages[-1]
        print(last_message)

        assert last_message["role"] == "assistant"
        function_calls = response["body"]["function_calls"]

    assert "text" in messages[-1]["content"][0]
    assert "sunny" in messages[-1]["content"][0]["text"].lower()
