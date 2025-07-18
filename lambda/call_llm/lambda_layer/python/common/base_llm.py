from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging
import json

# Set up standard Python logging with JSON format similar to Lambda Powertools
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'level': record.levelname,
            'location': f"{record.funcName}:{record.lineno}",
            'message': record.getMessage(),
            'timestamp': self.formatTime(record, self.datefmt),
            'service': 'shared-llm'
        }
        return json.dumps(log_obj)

# Create logger with JSON formatting
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Create a dummy tracer that does nothing to avoid breaking existing code
class DummyTracer:
    def capture_lambda_handler(self, func):
        """Dummy decorator that just returns the function unchanged"""
        return func

tracer = DummyTracer()

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
