# This lambda function will be used as a tool MicrosoftGraphAPI for the AI Agent platform

# Imports for Tool
import requests
import json
from typing import Optional

# Imports for Lambda
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities import parameters

# Initialize the logger and tracer
logger = Logger(level="INFO")
tracer = Tracer()

# Reading the secrets from the AWS Secrets Manager
# Initialize these with your values from Azure AD

keys = json.loads(parameters.get_secret("/ai-agent/MicrosoftGraphAPISecrets"))
tenant_id = keys["TENANT_ID"]
client_id = keys["CLIENT_ID"]
client_secret = keys["CLIENT_SECRET"]
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
            # json=data
        )
        response.raise_for_status()
        return response.json()

# Tool Functions
def MicrosoftGraphAPI(
    query: str
    ) -> str:
    """Interface to the Microsoft Graph API of a specific tenant..
    Args:
        query (str): The API query to perform.

    Returns:
        str: Interface to the Microsoft Graph API of a specific tenant.,
             or an error message if the execution fails.

    Raises:
        Exception: Any exception during query execution will be caught and returned as an error message.
    """

    try:
        # Initialize the Graph API client
        client = GraphAPIClient(tenant_id, client_id, client_secret)
        
        # Example: List users
        output = client.call_graph_api(query)
        logger.info(f"Output: {output}")
        result = output
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing query: {str(e)}"


@tracer.capture_method
def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use['name']
    tool_input = tool_use['input']

    logger.info(f"Tool name: {tool_name}")
    match tool_name:
        case 'MicrosoftGraphAPI':
            result = MicrosoftGraphAPI(tool_input['query'])

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
    
    # Test event for MicrosoftGraphAPI
    test_event = {
        "name": "MicrosoftGraphAPI",
        "id": "execute_unique_id",
        "input": {
            "query": "users"
        },
        "type": "tool_use"
    }
    
    # Call lambda handler with test events
    print("\nTesting MicrosoftGraphAPI:")
    response = lambda_handler(test_event, None)
    print(response)
