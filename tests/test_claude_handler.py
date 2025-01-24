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