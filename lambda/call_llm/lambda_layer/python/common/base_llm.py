from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
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
    
    # Defensive Programming Utilities
    def safe_get_nested(self, data: Any, path: str, default: Any = None) -> Any:
        """Safely get nested field from data structure using dot notation path
        
        Args:
            data: The data structure to navigate
            path: Dot-notation path (e.g., 'choices.0.message.content')
            default: Default value if path doesn't exist
            
        Returns:
            Value at path or default if not found
        """
        try:
            current = data
            for key in path.split('.'):
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    idx = int(key)
                    current = current[idx] if 0 <= idx < len(current) else None
                elif hasattr(current, key):
                    current = getattr(current, key)
                else:
                    logger.warning(f"Path segment '{key}' not found in {type(current).__name__}")
                    return default
                    
                if current is None:
                    return default
                    
            return current
        except (KeyError, IndexError, AttributeError, ValueError) as e:
            logger.warning(f"Failed to get nested field '{path}': {str(e)}")
            return default
    
    def validate_required_fields(self, data: Any, required_fields: List[str], context: str = "") -> Dict[str, bool]:
        """Validate that required fields exist in data structure
        
        Args:
            data: Data structure to validate
            required_fields: List of dot-notation paths that must exist
            context: Context description for logging
            
        Returns:
            Dict mapping field paths to validation results
        """
        results = {}
        missing_fields = []
        
        for field_path in required_fields:
            value = self.safe_get_nested(data, field_path)
            is_valid = value is not None
            results[field_path] = is_valid
            
            if not is_valid:
                missing_fields.append(field_path)
        
        if missing_fields:
            logger.warning(f"Missing required fields in {context}: {missing_fields}")
        
        return results
    
    def safe_extract_field(self, data: Any, field_paths: List[str], default: Any = None) -> Any:
        """Try multiple field paths and return first valid value
        
        Args:
            data: Data structure to search
            field_paths: List of alternative paths to try
            default: Default value if none found
            
        Returns:
            First valid value found or default
        """
        for path in field_paths:
            value = self.safe_get_nested(data, path)
            if value is not None:
                return value
        
        logger.info(f"No valid value found in paths {field_paths}, using default: {default}")
        return default
    
    def detect_response_format(self, response: Any) -> Dict[str, Any]:
        """Detect response format and version indicators
        
        Args:
            response: LLM response to analyze
            
        Returns:
            Dict with format detection results
        """
        format_info = {
            'has_choices': self.safe_get_nested(response, 'choices') is not None,
            'has_candidates': self.safe_get_nested(response, 'candidates') is not None,
            'has_content': self.safe_get_nested(response, 'content') is not None,
            'model_info': self.safe_extract_field(response, ['model', 'model_id', 'modelId']),
            'api_version': self.safe_extract_field(response, ['api_version', 'version']),
            'response_type': type(response).__name__
        }
        
        logger.info(f"Detected response format: {format_info}")
        return format_info
    
    def create_error_response(self, error_msg: str, context: Dict = None) -> Dict:
        """Create standardized error response
        
        Args:
            error_msg: Error message
            context: Additional context information
            
        Returns:
            Standardized error response dict
        """
        # Get model from context or instance variable if available
        model_id = 'unknown'
        if context and 'model' in context:
            model_id = context['model']
        elif hasattr(self, 'model_id'):
            model_id = self.model_id
            
        error_response = {
            'message': {
                'role': 'assistant',
                'content': f"Error: {error_msg}"
            },
            'function_calls': [],
            'metadata': {
                'model': model_id,
                'stop_reason': 'error',
                'usage': {
                    'input_tokens': 0,
                    'output_tokens': 0
                },
                'error': error_msg
            }
        }
        
        if context:
            error_response['metadata']['error_context'] = context
            
        logger.error(f"Created error response: {error_msg}", extra={'context': context})
        return error_response
