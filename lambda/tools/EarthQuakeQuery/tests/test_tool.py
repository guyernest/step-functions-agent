import pytest

from index import lambda_handler

@pytest.fixture
def input_event():
    return {
        "id": "uniquetooluseid",
        "input": {
            "start_date": "2024-01-01"
        },
        "name": "EarthQuakeQuery",
        "type": "tool_use"
    }


def test_lambda_handler(input_event):
    # Test the handler
    response = lambda_handler(input_event, None)
    
    # Assert response structure
    assert response["type"] == "tool_result"
    assert response["tool_use_id"] == "uniquetooluseid"
    assert "content" in response


