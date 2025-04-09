import pytest

from index import lambda_handler

@pytest.fixture
def get_event():
    return {
        "id": "uniquetooluseid",
        "input": {
            "endpoint": "users",
            "method": "GET"
        },
        "name": "MicrosoftGraphAPI",
        "type": "tool_use"
    }

@pytest.fixture
def post_event():
    return {
        "id": "uniquetooluseid",
        "input": {
            "endpoint": "me/sendMail",
            "method": "POST",
            "data": {
                "message": {
                    "subject": "Test email",
                    "body": {
                        "contentType": "HTML",
                        "content": "<p>This is a test email.</p>"
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": "test@example.com"
                            }
                        }
                    ]
                },
                "saveToSentItems": True
            }
        },
        "name": "MicrosoftGraphAPI",
        "type": "tool_use"
    }

@pytest.fixture
def legacy_event():
    return {
        "id": "uniquetooluseid",
        "input": {
            "query": "users"
        },
        "name": "MicrosoftGraphAPI",
        "type": "tool_use"
    }


def test_get_request(get_event):
    # Test the handler with GET request
    response = lambda_handler(get_event, None)
    
    # Assert response structure
    assert response["type"] == "tool_result"
    assert response["tool_use_id"] == "uniquetooluseid"
    assert "content" in response
    assert "Error" not in response["content"]

def test_legacy_request(legacy_event):
    # Test the handler with legacy format
    response = lambda_handler(legacy_event, None)
    
    # Assert response structure
    assert response["type"] == "tool_result"
    assert response["tool_use_id"] == "uniquetooluseid"
    assert "content" in response
    assert "Error" not in response["content"]

