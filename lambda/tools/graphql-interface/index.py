# This lambda function will be used as a tooll to query a GraphQL endpoint
# It is part of the AI Agent platform on top of Step Functions

# Imports for GraphQL
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from graphql import print_schema

# Imports for Lambda
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities import parameters

import asyncio
import json
from typing import Any, Dict, Optional

# Initialize the logger and tracer
logger = Logger(level="INFO")
tracer = Tracer()

GRAPHQL_API_KEY = json.loads(parameters.get_secret("/ai-agent/graphql-tool/keys"))["GRAPHQL_API_KEY"]
GRAPHQL_ENDPOINT = parameters.get_parameter("/ai-agent/graphql-tool/graphql-endpoint")

class GraphQLClient:
    def __init__(self, endpoint: str):
        self.transport = AIOHTTPTransport(
            url=endpoint,
            headers={
                "x-api-key": GRAPHQL_API_KEY,
                'Content-Type': 'application/json',
            },
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

client = GraphQLClient(GRAPHQL_ENDPOINT)

def connect_graphql() -> str:
    """Connect to the GraphQL endpoint and fetch its schema"""
    try:
        schema = asyncio.run(client.get_schema())

        return f"Successfully connected to {GRAPHQL_ENDPOINT}. Schema loaded."
    except Exception as e:
        return f"Error connecting to GraphQL endpoint: {str(e)}"

# Function to generate instruction to generate a GraphQL query based on the schema and user description
def generate_query_prompt(description: str) -> str:
    """Generate a GraphQL query based on the schema and user description"""
    try:
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
def execute_graphql(query: str, variables: Optional[str] = None) -> str:
    """Execute a GraphQL query against the connected endpoint.
    Args:
        query (str): The GraphQL query string to execute.
        variables (Optional[str], optional): JSON string containing variables for the query. Defaults to None.

    Returns:
        str: JSON string containing the query results with indentation,
             or an error message if the execution fails.

    Raises:
        Exception: Any exception during query execution will be caught and returned as an error message.
    """
    try:
        vars_dict = json.loads(variables) if variables else None
        result = asyncio.run(client.execute_query(query, vars_dict))
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
        case 'generate_query_prompt':
            result = generate_query_prompt(tool_input['description'])
        case 'execute_graphql_query':
            # The SQL provided might cause ad error. We need to return the error message to the LLM
            # so it can fix the SQL and try again.
            try:
                result = execute_graphql(tool_input['graphql_query'])
            except Exception as e:
                result = json.dumps({
                    'error': str(e)
                })
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