# functions/bedrock/bedrock_handler.py
import boto3
import json
from common.base_llm import BaseLLM, logger

from typing import List, Dict

MODEL_ID = "ai21.jamba-1-5-large-v1:0"

class BedrockLLM(BaseLLM):
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:

        jamba_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    # Unpack the input_schema if it exists, otherwise don't include the parameters key
                    **({"parameters": tool["input_schema"]} if tool["input_schema"]["properties"] != {} else {})
                },
            }
            for tool in tools
        ] if tools else []

        # Replace the last message with the tool_use_id and content messages.
        last_message = messages[-1]
        if last_message["role"] == "user":
            if "content" in last_message:
                if isinstance(last_message["content"], list):   
                    remove_last_message = True                     
                    for part in last_message["content"]:
                        if "type" in part and part["type"] == "tool_result":
                            if remove_last_message:
                                messages.pop()
                                remove_last_message = False
                            messages.append({
                                "role": "tool",
                                "tool_call_id": part["tool_use_id"],
                                "content": json.dumps(part["content"])
                            })  # tool_use


        if system and messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": system})
        return {
            "messages": messages,
            "tools": jamba_tools
        }
    
    def convert_to_json(self, response) -> Dict:
        completion = json.loads(response['body'].read().decode('utf-8'))
        logger.info(f"Completion: {completion}")
        first_choice = completion['choices'][0]
        message = first_choice['message']
        
        message_dict = {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tool_call["id"],
                    "function": {
                        "arguments": tool_call["function"]["arguments"],
                        "name": tool_call["function"]["name"],
                    },
                    "type": tool_call["type"]
                } for tool_call in message["tool_calls"]
            ] if message["tool_calls"] else []
        }

        if message.get("content"):
            message_dict["content"] = message["content"]

        return {
            "message": message_dict,
            "function_calls": [
                {
                    "id": tool_call["id"],
                    "input": json.loads(tool_call["function"]["arguments"]),
                    "name": tool_call["function"]["name"],
                } for tool_call in message["tool_calls"]
            ] if "tool_calls" in message and message["tool_calls"] else [],
            "metadata": {
                "model": MODEL_ID,
                "stop_reason": first_choice["finish_reason"],
                "usage": {
                    "input_tokens": completion["usage"]["prompt_tokens"],
                    "output_tokens": completion["usage"]["completion_tokens"]
                }
            }
        }

    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        prepared_messages = self.prepare_messages(system, messages, tools)
        logger.info(f"Messages: {prepared_messages}")
        response = self.client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(prepared_messages)
        )
        logger.info(f"Bedrock response: {response}")
        return self.convert_to_json(response)