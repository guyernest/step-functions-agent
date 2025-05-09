# llms/openai_handler.py
from openai import OpenAI
from common.base_llm import BaseLLM, logger
from common.config import get_api_keys

from typing import List, Dict
import json

MODEL_ID = "gpt-4o"

class OpenAILLM(BaseLLM):
    def __init__(self):
        api_keys = get_api_keys()
        self.client = OpenAI(api_key=api_keys["OPENAI_API_KEY"])
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        # Convert tools to OpenAI format
        openai_tools = [
            {
                "type": "function",
                "function":
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        # Unpack the input_schema if it exists, otherwise don't include the parameters key
                        **({"parameters": tool["input_schema"]} if tool["input_schema"]["properties"] != {} else { "type": "object", "properties": {} })
                    }
            } for tool in tools
        ] if tools else []

        # # Convert messages to OpenAI format
        # for message in messages:
        #     if message["role"] == "user":
        #         if "content" in message:
        #             if isinstance(message["content"], list):                        
        #                 for part in message["content"]:
        #                     if "type" in part and part["type"] == "tool_result":  # tool_use
        #                         message['role'] = 'tool'
        #                         part['tool_call_id'] = part['tool_use_id']
        #                         part['content'] = json.dumps(part['content'])

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
            "tools": openai_tools
        }
    
    def convert_to_json(self, completion) -> Dict:
        choice = completion.choices[0]
        message = choice.message
        return {
            "message": {
                "role": message.role,
                "content": [{"text": message.content, "type": "text"}] if message.content else "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "function": {
                            "arguments": tool_call.function.arguments,
                            "name": tool_call.function.name,
                        },
                        "type": tool_call.type
                    } for tool_call in message.tool_calls
                ] if message.tool_calls else []
            },
            "function_calls": [
                {
                    "id": tool_call.id,
                    "input": json.loads(tool_call.function.arguments),
                    "name": tool_call.function.name,
                } for tool_call in message.tool_calls
            ] if message.tool_calls else [],
            "metadata": {
                "model": MODEL_ID,
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
            model=MODEL_ID,
            **prepared_messages
        )
        return self.convert_to_json(completion)