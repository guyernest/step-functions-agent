import pytest

from index import lambda_handler

@pytest.fixture
def input_event():
    return {
        "id": "uniquetooluseid",
        "input": {
            "{{cookiecutter.input_param_name}}": "{{cookiecutter.test_input}}"
        },
        "name": "{{cookiecutter.tool_name}}",
        "type": "tool_use"
    }


def test_lambda_handler(input_event):
    # Test the handler
    response = lambda_handler(input_event, None)
    
    # Assert response structure
    assert response["type"] == "tool_result"
    assert response["tool_use_id"] == "uniquetooluseid"
    assert "content" in response


