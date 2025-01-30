# call_llm/handlers/__init__.py
from .claude_lambda import lambda_handler as claude_handler
from .openai_lambda import lambda_handler as openai_handler
from .bedrock_lambda import lambda_handler as bedrock_handler
from .gemini_lambda import lambda_handler as gemini_handler