import json
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
# TODO Split to separate files for each LLM
import anthropic
from openai import OpenAI
import boto3

logger = Logger(level="INFO")

# Loading the API KEYs for the LLM and related services
try:
    ANTHROPIC_API_KEY = json.loads(parameters.get_secret("/ai-agent/api-keys"))["ANTHROPIC_API_KEY"]
    OPENAI_API_KEY = json.loads(parameters.get_secret("/ai-agent/api-keys"))["OPENAI_API_KEY"]
except ValueError:
    raise ValueError("API keys not found in Secrets Manager")

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# To translate between JSON and the LLM message format
from anthropic.types import Message, TextBlock, ToolUseBlock

def convert_claude_message_to_json(message):
    logger.info(f"Converting Claude message to JSON: {message}")
    message_dict = {
        "message" : {
            "role": message.role,
            "content": [],
        }, 
        "metadata" : {
            "stop_reason": message.stop_reason,
            "stop_sequence": message.stop_sequence,
            "type": message.type,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens
            }
        }
    }
    
    for block in message.content:
        if isinstance(block, TextBlock):
            message_dict["message"]["content"].append({
                "text": block.text,
                "type": block.type
            })
        elif isinstance(block, ToolUseBlock):
            message_dict["message"]["content"].append({
                "id": block.id,
                "input": block.input,
                "name": block.name,
                "type": block.type
            })
    
    return message_dict

def convert_gpt4_message_to_json(completion):
    logger.info(f"Converting GPT-4 message to JSON: {completion}")

    choice = completion.choices[0]
    message = choice.message
    message_dict = {
        "message" : {
            "role": message.role,
            "content": [],
            "tool_calls": []
        }, 
        "metadata" : {
            "stop_reason": choice.finish_reason,
            "usage": {
                "input_tokens": completion.usage.prompt_tokens,
                "output_tokens": completion.usage.completion_tokens
            }
        }
    }
    
    if message.tool_calls:
        for tool_call in message.tool_calls:
            message_dict["message"]["tool_calls"].append({
                "id": tool_call.id,
                "function": {   
                    "arguments": tool_call.function.arguments,
                    "name": tool_call.function.name,
                },
                "type": tool_call.type
            })

    if message.content:
        message_dict["message"]["content"].append({
            "text": message.content,
            "type": "text"
        })

    return message_dict

def convert_bedrock_message_to_json(completion):
    logger.info(f"Converting Bedrock message to JSON: {completion}")
    completion = json.loads(completion['body'].read().decode('utf-8'))
    first_choice = completion['choices'][0]
    message = first_choice['message']
    logger.info(f"Processing Bedrock message: {message}")

    message_dict = {
        "message" : {
            "role": "assistant",
            "tool_calls": []
        },
        "metadata" : {
            "stop_reason": first_choice["finish_reason"],
            "usage": {
                "input_tokens": completion["usage"]["prompt_tokens"],
                "output_tokens": completion["usage"]["completion_tokens"]
            }
        }
    }
    if message["tool_calls"]:
        for tool_call in message["tool_calls"]:
            message_dict["message"]["tool_calls"].append({
                "id": tool_call["id"],
                "function": {
                    "arguments": tool_call["function"]["arguments"],
                    "name": tool_call["function"]["name"],
                },
                "type": tool_call["type"]
            })
    if message["content"]:
        if not "content" in message_dict["message"]:
            message_dict["message"]["content"] = []
        message_dict["message"]["content"].append({
            "text": message["content"],
            "type": "text"
        })

    return message_dict


def lambda_handler(event, context):
    # Get system, messages, and model from event
    system = event.get('system')
    messages = event.get('messages')
    tools = event.get('tools', [])
    # Default to Claude 3.5 Sonner
    model = event.get('model', 'claude-3-5-sonnet-20241022').lower() 
    
    try:
        if 'claude' in model:
            #Send a request to Claude
            response = anthropic_client.messages.create(
                system = system,
                model=model,
                max_tokens=4096,
                tools=tools,
                messages=messages
            )

            assistant_message = convert_claude_message_to_json(response)

            # Update messages to include Claude's response
            messages.append(assistant_message["message"])
            
            logger.info(f"Claude result: {assistant_message}")
            
        elif 'gpt-4' in model:
            #Send a request to GPT-4
            completion = openai_client.chat.completions.create(
                model=model,
                tools=tools,
                messages=messages
            )            
            # Update messages to include GPT-4's response
            assistant_message = convert_gpt4_message_to_json(completion)

            messages.append(assistant_message["message"])
            
            logger.info(f"GPT-4 result: {assistant_message}")
           
        elif 'jamba' in model:
            #Send a request to Jamba
            print("Jamba was called through Bedrock")
            # The Jamba models are only available in us-east-1, currently.
            bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

            # Handle the system message by appending it to the first user message
            if system and messages and messages[0]['role'] == 'user':
                # prepend the system message to the first user message
                messages.insert(
                    0, 
                    {
                        "role": "system",
                        "content": system
                    }
                )
           
            print(f"Messages: {messages}")

            response = bedrock_client.invoke_model( 
                modelId=model, 
                body=json.dumps({
                    'messages': messages,
                    'max_tokens': 4096,
                    'tools': tools
                }) 
            ) 
            assistant_message = convert_bedrock_message_to_json(response)

            # Update messages to include Jamba's response
            messages.append(assistant_message["message"])
            logger.info(f"AI21 result: {assistant_message}")
            
        else:
            raise ValueError(f"Unsupported model: {model}")
            
        return {
            'statusCode': 200,
            'body': {
                'messages': messages,
                'metadata' : assistant_message["metadata"]
            }
        }
        
    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
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
    # response_claude = lambda_handler(test_event_claude, None)
    # print(response_claude)

    # Test event for GPT-4
    test_event_gpt4 = {
        "model": "gpt-4o",
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
    
    
    print("\nTesting GPT-4:")
    # response_gpt4 = lambda_handler(test_event_gpt4, None)
    # print(response_gpt4)


    print("\nTesting AI21:")
    test_event_ai21 = test_event_gpt4.copy()
    test_event_ai21["model"] = "ai21.jamba-1-5-large-v1:0"
    test_event_ai21["system"] = "You are chatbot, who is helping people with answers to their questions."

    response_ai21 = lambda_handler(test_event_ai21, None)
    print(response_ai21)

