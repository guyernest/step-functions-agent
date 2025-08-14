# This lambda function will be used as a tool MicrosoftGraphAPI for the AI Agent platform

# Imports for Tool
import requests
import json
import base64
from typing import Optional

# Imports for Lambda
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from tool_secrets import get_tool_secrets, get_legacy_secret

# Initialize the logger and tracer
logger = Logger(service="MicrosoftGraphAPI")
tracer = Tracer()

def mask_secret(value: str, name: str = "secret") -> str:
    """Safely mask secret values for logging"""
    if not value:
        return f"{name}_NOT_SET"
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"

# Reading the secrets from the AWS Secrets Manager
# Initialize these with your values from Azure AD

# Try consolidated secret first, then fall back to legacy
try:
    logger.debug("Starting credential retrieval process")
    keys = get_tool_secrets('microsoft-graph')
    
    logger.debug("Checking consolidated secret", 
                 extra={
                     "source": "consolidated",
                     "has_keys": bool(keys),
                     "keys_present": list(keys.keys()) if keys else []
                 })
    
    if keys and all(k in keys for k in ['TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET']):
        tenant_id = keys["TENANT_ID"].strip()
        client_id = keys["CLIENT_ID"].strip()
        client_secret = keys["CLIENT_SECRET"].strip()
        logger.info("Microsoft Graph credentials retrieved successfully",
                   extra={
                       "source": "consolidated",
                       "tenant_id_preview": mask_secret(tenant_id, "tenant"),
                       "client_id_preview": mask_secret(client_id, "client"),
                       "has_client_secret": bool(client_secret)
                   })
    else:
        # Fall back to legacy secret
        logger.info("Consolidated secret incomplete, trying legacy sources",
                   extra={"missing_keys": [k for k in ['TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET'] 
                                          if not keys or k not in keys]})
        
        keys = get_legacy_secret("/ai-agent/MicrosoftGraphAPISecrets")
        if not keys:
            logger.debug("First legacy path failed, trying alternate path")
            keys = get_legacy_secret("/ai-agent/tools/microsoft-graph/prod")
        
        tenant_id = keys["TENANT_ID"].strip()
        client_id = keys["CLIENT_ID"].strip()
        client_secret = keys["CLIENT_SECRET"].strip()
        logger.info("Microsoft Graph credentials retrieved from legacy secret",
                   extra={
                       "source": "legacy",
                       "tenant_id_preview": mask_secret(tenant_id, "tenant"),
                       "client_id_preview": mask_secret(client_id, "client")
                   })
except Exception as e:
    logger.error("Failed to retrieve Microsoft Graph credentials",
                extra={"error": str(e), "error_type": type(e).__name__})
    raise
# Define the GraphAPIClient class

class GraphAPIClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token: Optional[str] = None
        
    @tracer.capture_method
    def get_token(self) -> str:
        """Get access token using client credentials flow"""
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        logger.debug("Requesting access token",
                    extra={
                        "token_url": token_url,
                        "tenant_id": mask_secret(self.tenant_id, "tenant"),
                        "client_id": mask_secret(self.client_id, "client")
                    })
        
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        try:
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            
            token_response = response.json()
            self.token = token_response.get('access_token')
            
            # Decode token to inspect claims (only for debugging)
            token_claims = None
            if self.token and logger.level <= 10:  # DEBUG level is 10
                try:
                    # JWT tokens have 3 parts separated by dots
                    parts = self.token.split('.')
                    if len(parts) >= 2:
                        # Decode the payload (second part)
                        payload = parts[1]
                        # Add padding if needed
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.b64decode(payload)
                        token_claims = json.loads(decoded)
                        
                        logger.debug("Token claims decoded",
                                   extra={
                                       "scopes": token_claims.get('scp', 'Not found'),
                                       "roles": token_claims.get('roles', 'Not found'),
                                       "app_id": token_claims.get('appid', 'Not found'),
                                       "tenant_id": token_claims.get('tid', 'Not found'),
                                       "audience": token_claims.get('aud', 'Not found')
                                   })
                except Exception as decode_error:
                    logger.debug("Failed to decode token claims", 
                               extra={"error": str(decode_error)})
            
            logger.info("Access token obtained successfully",
                       extra={
                           "token_preview": mask_secret(self.token, "token") if self.token else "NO_TOKEN",
                           "expires_in": token_response.get('expires_in'),
                           "token_type": token_response.get('token_type')
                       })
            return self.token
            
        except requests.exceptions.HTTPError as e:
            logger.error("Failed to obtain access token",
                        extra={
                            "status_code": e.response.status_code if e.response else None,
                            "error_body": e.response.text if e.response else None,
                            "error": str(e)
                        })
            raise

    @tracer.capture_method
    def call_graph_api(self, endpoint: str, method: str = 'GET', data: dict = None) -> dict:
        """Make a call to Microsoft Graph API"""
        if not self.token:
            logger.debug("No token available, requesting new token")
            self.get_token()
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://graph.microsoft.com/v1.0/{endpoint}'
        
        logger.info(f"Calling Microsoft Graph API",
                   extra={
                       "endpoint": endpoint,
                       "method": method,
                       "url": url,
                       "has_data": bool(data)
                   })
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None
            )
            response.raise_for_status()
            
            result = response.json() if response.text else {}
            logger.info("Graph API call successful",
                       extra={
                           "status_code": response.status_code,
                           "response_size": len(response.text) if response.text else 0
                       })
            return result
            
        except requests.exceptions.HTTPError as e:
            error_detail = None
            if e.response:
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text
            
            logger.error("Graph API call failed",
                        extra={
                            "status_code": e.response.status_code if e.response else None,
                            "error_body": error_detail,
                            "endpoint": endpoint,
                            "method": method,
                            "url": url,
                            "headers_sent": {k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}
                        })
            raise

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
        
        # Log output summary without exposing sensitive data
        logger.debug("API call completed",
                    extra={
                        "has_output": bool(output),
                        "output_type": type(output).__name__,
                        "output_keys": list(output.keys()) if isinstance(output, dict) else None
                    })
        
        result = output
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing Graph API request: {str(e)}"


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    # Support dynamic log level from event
    if "_debug" in event and "log_level" in event["_debug"]:
        log_level = event["_debug"]["log_level"].upper()
        logger.setLevel(log_level)
        logger.info(f"Log level set to {log_level}")
    
    # Extract test mode flag
    test_mode = event.get("_test_mode", False)
    
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use.get('name', '')
    tool_input = tool_use.get('input', {})
    
    # Add request context to all logs
    logger.append_keys(
        tool_name=tool_name,
        request_id=context.aws_request_id if context else "local-test",
        test_mode=test_mode
    )

    logger.info("Tool execution started",
               extra={"tool_name": tool_name, "has_input": bool(tool_input)})
    
    match tool_name:
        case 'MicrosoftGraphAPI':
            endpoint = tool_input.get('endpoint', tool_input.get('query', ''))
            method = tool_input.get('method', 'GET')
            data = tool_input.get('data')
            
            logger.debug("Processing MicrosoftGraphAPI request",
                        extra={"endpoint": endpoint, "method": method, "has_data": bool(data)})
            
            result = MicrosoftGraphAPI(endpoint, method, data)
            
            logger.info("Tool execution completed successfully",
                       extra={"result_size": len(result) if result else 0})

        # Add more tools functions here as needed

        case _:
            logger.error(f"Unknown tool name received", extra={"tool_name": tool_name})
            result = json.dumps({
                'error': f"Unknown tool name: {tool_name}"
            })

    # Include logs in response if in test mode
    response = {
        "type": "tool_result",
        "name": tool_name,
        "tool_use_id": tool_use.get("id", ""),
        "content": result
    }
    
    # Add debug info if in test mode
    if test_mode:
        response["_debug"] = {
            "log_level": logger.level,
            "request_id": context.aws_request_id if context else "local-test"
        }
    
    return response

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
