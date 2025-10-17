#!/usr/bin/env python3
"""Nova Act Browser Agent for Bedrock Agent Core runtime.

This agent handles browser automation tasks using Nova Act.
It supports three main actions:
- broadband: UK broadband availability checking
- shopping: E-commerce product search
- search: General web search and extraction
"""

import json
import os
from typing import Any, Dict

from nova_act_agent.base_agent import NovaActAgent, BroadbandCheckerAgent, AuthenticatedBroadbandCheckerAgent, ShoppingAgent


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for Agent Core with health check support.

    Args:
        event: Event from Agent Core
        context: Lambda context

    Returns:
        Response dictionary
    """
    # Handle health check requests (Agent Core runtime requirement)
    if event.get("httpMethod") == "GET" and event.get("path") == "/health":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "healthy",
                "agent": "nova-act-browser-agent",
                "version": "1.0.0"
            })
        }

    # Handle readiness check
    if event.get("httpMethod") == "GET" and event.get("path") == "/ready":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "ready": True,
                "agent": "nova-act-browser-agent"
            })
        }

    # Handle Agent Core invocations
    if event.get("httpMethod") == "POST" and event.get("path") == "/invoke":
        try:
            body = json.loads(event.get("body", "{}")) if isinstance(event.get("body"), str) else event.get("body", {})

            # Extract credentials if provided
            credentials = body.get("credentials", {})
            if credentials and "NOVA_ACT_API_KEY" in credentials:
                os.environ["NOVA_ACT_API_KEY"] = credentials["NOVA_ACT_API_KEY"]

            # Route based on input structure
            input_data = body.get("input", {})

            # Determine action type
            if "postcode" in input_data or "building_number" in input_data:
                result = handle_broadband_check(input_data, credentials)
            elif "city" in input_data or "bedrooms" in input_data:
                result = handle_apartment_search(input_data, credentials)
            elif "site" in input_data and "query" in input_data:
                result = handle_shopping_search(input_data, credentials)
            elif "url" in input_data:
                result = handle_web_search(input_data, credentials)
            else:
                result = {
                    "success": False,
                    "error": "Could not determine action type from input",
                    "input_received": input_data
                }

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result)
            }
        except Exception as e:
            import traceback
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "message": "Failed to process request"
                })
            }

    # Handle legacy direct invocation (backward compatibility)
    if "prompt" in event or "input" in event:
        try:
            input_data = event.get("input", {})
            credentials = input_data.get("credentials", {})

            if credentials and "NOVA_ACT_API_KEY" in credentials:
                os.environ["NOVA_ACT_API_KEY"] = credentials["NOVA_ACT_API_KEY"]

            # Determine action type
            if "postcode" in input_data or "building_number" in input_data:
                result = handle_broadband_check(input_data, credentials)
            elif "city" in input_data or "bedrooms" in input_data:
                result = handle_apartment_search(input_data, credentials)
            elif "site" in input_data and "query" in input_data:
                result = handle_shopping_search(input_data, credentials)
            elif "url" in input_data:
                result = handle_web_search(input_data, credentials)
            else:
                result = {
                    "success": False,
                    "error": "Could not determine action type from input"
                }

            return result
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    # Unknown request
    return {
        "statusCode": 400,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Invalid request",
            "message": "Unsupported path or method"
        })
    }


def handle_broadband_check(input_data: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle broadband availability checking using Nova Act.

    Args:
        input_data: Request data with address fields
        credentials: Optional credentials for authenticated checks

    Returns:
        Response dictionary with broadband availability results
    """
    # Extract address from either direct format or nested input
    if "address" in input_data:
        address = input_data["address"]
    else:
        address = {
            "building_number": input_data.get("building_number", ""),
            "street": input_data.get("street", ""),
            "town": input_data.get("town", ""),
            "postcode": input_data.get("postcode", "")
        }

    print(f"Checking broadband for address: {address}")

    try:
        # Set Nova Act API key from credentials if provided
        if credentials and "NOVA_ACT_API_KEY" in credentials:
            os.environ["NOVA_ACT_API_KEY"] = credentials["NOVA_ACT_API_KEY"]
            print("Nova Act API key configured from credentials")

        # Use authenticated agent for BT portal access
        # This logs into My BT Wholesale and uses the internal broadband checker
        agent = AuthenticatedBroadbandCheckerAgent()

        # Execute broadband check with portal credentials
        portal_credentials = {
            "username": credentials.get("BT_USERNAME", "nterizakis") if credentials else "nterizakis",
            "password": credentials.get("BT_PASSWORD", "A1oncloud!") if credentials else "A1oncloud!"
        }

        result = agent.check_broadband(address, portal_credentials)

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
                "recording_url": result.get("recording_url"),
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


def handle_apartment_search(input_data: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle apartment search using Nova Act and Zumper.

    Args:
        input_data: Request data with search parameters
        credentials: Optional credentials

    Returns:
        Response dictionary with apartment listings
    """
    city = input_data.get("city", "Redwood City")
    bedrooms = input_data.get("bedrooms", 2)
    baths = input_data.get("baths", 1)
    min_results = input_data.get("min_results", 5)

    print(f"Apartment search: city='{city}', bedrooms={bedrooms}, baths={baths}, min_results={min_results}")

    try:
        # Set Nova Act API key from credentials if provided
        if credentials and "NOVA_ACT_API_KEY" in credentials:
            os.environ["NOVA_ACT_API_KEY"] = credentials["NOVA_ACT_API_KEY"]
            print("Nova Act API key configured from credentials")

        # Initialize the Shopping Agent
        agent = ShoppingAgent()

        # Execute apartment search
        search_params = {
            "city": city,
            "bedrooms": bedrooms,
            "baths": baths,
            "min_results": min_results
        }
        result = agent.search_apartments(search_params)

        print(f"Apartment search result: {json.dumps(result)[:300]}")

        return {
            "success": result.get("success", False),
            "message": "Apartment search completed" if result.get("success") else "Apartment search failed",
            "data": {
                "city": city,
                "bedrooms": bedrooms,
                "baths": baths,
                "min_results": min_results,
                "has_credentials": bool(credentials),
                "apartments": result.get("apartments"),
                "response": result.get("response"),
                "session_id": result.get("session_id"),
                "recording_url": result.get("recording_url"),
                "error": result.get("error")
            }
        }
    except Exception as e:
        print(f"Error in apartment search: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to perform apartment search"
        }


def handle_shopping_search(input_data: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle e-commerce product search using Nova Act.

    Args:
        input_data: Request data with search query
        credentials: Optional credentials for authenticated searches

    Returns:
        Response dictionary with product search results
    """
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
                "recording_url": result.get("recording_url"),
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


def handle_web_search(input_data: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle general web search and extraction using Nova Act.

    Args:
        input_data: Request data with URL and instructions
        credentials: Optional credentials for authenticated access

    Returns:
        Response dictionary with extracted data
    """
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
                "recording_url": result.get("recording_url"),
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
    # This allows the module to be run with python -m browser_agent
    from bedrock_agentcore import BedrockAgentCoreApp
    app = BedrockAgentCoreApp()

    @app.entrypoint
    def invoke(event, context):
        return handler(event, context)

    app.run()
