# tests/conftest.py
import os
import sys
import pytest

# Add Lambda function directory to Python path
lambda_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lambda/call_llm")
sys.path.append(lambda_dir)
