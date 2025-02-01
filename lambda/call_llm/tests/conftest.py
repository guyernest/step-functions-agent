# tests/conftest.py
import os
import sys
import pytest

# Add Lambda function directory to Python path
import sys
import os

# Get the absolute path of the lambda_layer
LAMBDA_LAYER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../lambda_layer/python"))
# Add the layer path to sys.path for local testing
sys.path.insert(0, LAMBDA_LAYER_PATH)

lambda_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../functions/bedrock")
sys.path.append(lambda_dir)
