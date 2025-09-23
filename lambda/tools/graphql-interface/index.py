# This lambda function will be used as a tool to query GraphQL endpoints
# It is part of the AI Agent platform on top of Step Functions
# Supports multiple GraphQL endpoints through dynamic selection

# Imports for GraphQL
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from graphql import print_schema

# Imports for Lambda
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer

import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

# Initialize the logger and tracer first
logger = Logger(level="INFO")
tracer = Tracer()

# Add the shared helper path
sys.path.insert(0, '/opt/python')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared/tool-secrets-helper'))

# Import boto3 for direct secret access
import boto3

# Initialize secrets manager client
secretsmanager = boto3.client('secretsmanager')

# Cache for secrets
_cached_secrets = None

def get_tool_secrets(tool_name: str) -> Dict[str, Any]:
    """Get secrets for the GraphQL tool from consolidated secret."""
    global _cached_secrets

    if _cached_secrets is not None:
        return _cached_secrets.get(tool_name, {})

    try:
        # Get consolidated secret
        env_name = os.environ.get('ENVIRONMENT', 'prod')
        secret_name = os.environ.get('CONSOLIDATED_SECRET_NAME', f'/ai-agent/tool-secrets/{env_name}')

        response = secretsmanager.get_secret_value(SecretId=secret_name)
        all_secrets = json.loads(response['SecretString'])
        _cached_secrets = all_secrets

        return all_secrets.get(tool_name, {})
    except Exception as e:
        logger.error(f"Error retrieving consolidated secrets: {e}")
        return {}

class GraphQLClient:
    def __init__(self, endpoint: str, api_key: str = None, headers: Dict[str, str] = None):
        """Initialize GraphQL client with endpoint and authentication.

        Args:
            endpoint: GraphQL endpoint URL
            api_key: API key for authentication (optional)
            headers: Additional headers to include (optional)
        """
        self.endpoint = endpoint

        # Build headers
        transport_headers = {'Content-Type': 'application/json'}
        if api_key:
            transport_headers['x-api-key'] = api_key
        if headers:
            transport_headers.update(headers)

        self.transport = AIOHTTPTransport(
            url=endpoint,
            headers=transport_headers,
        )
        self.client = Client(transport=self.transport, fetch_schema_from_transport=True)
        
    async def get_schema(self) -> str:
        """Fetch and return the GraphQL schema as a string"""
        async with self.client as session:
            schema = session.client.schema
            return print_schema(schema)
            
    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query and return the results"""
        async with self.client as session:
            result = await session.execute(gql(query), variable_values=variables)
            return result

# Global cache for GraphQL clients
_graphql_clients: Dict[str, GraphQLClient] = {}

def get_graphql_client(graphql_id: str) -> GraphQLClient:
    """Get or create a GraphQL client for the specified ID.

    Args:
        graphql_id: Identifier for the GraphQL endpoint (e.g., 'LogisticZ')

    Returns:
        GraphQLClient instance configured for the endpoint

    Raises:
        ValueError: If the graphql_id is not found in secrets
    """
    # Check cache first
    if graphql_id in _graphql_clients:
        return _graphql_clients[graphql_id]

    # Get all GraphQL configurations from tool secrets
    tool_secrets = get_tool_secrets('graphql-interface')

    logger.info(f"Retrieved tool secrets keys: {list(tool_secrets.keys()) if tool_secrets else 'None'}")

    if not tool_secrets or graphql_id not in tool_secrets:
        raise ValueError(f"GraphQL configuration not found for ID: {graphql_id}. Available IDs: {list(tool_secrets.keys()) if tool_secrets else 'None'}")

    config = tool_secrets[graphql_id]

    # Handle both dictionary and JSON string formats
    if isinstance(config, str):
        try:
            config = json.loads(config)
            logger.info(f"Parsed config for {graphql_id}: endpoint={config.get('endpoint', 'N/A')}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid configuration format for {graphql_id}")

    endpoint = config.get('endpoint')
    api_key = config.get('api_key')
    headers = config.get('headers', {})

    if not endpoint:
        raise ValueError(f"Endpoint not configured for GraphQL ID: {graphql_id}. Config: {config}")

    # Create and cache the client
    client = GraphQLClient(endpoint, api_key, headers)
    _graphql_clients[graphql_id] = client

    logger.info(f"Created GraphQL client for {graphql_id} at {endpoint}")
    return client

def get_graphql_schema(graphql_id: str) -> str:
    """Fetch the GraphQL schema for a specific endpoint.

    Args:
        graphql_id: Identifier for the GraphQL endpoint

    Returns:
        The GraphQL schema as a string, or error message
    """
    try:
        client = get_graphql_client(graphql_id)
        schema = asyncio.run(client.get_schema())
        return f"Successfully fetched schema for {graphql_id}:\n\n{schema}"
    except Exception as e:
        logger.error(f"Error fetching schema for {graphql_id}: {str(e)}")
        return f"Error fetching schema for {graphql_id}: {str(e)}"

# Function to generate instruction to generate a GraphQL query based on the schema and user description
def generate_query_prompt(graphql_id: str, description: str) -> str:
    """Generate a GraphQL query based on the schema and user description.

    Args:
        graphql_id: Identifier for the GraphQL endpoint
        description: Description of what query to generate

    Returns:
        Prompt for generating the GraphQL query
    """
    try:
        client = get_graphql_client(graphql_id)
        schema = asyncio.run(client.get_schema())
        
        # Provide context about the schema and request to help generate the query
        prompt = f"""Given this GraphQL schema:

