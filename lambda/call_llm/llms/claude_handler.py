# call_llm/llms/claude_handler.py
import os
import sys

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(current_dir)

import anthropic
from anthropic.types import Message, TextBlock, ToolUseBlock
from common.base_llm import BaseLLM, logger
from common.config import get_api_keys

from typing import List, Dict

class ClaudeLLM(BaseLLM):
    def __init__(self):
        api_keys = get_api_keys()
        self.client = anthropic.Anthropic(api_key=api_keys["ANTHROPIC_API_KEY"])
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
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
            "metadata": {
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
    
    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        prepared_messages = self.prepare_messages(system, messages, tools)
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            **prepared_messages
        )
        return self.convert_to_json(response)