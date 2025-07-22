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
        
        # Normalize input messages back to standard format and add the response
        normalized_messages = []
        for msg in messages:
            if "parts" in msg:
                # Convert from Gemini format back to standard format
                normalized_msg = {"role": "assistant" if msg["role"] == "model" else msg["role"]}
                if msg["parts"]:
                    normalized_msg["content"] = []
                    for part in msg["parts"]:
                        if "text" in part:
                            normalized_msg["content"].append({"type": "text", "text": part["text"]})
                        elif "function_call" in part:
                            normalized_msg["content"].append({
                                "type": "tool_use",
                                "id": part["function_call"].get("id"),
                                "name": part["function_call"]["name"],
                                "input": part["function_call"]["args"]
                            })
                        elif "function_response" in part:
                            normalized_msg["content"].append({
                                "type": "tool_result", 
                                "name": part["function_response"]["name"],
                                "content": part["function_response"]["response"]["result"]
                            })
                normalized_messages.append(normalized_msg)
            else:
                # Already in standard format
                normalized_messages.append(msg)
        
        # Add the assistant response
        normalized_messages.append(assistant_message["message"])
        
        return {
            'statusCode': 200,
            'body': {
                'messages': normalized_messages,
                'function_calls': assistant_message["function_calls"],
                'metadata': assistant_message["metadata"]
            }
        }
    except Exception as e:
        logger.error(e)
        raise e # To trigger the retry logic in the caller

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