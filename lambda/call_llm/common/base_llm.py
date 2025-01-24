from abc import ABC, abstractmethod
from typing import Dict, List, Any
from aws_lambda_powertools import Logger

logger = Logger(level="INFO")

class BaseLLM(ABC):
    @abstractmethod
    def prepare_messages(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Prepare messages for the specific LLM format"""
        pass
    
    @abstractmethod
    def convert_to_json(self, response: Any) -> Dict:
        """Convert LLM response to standardized JSON format"""
        pass
    
    @abstractmethod
    def generate_response(self, system: str, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Generate response from the LLM"""
        pass
