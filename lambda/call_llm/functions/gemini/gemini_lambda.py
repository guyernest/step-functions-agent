# call_llm/handlers/gemini_lambda.py
from common.base_llm import logger
from gemini_handler import GeminiLLM

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    try:
        system = event.get('system')
        messages = event.get('messages', [])
        tools = event.get('tools', [])
        
        llm = GeminiLLM()
        assistant_message = llm.generate_response(system, messages, tools)
        
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
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

if __name__ == "__main__":
    test_event = {
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
                            "b": {"type": "number"}
                        }
                    }
                }
            }
        ]
    }
    response = lambda_handler(test_event, None)
    print(response)