{schema}

Generate a GraphQL query that: {description}.

Please note that the GraphQL API is designed to answer policy questions for a specific organization.
The quesions of the users related to a speicific state where they are located or want to go. 
When you generate a GraphQL query, the query should be focused on the state, and therefore use the state query, with the short code of the state as the id (for example: "id": "NY", for New York).
When you ask for policies, don't filter by their names, as you don't know them yet. Once you get the policies, you can filter by their names.
Please note that you should also request the policy holder of the policies, and then check for their type. 
The policies are organized in an hierarchy, where lower levels override higher levels (for example: a policy of a state can override a policy of a country).
For example, here is a query to get all the policies of a state:
```graphql
query sampleStateQuery {{
  state(id: "NY") {{
    state_name
    policies {{
      policy_type
      policy_document
      policy_holder {{
        __typename
      }}
    }}
  }}
}}
```
Return only the GraphQL query without any explanation."""
        
        return prompt
    except Exception as e:
        return f"Error generating query: {str(e)}"

# Function to execute the GraphQL query
def execute_graphql(graphql_id: str, query: str, variables: Optional[str] = None) -> str:
    """Execute a GraphQL query against a specific endpoint.

    Args:
        graphql_id: Identifier for the GraphQL endpoint
        query: The GraphQL query string to execute
        variables: JSON string containing variables for the query (optional)

    Returns:
        JSON string containing the query results with indentation,
        or an error message if the execution fails.
    """
    try:
        client = get_graphql_client(graphql_id)
        vars_dict = json.loads(variables) if variables else None
        result = asyncio.run(client.execute_query(query, vars_dict))
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error executing query for {graphql_id}: {str(e)}")
        return f"Error executing query: {str(e)}"


@tracer.capture_method
def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use['name']
    tool_input = tool_use['input']

    logger.info(f"Tool name: {tool_name}")
    logger.info(f"Tool input: {json.dumps(tool_input)}")

    if tool_name == 'get_graphql_schema':
        # Fetch the schema for a specific GraphQL endpoint
        graphql_id = tool_input.get('graphql_id')
        if not graphql_id:
            result = json.dumps({
                'error': 'graphql_id parameter is required'
            })
        else:
            result = get_graphql_schema(graphql_id)

    elif tool_name == 'generate_query_prompt':
        # Generate a query prompt with schema awareness
        graphql_id = tool_input.get('graphql_id')
        description = tool_input.get('description')
        if not graphql_id:
            result = json.dumps({
                'error': 'graphql_id parameter is required'
            })
        elif not description:
            result = json.dumps({
                'error': 'description parameter is required'
            })
        else:
            result = generate_query_prompt(graphql_id, description)

    elif tool_name == 'execute_graphql_query':
        # Execute a GraphQL query against a specific endpoint
        graphql_id = tool_input.get('graphql_id')
        query = tool_input.get('graphql_query', tool_input.get('query'))  # Support both field names
        variables = tool_input.get('variables')

        if not graphql_id:
            result = json.dumps({
                'error': 'graphql_id parameter is required'
            })
        elif not query:
            result = json.dumps({
                'error': 'graphql_query parameter is required'
            })
        else:
            try:
                # Convert variables to JSON string if it's a dict
                if variables and isinstance(variables, dict):
                    variables = json.dumps(variables)
                result = execute_graphql(graphql_id, query, variables)
            except Exception as e:
                result = json.dumps({
                    'error': str(e)
                })

    else:
        result = json.dumps({
            'error': f"Unknown tool name: {tool_name}"
        })

    return {
        "type": "tool_result",
        "name": tool_name,
        "tool_use_id": tool_use["id"],
        "content": result
    }