# call_llm/handlers/claude_lambda.py
import sys
print(f"DEBUG: Lambda startup - Python path: {sys.path[:3]}...")

# Test library imports at module level
try:
    import boto3
    print(f"DEBUG: Module level - boto3 version: {boto3.__version__}")
except Exception as e:
    print(f"DEBUG: Module level - boto3 import error: {e}")

try:
    import botocore
    print(f"DEBUG: Module level - botocore version: {botocore.__version__}")
except Exception as e:
    print(f"DEBUG: Module level - botocore import error: {e}")

try:
    import pydantic
    print(f"DEBUG: Module level - pydantic version: {pydantic.__version__}")
except Exception as e:
    print(f"DEBUG: Module level - pydantic import error: {e}")

try:
    import pydantic_core
    print(f"DEBUG: Module level - pydantic_core version: {pydantic_core.__version__}")
except Exception as e:
    print(f"DEBUG: Module level - pydantic_core import error: {e}")

from common.base_llm import logger, tracer
from claude_handler import ClaudeLLM

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    try:
        system = event.get('system')
        messages = event.get('messages', [])
        tools = event.get('tools', [])
        
        llm = ClaudeLLM()
        assistant_message = llm.generate_response(system, messages, tools)
        
        # Update messages with assistant's response
        messages.append(assistant_message["message"])
        
        return {
            'statusCode': 200,
            'body': {
                'messages': messages,
                'function_calls': assistant_message["function_calls"],
                'metadata': assistant_message["metadata"]
            }
        }
    except Exception as e:
        logger.error(e)
        raise e # To activate the retry mechanism in the caller

if __name__ == "__main__":
    # Test event for Claude 3
    test_event_claude = {
        "model": "claude-3-5-sonnet-20241022",
        "system": "You are chatbot, who is helping people with answers to their questions.",
        "messages": [
            {
                "role": "user", 
                "content": "What is 2+2?"
            }
        ],
        "tools": [
            {
                "name": "get_db_schema",
                "description": "Describe the schema of the SQLite database, including table names, and column names and types.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }
    
    # Call lambda handler with test events
    print("\nTesting Claude 3:")
    response_claude = lambda_handler(test_event_claude, None)
    print(response_claude)