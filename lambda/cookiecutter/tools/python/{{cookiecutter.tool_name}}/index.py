# This lambda function will be used as a tool {{cookiecutter.tool_name}} for the AI Agent platform

# Imports for Tool

# Imports for Lambda
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities import parameters

# Initialize the logger and tracer
logger = Logger(level="INFO")
tracer = Tracer()

# Tool Functions
def {{cookiecutter.tool_name}}(
    {{cookiecutter.input_param_name}}: str
    ) -> str:
    """{{cookiecutter.description}}.
    Args:
        {{cookiecutter.imput_param_name}} (str): {{cookiecutter.imput_param_description}}.

    Returns:
        str: {{cookiecutter.tool_description}},
             or an error message if the execution fails.

    Raises:
        Exception: Any exception during query execution will be caught and returned as an error message.
    """
    try:
        
        result = "Logic Implementation Here (generated by LLM)"
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
        case '{{cookiecutter.tool_name}}':
            result = {{cookiecutter.tool_name}}(tool_input['{{cookiecutter.imput_param_name}}'])

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