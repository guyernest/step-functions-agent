# call_llm/handlers/claude_lambda.py


from common import logger
from llms import ClaudeLLM

def lambda_handler(event, context):
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