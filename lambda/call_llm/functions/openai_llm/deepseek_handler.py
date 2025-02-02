# llms/deepseek_handler.py
from openai import OpenAI
from common.base_llm import BaseLLM, logger
from openai_handler import OpenAILLM
from common.config import get_api_keys

from typing import List, Dict
import json

class DeepSeekLLM(OpenAILLM):
    def __init__(self):
        api_keys = get_api_keys()
        self.client = OpenAI(api_key=api_keys["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
    
    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        prepared_messages = self.prepare_messages(system, messages, tools)
        completion = self.client.chat.completions.create(
            model="deepseek-chat",
            **prepared_messages
        )
        return self.convert_to_json(completion)