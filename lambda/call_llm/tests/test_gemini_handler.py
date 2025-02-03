import pytest

from functions.gemini_llm.gemini_lambda import lambda_handler

@pytest.fixture
def input_event():
    return {
        "system": "You are a helpful AI assistant.",
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

@pytest.fixture
def tool_response():
    return {
        "role": "user", 
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_011NmrpmP4ucmWP6x1YMR2dM",
                "name" : "get_current_weather",
                "content" : {
                    "result" : "Sunny with a high of 70°F."
                }
            },
            {
                "type": "tool_result",
                "tool_use_id": "toolu_011NmrpmP4ucmWP6x1YMR2dM",
                "name" : "get_current_weather",
                "content" : {
                    "result" : "Clear with a low of 31°F."
                }
            }
        ]
    }



def test_lambda_handler(input_event, tool_response):
    
    # Test the initial prompt and tool call output
    response = lambda_handler(input_event, None)
    
    assert response["statusCode"] == 200
    assert "messages" in response["body"]
    assert "metadata" in response["body"]
    
    # Test the internal message format of the LLM
    messages = response["body"]["messages"]
    assert len(messages) > 1
    assert messages[-1]["role"] == "model"
    assert "function_call" in messages[-1]["parts"][0]
    assert messages[-1]["parts"][0]["function_call"]["name"] == "get_current_weather"

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

    # Test the tool result messages
    input_event["messages"].append(tool_response)
    response = lambda_handler(input_event, None)
    
    assert response["statusCode"] == 200
    assert "messages" in response["body"]
    assert "metadata" in response["body"]

    messages = response["body"]["messages"]
    assert len(messages) > 1
    assert messages[-1]["role"] == "model"
    assert "function_call" not in messages[-1]["parts"][0]
    assert "text" in messages[-1]["parts"][0]
    assert "sunny" in messages[-1]["parts"][0]["text"].lower()
