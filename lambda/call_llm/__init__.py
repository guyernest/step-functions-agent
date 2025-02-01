# lambda/call_llm/__init__.py
import os
import sys

# Add the package directory to the Python path
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

# Define the package name
__package__ = 'call_llm'

# Import your submodules
from lambda_layer.python import common
from functions import bedrock, anthropic, openai
from functions.bedrock import bedrock_handler

# Make the imports available at the package level
__all__ = [
    'common', 
    'bedrock', 
    'bedrock_handler', 
    'anthropic', 
    'openai'
]