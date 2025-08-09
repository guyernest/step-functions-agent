# call_llm/functions/anthropic/claude_handler.py
import anthropic
from anthropic.types import Message, TextBlock, ToolUseBlock
from common.base_llm import BaseLLM, logger
from common.config import get_api_keys

from typing import List, Dict

DEFAULT_MODEL_ID = "claude-3-7-sonnet-latest"

class ClaudeLLM(BaseLLM):
    def __init__(self, model_id: str = None):
        api_keys = get_api_keys()
        self.client = anthropic.Anthropic(api_key=api_keys["ANTHROPIC_API_KEY"])
        self.model_id = model_id or DEFAULT_MODEL_ID
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:

        # Convert messages to Claude format
        messages_formatted = []
        for message in messages:
            # Create a clean message with only the required fields
            clean_message = {"role": message["role"]}
            
            # Handle content field
            if "content" in message:
                if isinstance(message["content"], list):
                    content_list = []
                    for part in message["content"]:
                        # For tool_result, only include required fields
                        if "type" in part and part["type"] == "tool_result":
                            clean_part = {
                                "type": "tool_result",
                                "tool_use_id": part["tool_use_id"],
                                "content": part["content"]
                            }
                            content_list.append(clean_part)
                        # For tool_use, include required fields
                        elif "type" in part and part["type"] == "tool_use":
                            clean_part = {
                                "type": "tool_use",
                                "id": part["id"],
                                "name": part["name"],
                                "input": part["input"]
                            }
                            content_list.append(clean_part)
                        # For other content types, include safe fields
                        elif "type" in part:
                            if part["type"] == "text" and "text" in part:
                                clean_part = {
                                    "type": "text",
                                    "text": part["text"]
                                }
                                content_list.append(clean_part)
                            elif part["type"] == "image" and "source" in part:
                                clean_part = {
                                    "type": "image",
                                    "source": part["source"]
                                }
                                content_list.append(clean_part)
                    clean_message["content"] = content_list
                else:
                    # String content
                    clean_message["content"] = message["content"]
            messages_formatted.append(clean_message)

        # Format system with cache_control
        if isinstance(system, str):
            # If it's a single string, convert to list format with cache_control
            system_formatted = [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        elif isinstance(system, list) and system:
            # If it's already a list, add cache_control to last element
            system_formatted = system.copy()
            if "cache_control" not in system_formatted[-1]:
                system_formatted[-1] = {**system_formatted[-1], "cache_control": {"type": "ephemeral"}}
        elif isinstance(system, dict):
            # If it's a dict, add cache_control directly to it
            system_formatted = {**system, "cache_control": {"type": "ephemeral"}}
        else:
            # Fallback case
            system_formatted = system
        
        # Add cache_control to the last tool if tools exist
        tools_formatted = []
        if tools and isinstance(tools, list):
            tools_formatted = tools.copy()
            if tools_formatted:
                if "cache_control" not in tools_formatted[-1]:
                    tools_formatted[-1] = {**tools_formatted[-1], "cache_control": {"type": "ephemeral"}}
        else:
            tools_formatted = tools

        # Return only the valid fields expected by the Anthropic API
        return {
            "system": system_formatted,
            "tools": tools_formatted,
            "messages": messages_formatted,
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
                "model": self.model_id,
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
        try:
            prepared_messages = self.prepare_messages(system, messages, tools)
            print("prepared_messages", prepared_messages)
            response = self.client.messages.create(
                model=self.model_id,
                **prepared_messages
            )
            return self.convert_to_json(response)
        except Exception as e:
            logger.error(f"Claude API call failed with model {self.model_id}: {str(e)}")
            return self.create_error_response(f"API call failed: {str(e)}", {"model": self.model_id})