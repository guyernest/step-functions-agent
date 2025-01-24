# handlers/bedrock_lambda.py
import os
import sys

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(current_dir)

from common.base_llm import logger
from llms.bedrock_handler import BedrockLLM

def lambda_handler(event, context):
    try:
        system = event.get('system')
        messages = event.get('messages', [])
        tools = event.get('tools', [])
        
        llm = BedrockLLM()
        assistant_message = llm.generate_response(system, messages, tools)
        logger.info(assistant_message)
        messages.append(assistant_message["message"])
        
        return {
            'statusCode': 200,
            'body': {
                'messages': messages,
                'metadata': assistant_message["metadata"]
            }
        }
    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

if __name__ == "__main__":
    # Test event for Jamba model
    event = {
        "model": "ai21.jamba-1-5-large-v1:0",
        "messages": [
            {"role": "user", "content": "What is 25*4+64*3?"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                    },
                },
            }
        ]
    }
    response = lambda_handler(event, None)
    print(response)