# llms/openai_handler.py
from openai import OpenAI
from common.base_llm import BaseLLM, logger
from common.config import get_api_keys

from typing import List, Dict, Any
import json
import os

DEFAULT_MODEL_ID = "gpt-4o"

class OpenAILLM(BaseLLM):
    def __init__(self, model_id: str = None):
        api_keys = get_api_keys()
        self.client = OpenAI(api_key=api_keys["OPENAI_API_KEY"])
        self.model_id = model_id or DEFAULT_MODEL_ID
    
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
        try:
            # Detect response format for compatibility
            format_info = self.detect_response_format(completion)
            
            # Try multiple paths for extracting choice and message
            choice = self.safe_extract_field(completion, ['choices.0', 'results.0'])
            if not choice:
                return self.create_error_response("No valid choice found in OpenAI response", format_info)
            
            message = self.safe_get_nested(choice, 'message')
            if not message:
                return self.create_error_response("No message found in OpenAI choice", format_info)
            
            # Safely extract message fields
            role = self.safe_get_nested(message, 'role', 'assistant')
            content = self.safe_get_nested(message, 'content', '')
            tool_calls = self.safe_get_nested(message, 'tool_calls', [])
            
            # Handle different content formats (GPT-5 might change this)
            content_formatted = [{"text": content, "type": "text"}] if content else ""
            
            # Safely process tool calls
            processed_tool_calls = []
            processed_function_calls = []
            
            if tool_calls:
                for tool_call in tool_calls:
                    try:
                        tool_id = self.safe_get_nested(tool_call, 'id')
                        tool_type = self.safe_get_nested(tool_call, 'type', 'function')
                        function_name = self.safe_get_nested(tool_call, 'function.name')
                        function_args = self.safe_get_nested(tool_call, 'function.arguments', '{}')
                        
                        if not tool_id or not function_name:
                            logger.warning(f"Incomplete tool call data: id={tool_id}, name={function_name}")
                            continue
                            
                        processed_tool_calls.append({
                            "id": tool_id,
                            "function": {
                                "arguments": function_args,
                                "name": function_name,
                            },
                            "type": tool_type
                        })
                        
                        # Parse arguments safely for function_calls format
                        try:
                            parsed_args = json.loads(function_args) if isinstance(function_args, str) else function_args
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse function arguments: {function_args}, error: {e}")
                            parsed_args = {}
                            
                        processed_function_calls.append({
                            "id": tool_id,
                            "input": parsed_args,
                            "name": function_name,
                        })
                        
                    except Exception as e:
                        logger.warning(f"Failed to process tool call: {tool_call}, error: {e}")
                        continue
            
            # Safely extract metadata
            finish_reason = self.safe_get_nested(choice, 'finish_reason', 'unknown')
            usage_input = self.safe_extract_field(completion, ['usage.prompt_tokens', 'usage.input_tokens'], 0)
            usage_output = self.safe_extract_field(completion, ['usage.completion_tokens', 'usage.output_tokens'], 0)
            
            return {
                "message": {
                    "role": role,
                    "content": content_formatted,
                    "tool_calls": processed_tool_calls
                },
                "function_calls": processed_function_calls,
                "metadata": {
                    "model": self.model_id,
                    "stop_reason": finish_reason,
                    "usage": {
                        "input_tokens": usage_input,
                        "output_tokens": usage_output
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to convert OpenAI response to JSON: {str(e)}")
            return self.create_error_response(f"Response conversion failed: {str(e)}", {"model": self.model_id})
    
    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        try:
            prepared_messages = self.prepare_messages(system, messages, tools)
            completion = self.client.chat.completions.create(
                model=self.model_id,
                **prepared_messages
            )
            return self.convert_to_json(completion)
        except Exception as e:
            logger.error(f"OpenAI API call failed with model {self.model_id}: {str(e)}")
            return self.create_error_response(f"API call failed: {str(e)}", {"model": self.model_id})