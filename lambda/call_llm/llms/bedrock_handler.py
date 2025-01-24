# llms/bedrock_handler.py
import boto3
import json
from common.base_llm import BaseLLM, logger

from typing import List, Dict

class BedrockLLM(BaseLLM):
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        if system and messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": system})
        return {
            "messages": messages,
            "max_tokens": 4096,
            "tools": tools
        }
    
    def convert_to_json(self, response) -> Dict:
        completion = json.loads(response['body'].read().decode('utf-8'))
        logger.info(f"Completion: {completion}")
        first_choice = completion['choices'][0]
        message = first_choice['message']
        
        message_dict = {
            "role": "assistant",
            "tool_calls": [{
                "id": tool_call["id"],
                "function": {
                    "arguments": tool_call["function"]["arguments"],
                    "name": tool_call["function"]["name"],
                },
                "type": tool_call["type"]
            } for tool_call in (message.get("tool_calls") or []) if tool_call is not None]
        }

        if message.get("content"):
            message_dict["content"] = [{"text": message["content"], "type": "text"}]

        return {
            "message": message_dict,
            "metadata": {
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
            modelId="ai21.jamba-1-5-large-v1:0",
            body=json.dumps(prepared_messages)
        )
        logger.info(f"Bedrock response: {response}")
        return self.convert_to_json(response)