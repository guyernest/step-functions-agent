# This lambda function will be used as a tool MicrosoftGraphAPI for the AI Agent platform

# Imports for Tool
import requests
import json
from typing import Optional

# Imports for Lambda
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from tool_secrets import get_tool_secrets, get_legacy_secret

# Initialize the logger and tracer
logger = Logger(level="INFO")
tracer = Tracer()

# Reading the secrets from the AWS Secrets Manager
# Initialize these with your values from Azure AD

# Try consolidated secret first, then fall back to legacy
try:
    logger.info("Retrieving Microsoft Graph credentials from consolidated tool secrets")
    keys = get_tool_secrets('microsoft-graph')
    
    if keys and all(k in keys for k in ['TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET']):
        tenant_id = keys["TENANT_ID"]
        client_id = keys["CLIENT_ID"]
        client_secret = keys["CLIENT_SECRET"]
        logger.info("Microsoft Graph credentials retrieved from consolidated secret")
    else:
        # Fall back to legacy secret
        logger.info("Falling back to legacy secret")
        keys = get_legacy_secret("/ai-agent/MicrosoftGraphAPISecrets")
        if not keys:
            keys = get_legacy_secret("/ai-agent/tools/microsoft-graph/prod")
        tenant_id = keys["TENANT_ID"]
        client_id = keys["CLIENT_ID"]
        client_secret = keys["CLIENT_SECRET"]
        logger.info("Microsoft Graph credentials retrieved from legacy secret")
except Exception as e:
    logger.error(f"Failed to retrieve Microsoft Graph credentials: {e}")
    raise
# Define the GraphAPIClient class

class GraphAPIClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token: Optional[str] = None
        
    def get_token(self) -> str:
        """Get access token using client credentials flow"""
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        
        self.token = response.json()['access_token']
        logger.info(f"Token: {self.token}")
        return self.token

    def call_graph_api(self, endpoint: str, method: str = 'GET', data: dict = None) -> dict:
        """Make a call to Microsoft Graph API"""
        if not self.token:
            self.get_token()
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://graph.microsoft.com/v1.0/{endpoint}'
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if data else None
        )
        response.raise_for_status()
        return response.json()

# Tool Functions
def MicrosoftGraphAPI(
    endpoint: str,
    method: str = "GET",
    data: dict = None
    ) -> str:
    """Interface to the Microsoft Graph API of a specific tenant.
    Args:
        endpoint (str): The Graph API endpoint to call (e.g. 'users', 'me/sendMail').
        method (str, optional): HTTP method to use (GET, POST, etc.). Defaults to GET.
        data (dict, optional): The data payload for POST/PUT/PATCH requests.

    Returns:
        str: Response from the Microsoft Graph API, or an error message if execution fails.

    Raises:
        Exception: Any exception during API execution will be caught and returned as an error message.
    """

    try:
        # Initialize the Graph API client
        client = GraphAPIClient(tenant_id, client_id, client_secret)
        
        # Call the Microsoft Graph API
        output = client.call_graph_api(endpoint, method=method, data=data)
        logger.info(f"Output: {output}")
        result = output
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing Graph API request: {str(e)}"


@tracer.capture_method
def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use['name']
    tool_input = tool_use['input']

    logger.info(f"Tool name: {tool_name}")
    match tool_name:
        case 'MicrosoftGraphAPI':
            endpoint = tool_input.get('endpoint', tool_input.get('query', ''))
            method = tool_input.get('method', 'GET')
            data = tool_input.get('data')
            
            result = MicrosoftGraphAPI(endpoint, method, data)

        # Add more tools functions here as needed

        case _:
            result = json.dumps({
                'error': f"Unknown tool name: {tool_name}"
            })

    return {
        "type": "tool_result",
        "name": tool_name,
        "tool_use_id": tool_use["id"],
        "content": result
    }

if __name__ == "__main__":
    
    # Test event for MicrosoftGraphAPI - GET request
    test_get_event = {
        "name": "MicrosoftGraphAPI",
        "id": "execute_unique_id",
        "input": {
            "endpoint": "users",
            "method": "GET"
        },
        "type": "tool_use"
    }
    
    # Test event for MicrosoftGraphAPI - POST request (email sending)
    test_email_event = {
        "name": "MicrosoftGraphAPI",
        "id": "execute_unique_id",
        "input": {
            "endpoint": "me/sendMail",
            "method": "POST",
            "data": {
                "message": {
                    "subject": "Test email from Graph API Tool",
                    "body": {
                        "contentType": "HTML",
                        "content": "<p>This is a test email sent via Microsoft Graph API.</p>"
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
        "type": "tool_use"
    }
    
    # Call lambda handler with GET test event
    print("\nTesting MicrosoftGraphAPI GET:")
    response = lambda_handler(test_get_event, None)
    print(response)
    
    # Call lambda handler with email test event
    print("\nTesting MicrosoftGraphAPI Email Send:")
    # Uncomment the line below to actually test sending an email
    # response = lambda_handler(test_email_event, None)
    # print(response)
