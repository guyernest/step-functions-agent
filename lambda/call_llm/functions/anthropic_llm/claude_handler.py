# call_llm/functions/anthropic/claude_handler.py
import anthropic
from anthropic.types import Message, TextBlock, ToolUseBlock
from common.base_llm import BaseLLM
from common.config import get_api_keys

from typing import List, Dict

MODEL_ID = "claude-3-7-sonnet-latest"

class ClaudeLLM(BaseLLM):
    def __init__(self):
        api_keys = get_api_keys()
        self.client = anthropic.Anthropic(api_key=api_keys["ANTHROPIC_API_KEY"])
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:

        # Convert messages to Claude format
        last_message = messages[-1]
        if last_message["role"] == "user":
            if "content" in last_message:
                if isinstance(last_message["content"], list):
                    for part in last_message["content"]:
                        if "type" in part and part["type"] == "tool_result":  # tool_use
                            del part["name"]


        return {
            "system": system,
            "messages": messages,
            "tools": tools,
            "max_tokens": 4096
        }
    
    def convert_to_json(self, message: Message) -> Dict:
        message_dict = {
            "message": {
                "role": message.role,
                "content": [],
            },
            "function_calls": [],
            "metadata": {
                "model": MODEL_ID,
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
                message_dict["function_calls"].append({
                    "id": block.id,
                    "input": block.input,
                    "name": block.name,
                })
        
        return message_dict
    
    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        prepared_messages = self.prepare_messages(system, messages, tools)
        response = self.client.messages.create(
            model=MODEL_ID,
            **prepared_messages
        )
        return self.convert_to_json(response)