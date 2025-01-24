# llms/openai_handler.py
from openai import OpenAI
from common.base_llm import BaseLLM, logger
from common.config import get_api_keys

from typing import List, Dict

class OpenAILLM(BaseLLM):
    def __init__(self):
        api_keys = get_api_keys()
        self.client = OpenAI(api_key=api_keys["OPENAI_API_KEY"])
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        if system and messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": system})
        return {
            "messages": messages,
            "tools": tools
        }
    
    def convert_to_json(self, completion) -> Dict:
        choice = completion.choices[0]
        message = choice.message
        return {
            "message": {
                "role": message.role,
                "content": [{"text": message.content, "type": "text"}] if message.content else [],
                "tool_calls": [{
                    "id": tool_call.id,
                    "function": {
                        "arguments": tool_call.function.arguments,
                        "name": tool_call.function.name,
                    },
                    "type": tool_call.type
                } for tool_call in message.tool_calls] if message.tool_calls else []
            },
            "metadata": {
                "stop_reason": choice.finish_reason,
                "usage": {
                    "input_tokens": completion.usage.prompt_tokens,
                    "output_tokens": completion.usage.completion_tokens
                }
            }
        }
    
    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        prepared_messages = self.prepare_messages(system, messages, tools)
        completion = self.client.chat.completions.create(
            model="gpt-4",
            **prepared_messages
        )
        return self.convert_to_json(completion)