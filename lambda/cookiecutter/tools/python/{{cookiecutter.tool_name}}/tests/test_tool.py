import pytest

from index import lambda_handler

{% for name in cookiecutter.tool_functions.functions_names %}

@pytest.fixture
def input_event_{{ name }}():
    return {
        "id": "uniquetooluseid",
        "input": {
            "{{cookiecutter.input_param_name}}": "{{cookiecutter.input_test_value}}"
        },
        "name": "{{name}}",
        "type": "tool_use"
    }


def test_lambda_handler_{{ name }}(input_event_{{ name }}):
    # Test the handler
    response = lambda_handler(input_event_{{ name }}, None)
    
    # Assert response structure
    assert response["type"] == "tool_result"
    assert response["tool_use_id"] == "uniquetooluseid"
    assert "content" in response

{% endfor %}

