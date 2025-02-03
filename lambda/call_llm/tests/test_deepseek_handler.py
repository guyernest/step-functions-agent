import pytest

from functions.openai_llm.deepseek_lambda import lambda_handler

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
                    "properties": {}
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
    response = lambda_handler(input_event, None)
    print(response)

    assert response["statusCode"] == 200
    assert "messages" in response["body"]
    assert "metadata" in response["body"]
    
    messages = response["body"]["messages"]
    assert len(messages) > 1
    last_message = messages[-1]
    print(last_message)
    assert last_message["role"] == "assistant"
    assert "tool_calls" in messages[-1]
    assert len(last_message["tool_calls"]) > 0
    assert last_message["tool_calls"][-1]["function"]["name"] == "get_current_weather"

    metadata = response["body"]["metadata"]
    assert "usage" in metadata
    assert "stop_reason" in metadata
    usage = metadata["usage"]
    assert "input_tokens" in usage
    assert "output_tokens" in usage

    function_calls = response["body"]["function_calls"]
    while len(function_calls) > 0:
        assert function_calls[0]["name"] == "get_current_weather"

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
            })

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
