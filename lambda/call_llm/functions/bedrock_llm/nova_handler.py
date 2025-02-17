# llms/bedrock_handler.py
import boto3
import json
from common.base_llm import BaseLLM, logger
from bedrock_handler import BedrockLLM

from typing import List, Dict

LITE_MODEL_ID = "us.amazon.nova-lite-v1:0"
PRO_MODEL_ID = "us.amazon.nova-pro-v1:0"

MODEL_ID = PRO_MODEL_ID

class NovaLLM(BedrockLLM):
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name='us-west-2')
    
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:

        nova_tools = [
            {
                "toolSpec": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "inputSchema": {
                        **({"json": tool["input_schema"]} if tool["input_schema"]["properties"] != {} else {})
                    }
                }
            }
            for tool in tools
        ] if tools else []

        # Replace the last message with the tool_use_id and content messages.
        last_message = messages[-1]
        if last_message["role"] == "user":
            if "content" in last_message:
                if isinstance(last_message["content"], str):  
                     last_message["content"] = [
                        {
                            "text": last_message["content"]
                        }
                    ]
                elif isinstance(last_message["content"], list):   
                    last_message["content"] = [
                        { 
                            "toolResult": {
                                "toolUseId": tool['tool_use_id'],
                                "content": [
                                    {
                                        "json": tool['content']
                                    }
                                ]
                            }
                        }
                        for tool in last_message["content"] if tool['tool_use_id'] is not None]

        if system:
            system_list = [
                {
                    "text": system,
                }
            ]

        return {
            "messages": messages,
            "toolConfig" : {
                "tools": nova_tools
            } if tools else None,
           "system": system_list if system else None
        }

    def convert_to_json(self, response) -> Dict:
        completion = json.loads(response['body'].read().decode('utf-8'))
        logger.info(f"Completion: {completion}")
        output = completion['output']
        message = output['message']
        
        function_calls = []
        for part in message["content"]:
            if "toolUse" in part:
                function_calls.append({
                    "id": part["toolUse"]["toolUseId"],
                    "input": part["toolUse"]["input"],
                    "name": part["toolUse"]["name"],
                })

        return {
            "message": message,
            "function_calls": function_calls,
            "metadata": {
                "model": MODEL_ID,
                "stop_reason": completion["stopReason"],
                "usage": {
                    "input_tokens": completion["usage"]["inputTokens"],
                    "output_tokens": completion["usage"]["outputTokens"]
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