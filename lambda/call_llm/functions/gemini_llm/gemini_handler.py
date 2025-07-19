from google import genai
from google.genai import types
import os

from common.base_llm import BaseLLM, logger
from common.config import get_api_keys
from typing import List, Dict

MODEL_ID = "gemini-2.0-flash-001"

class GeminiLLM(BaseLLM):
    def __init__(self):
        api_keys = get_api_keys()
        gemini_key = api_keys.get("GEMINI_API_KEY")
        logger.info(f"DEBUG: Retrieved API keys: {list(api_keys.keys())}")
        logger.info(f"DEBUG: Gemini API key present: {gemini_key is not None}")
        logger.info(f"DEBUG: Gemini API key length: {len(gemini_key) if gemini_key else 'None'}")
        logger.info(f"DEBUG: Gemini API key starts with: {gemini_key[:10] if gemini_key else 'None'}...")
        
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY not found in secrets")
        
        # Set the API key as environment variable and create client
        os.environ['GOOGLE_API_KEY'] = gemini_key
        self.client = genai.Client()
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        # Convert tools to Gemini format using types.Tool
        gemini_tools = []
        if tools:
            function_declarations = []
            for tool in tools:
                # Only include properties and required fields for parameters_json_schema
                schema = tool["input_schema"]
                clean_schema = {}
                if "properties" in schema and schema["properties"]:
                    clean_schema = {
                        "type": "object",
                        "properties": schema["properties"]
                    }
                    if "required" in schema:
                        clean_schema["required"] = schema["required"]
                
                # Create function declaration without parameters_json_schema first
                func_decl_args = {
                    "name": tool["name"],
                    "description": tool["description"]
                }
                
                # Only add parameters if we have a valid schema
                if clean_schema:
                    func_decl_args["parameters"] = clean_schema
                
                func_decl = types.FunctionDeclaration(**func_decl_args)
                function_declarations.append(func_decl)
            
            if function_declarations:
                gemini_tools = [types.Tool(function_declarations=function_declarations)]

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
                "model": MODEL_ID,
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
        
        # Build config with tools if present
        config_params = {
            "temperature": 0.7,
            "max_output_tokens": 2048,
            "system_instruction": prepared_messages["system"]
        }
        if prepared_messages["tools"]:
            config_params["tools"] = prepared_messages["tools"]
        
        response = self.client.models.generate_content(
            model=MODEL_ID,
            contents=prepared_messages["messages"],
            config=types.GenerateContentConfig(**config_params)
        )
        
        return self.convert_to_json(response)