# This lambda function will be used as a tool EarthQuakeQuery for the AI Agent platform

# Imports for Tool
import requests
import json

# Imports for Lambda
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities import parameters

# Initialize the logger and tracer
logger = Logger(level="INFO")
tracer = Tracer()

# Tool Functions
def query_earthquakes(starttime, endtime):
    """
    Function to retrieve earthquake data from the USGS Earthquake Hazards Program API.

    :param starttime: The start time for the earthquake data in YYYY-MM-DD format.
    :param endtime: The end time for the earthquake data in YYYY-MM-DD format.
    :return: The result of the earthquake data retrieval as a dictionary.
    """
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": 4.5,
        "limit": 1000
    }
    
    try:
        response = requests.get(url, params=params)
        logger.info(f"Earthquake API response: {response}")
        response.raise_for_status()  # Raises an error for HTTP errors
        return json.dumps(response.json(), indent=2)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving earthquake data: {e}")
        return {"error": "An error occurred while retrieving earthquake data."}

api_tool = {
    "function": query_earthquakes,
    "definition": {
        "name": "query_earthquakes",
        "description": "Retrieve earthquake data from the USGS Earthquake Hazards Program API and display the .",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "The start date for the earthquake data in YYYY-MM-DD format."
                },
                "end_date": {
                    "type": "string",
                    "description": "The end date for the earthquake data in YYYY-MM-DD format."
                }
            },
            "required": [
                "start_date", 
                "end_date"
            ]
        }
    }
}


@tracer.capture_method
def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use['name']
    tool_input = tool_use['input']

    logger.info(f"Tool name: {tool_name}")
    match tool_name:
        case 'query_earthquakes':
            result = query_earthquakes(
                tool_input['start_date'], 
                tool_input['end_date']
            )

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