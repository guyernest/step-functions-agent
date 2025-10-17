#!/usr/bin/env python3
"""Nova Act Agent for Bedrock Agent Core runtime with real browser automation."""

import json
import os
from typing import Any, Dict

from bedrock_agentcore import BedrockAgentCoreApp
from nova_act_agent.base_agent import NovaActAgent, BroadbandCheckerAgent

# Initialize AgentCore app
app = BedrockAgentCoreApp()


@app.entrypoint
def agent_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """AWS Lambda handler for Agent Core with Nova Act integration.

    This agent handles browser automation tasks using Nova Act.
    It supports multiple agent types via the AGENT_TYPE environment variable:
    - broadband: UK broadband availability checking
    - shopping: E-commerce product search
    - search: General web search and extraction

    Args:
        event: Event from Agent Core (direct JSON payload)
        context: Lambda context

    Returns:
        Response dictionary (direct JSON)
    """
    try:
        # Hardcoded agent type for this entrypoint
        agent_type = "shopping"
        print(f"Processing request for agent type: {agent_type}")
        print(f"Event keys: {list(event.keys())}")
        print(f"Full event: {json.dumps(event)[:500]}")  # Log first 500 chars of event for debugging

        # Extract credentials if provided (check both top-level and nested in input)
        credentials = event.get("credentials", {})
        if not credentials and "input" in event:
            credentials = event.get("input", {}).get("credentials", {})

        # Log that we received credentials (without logging the actual values)
        if credentials:
            print(f"Received credentials for {agent_type} agent (fields: {list(credentials.keys())})")
        else:
            print(f"No credentials found in event for {agent_type} agent")

        # Route to appropriate handler based on agent type
        if agent_type == "broadband":
            result = handle_broadband_check(event, credentials)
        elif agent_type == "shopping":
            result = handle_shopping_search(event, credentials)
        elif agent_type == "search":
            result = handle_web_search(event, credentials)
        else:
            result = {
                "success": False,
                "error": f"Unknown agent type: {agent_type}"
            }

        print(f"Handler result: {json.dumps(result)[:200]}")
        return result

    except Exception as e:
        import traceback
        print(f"Error in handler: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process request"
        }


def handle_broadband_check(body: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle broadband availability checking using Nova Act.

    Args:
        body: Request body with input parameters
        credentials: Optional credentials for authenticated checks

    Returns:
        Response dictionary with broadband availability results
    """
    # Extract address from either direct format or nested input
    if "address" in body:
        address = body["address"]
    elif "input" in body:
        input_data = body.get("input", {})
        address = {
            "number": input_data.get("building_number", ""),
            "street": input_data.get("street", ""),
            "town": input_data.get("town", ""),
            "postcode": input_data.get("postcode", "")
        }
    else:
        # Try top-level fields
        address = {
            "number": body.get("building_number", ""),
            "street": body.get("street", ""),
            "town": body.get("town", ""),
            "postcode": body.get("postcode", "")
        }

    print(f"Checking broadband for address: {address}")

    try:
        # Set Nova Act API key from credentials if provided
        if credentials and "NOVA_ACT_API_KEY" in credentials:
            os.environ["NOVA_ACT_API_KEY"] = credentials["NOVA_ACT_API_KEY"]
            print("Nova Act API key configured from credentials")

        # Initialize the BroadbandCheckerAgent
        agent = BroadbandCheckerAgent()

        # Execute broadband check
        result = agent.check_broadband(address)

        print(f"Broadband check result: {json.dumps(result)[:300]}")

        # Transform to consistent format
        return {
            "success": result.get("success", False),
            "message": "Broadband check completed" if result.get("success") else "Broadband check failed",
            "data": {
                "address": address,
                "has_credentials": bool(credentials),
                "nova_act_response": result.get("response"),
                "extracted_data": result.get("extracted_data"),
                "broadband_info": result.get("broadband_info"),
                "session_id": result.get("session_id"),
                "error": result.get("error")
            }
        }
    except Exception as e:
        print(f"Error in broadband check: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to check broadband availability"
        }


def handle_shopping_search(body: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle e-commerce product search using Nova Act.

    Args:
        body: Request body with search query
        credentials: Optional credentials for authenticated searches

    Returns:
        Response dictionary with product search results
    """
    input_data = body.get("input", body)
    query = input_data.get("query", "")
    site = input_data.get("site", "amazon.co.uk")
    max_results = input_data.get("max_results", 10)

    print(f"Shopping search: query='{query}', site={site}, max_results={max_results}")

    try:
        # Set Nova Act API key from credentials if provided
        if credentials and "NOVA_ACT_API_KEY" in credentials:
            os.environ["NOVA_ACT_API_KEY"] = credentials["NOVA_ACT_API_KEY"]
            print("Nova Act API key configured from credentials")

        # Initialize the Nova Act agent
        agent = NovaActAgent()

        # Build task for shopping search
        task = {
            "url": f"https://www.{site}",
            "instructions": f"""
            1. Navigate to the search functionality
            2. Search for "{query}"
            3. Extract the top {max_results} product results including:
               - Product title
               - Price
               - Rating
               - Product URL
               - Availability
            """,
            "extract_data": ["title", "price", "rating", "url", "availability"]
        }

        result = agent.execute(task)

        print(f"Shopping search result: {json.dumps(result)[:300]}")

        return {
            "success": result.get("success", False),
            "message": "Shopping search completed" if result.get("success") else "Shopping search failed",
            "data": {
                "query": query,
                "site": site,
                "max_results": max_results,
                "has_credentials": bool(credentials),
                "nova_act_response": result.get("response"),
                "extracted_data": result.get("extracted_data"),
                "session_id": result.get("session_id"),
                "error": result.get("error")
            }
        }
    except Exception as e:
        print(f"Error in shopping search: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to perform shopping search"
        }


def handle_web_search(body: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle general web search and extraction using Nova Act.

    Args:
        body: Request body with URL and instructions
        credentials: Optional credentials for authenticated access

    Returns:
        Response dictionary with extracted data
    """
    input_data = body.get("input", body)
    url = input_data.get("url", "")
    query = input_data.get("query", "")
    extract_fields = input_data.get("extract_fields", [])

    print(f"Web search: url='{url}', query='{query}', extract_fields={extract_fields}")

    try:
        # Set Nova Act API key from credentials if provided
        if credentials and "NOVA_ACT_API_KEY" in credentials:
            os.environ["NOVA_ACT_API_KEY"] = credentials["NOVA_ACT_API_KEY"]
            print("Nova Act API key configured from credentials")

        # Initialize the Nova Act agent
        agent = NovaActAgent()

        # Build instructions
        if query:
            instructions = f"Search for '{query}' and extract relevant information"
        else:
            instructions = "Navigate the page and extract the requested information"

        # Build task
        task = {
            "url": url,
            "instructions": instructions,
            "extract_data": extract_fields
        }

        result = agent.execute(task)

        print(f"Web search result: {json.dumps(result)[:300]}")

        return {
            "success": result.get("success", False),
            "message": "Web search completed" if result.get("success") else "Web search failed",
            "data": {
                "url": url,
                "query": query,
                "extract_fields": extract_fields,
                "has_credentials": bool(credentials),
                "nova_act_response": result.get("response"),
                "extracted_data": result.get("extracted_data"),
                "session_id": result.get("session_id"),
                "error": result.get("error")
            }
        }
    except Exception as e:
        print(f"Error in web search: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to perform web search"
        }


if __name__ == "__main__":
    # BedrockAgentCoreApp handles HTTP server setup automatically
    # Provides /ping and /invocations endpoints
    app.run()
