import pytest

from index import lambda_handler

@pytest.fixture
def generate_prompt_input_event():
    return {
        "id": "uniquetooluseid",
        "input": {
            "description": "Can I ship wine from California to Washington?",
        },
        "name": "generate_query_prompt",
        "type": "tool_use"
    }

@pytest.fixture
def execute_graphql_query_input_event():
    return {
        "id": "uniquetooluseid",
        "input": {
            "graphql_query": "query test { organization { name } }"
        },
        "name": "execute_graphql_query",
        "type": "tool_use"
    }

def test_lambda_handler(generate_prompt_input_event, execute_graphql_query_input_event):
    # Test the handler
    response = lambda_handler(generate_prompt_input_event, None)
    
    # Assert response structure
    assert response["type"] == "tool_result"
    assert response["tool_use_id"] == "uniquetooluseid"
    assert "content" in response
    assert "Given" in response["content"]


    response = lambda_handler(execute_graphql_query_input_event, None)
    print(response)
    assert response["type"] == "tool_result"
    assert response["tool_use_id"] == "uniquetooluseid"
    assert "content" in response
    assert "organization" in response["content"]
