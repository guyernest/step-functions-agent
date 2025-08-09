# tests/conftest.py
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure the lambda_layer/python directory is in sys.path
LAMBDA_LAYER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../lambda_layer/python")
)
sys.path.insert(0, LAMBDA_LAYER_PATH)

# Ensure the functions directory (Lambda handlers) is in sys.path
FUNCTIONS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../functions")
)
sys.path.insert(0, FUNCTIONS_DIR)

# Print for debugging
print("Updated sys.path for pytest:")
for p in sys.path:
    print(p)

import sys
import importlib

print("Checking module availability:")
try:
    common = importlib.import_module("common.base_llm")
    print("✅ common.base_llm loaded successfully")
except ModuleNotFoundError:
    print("❌ Module common.base_llm not found!")

# Global fixture to mock AWS Secrets Manager for all tests
@pytest.fixture(autouse=True)
def mock_aws_secrets():
    """Automatically mock AWS Secrets Manager for all tests"""
    with patch('common.config.boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock the get_secret_value response
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key", "XAI_API_KEY": "test-key", "DEEPSEEK_API_KEY": "test-key"}'
        }
        
        yield mock_client