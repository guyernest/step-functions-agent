from google import genai
from google.genai import types

from common.base_llm import BaseLLM, logger
from common.config import get_api_keys
from typing import List, Dict
import json

class GeminiLLM(BaseLLM):
    def __init__(self):
        api_keys = get_api_keys()
        self.client = genai.Client(api_key='AIzaSyBPpyWRLsSHC7dhTKOshZ8RyDBiZEN4HTg')
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        # Convert tools to Gemini format
        gemini_tools = [
            {
                "function_declarations": [
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        # Unpack the input_schema if it exists, otherwise don't include the parameters key
                        **({"parameters": tool["input_schema"]} if tool["input_schema"]["properties"] != {} else {})
                    }
                ]
            } for tool in tools] if tools else []

        # Convert messages to Gemini format
        for message in messages:
            if message["role"] == "user":
                if "content" in message:
                    if isinstance(message["content"], str):
                        message["parts"] = [{"text": message["content"]}]
                    elif isinstance(message["content"], list):
                        message["parts"] = []
                        for part in message["content"]:
                            if "type" in part and part["type"] == "tool_result":  # tool_use
                                message["parts"].append({
                                    "function_response": {
                                        "name": part["name"],
                                        "response" : {
                                            "result" : part["content"]
                                        }
                                    }
                                })
                    
                    del message["content"]

        return {
            "messages": messages,
            "tools": gemini_tools,
            "system": system
        }    
    
    def convert_to_json(self, response) -> Dict:
        function_call_content = response.candidates[0].content
        first_function_call_part = function_call_content.parts[0]

        message_dict = {
            "message": {
                "role": function_call_content.role,
                "parts": [],
            },
            "function_calls": [],
            "metadata": {
                "stop_reason": response.candidates[0].finish_reason,
                "usage": {
                    "input_tokens": response.usage_metadata.prompt_token_count,
                    "output_tokens": response.usage_metadata.candidates_token_count
                }
            }
        }
        
        for part in function_call_content.parts:
            if part.text:
                message_dict["message"]["parts"].append({
                    "text": part.text,
                })
            elif part.function_call:
                message_dict["function_calls"].append({
                    "id": part.function_call.id,
                    "input": part.function_call.args,
                    "name": part.function_call.name,
                })
                message_dict["message"]["parts"].append({
                    "function_call" : {
                        "id" : part.function_call.id,
                        "name" : part.function_call.name,
                        "args" : part.function_call.args
                    }
                })
        
        return message_dict

    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        prepared_messages = self.prepare_messages(system, messages, tools)
        logger.info(f"Prepared messages: {prepared_messages}")
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prepared_messages["messages"],
            config=types.GenerateContentConfig(
                system_instruction=prepared_messages["system"],
                tools=prepared_messages["tools"]
            ),
        )
        
        return self.convert_to_json(response)