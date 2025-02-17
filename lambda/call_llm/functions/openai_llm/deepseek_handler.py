# llms/deepseek_handler.py
from openai import OpenAI
from common.base_llm import BaseLLM, logger
from openai_handler import OpenAILLM
from common.config import get_api_keys

from typing import List, Dict
import json

# Using DeepSeek's API directly
MODEL_ID = "deepseek-chat"
# Using OpenRouter's API to call DeepSeek
# MODEL_ID = "deepseek/deepseek-chat",

class DeepSeekLLM(OpenAILLM):
    def __init__(self):
        api_keys = get_api_keys()
        # Using DeepSeek's API directly
        self.client = OpenAI(api_key=api_keys["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
        # Using OpenRouter's API to call DeepSeek
        # self.client = OpenAI(api_key=api_keys["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
    
    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        prepared_messages = self.prepare_messages(system, messages, tools)
        logger.info(f"Sending request to DeepSeek: {json.dumps(prepared_messages, indent=2)}")
        completion = self.client.chat.completions.create(
            model=MODEL_ID,
            **prepared_messages
        )
        logger.info(f"Received response from DeepSeek: {completion}")
        return self.convert_to_json(completion)