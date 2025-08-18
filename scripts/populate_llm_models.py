#!/usr/bin/env python3
"""
Script to populate the LLMModels DynamoDB table with initial data.
"""

import boto3
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
import os

# Initialize DynamoDB client
# Use AWS_DEFAULT_REGION if set, otherwise default to us-west-2
region = os.environ.get('AWS_DEFAULT_REGION', 'us-west-2')

if os.environ.get('AWS_PROFILE'):
    session = boto3.Session(profile_name=os.environ['AWS_PROFILE'], region_name=region)
    dynamodb = session.resource('dynamodb')
else:
    dynamodb = boto3.resource('dynamodb', region_name=region)

table = dynamodb.Table('LLMModels-prod')

def create_model_item(provider: str, model_id: str, display_name: str, 
                      input_price: float, output_price: float,
                      max_tokens: int = 4096, supports_tools: bool = True,
                      supports_vision: bool = False, is_default: bool = False) -> Dict[str, Any]:
    """Create a model item for DynamoDB."""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    return {
        'pk': f"{provider}#{model_id}",
        'provider': provider,
        'model_id': model_id,
        'display_name': display_name,
        'input_price_per_1k': Decimal(str(input_price)),
        'output_price_per_1k': Decimal(str(output_price)),
        'max_tokens': max_tokens,
        'supports_tools': supports_tools,
        'supports_vision': supports_vision,
        'is_active': 'true',  # String for GSI range key
        'is_default': is_default,
        'created_at': timestamp,
        'updated_at': timestamp
    }

# Define all models with their configurations
MODELS_DATA = [
    # Anthropic models
    {
        'provider': 'anthropic',
        'model_id': 'claude-3-7-sonnet-latest',
        'display_name': 'Claude 3.7 Sonnet',
        'input_price': 3.00,
        'output_price': 15.00,
        'max_tokens': 8192,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': True
    },
    {
        'provider': 'anthropic',
        'model_id': 'claude-3-5-sonnet-20241022',
        'display_name': 'Claude 3.5 Sonnet',
        'input_price': 3.00,
        'output_price': 15.00,
        'max_tokens': 8192,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': True
    },
    {
        'provider': 'anthropic',
        'model_id': 'claude-3-5-haiku-20241022',
        'display_name': 'Claude 3.5 Haiku',
        'input_price': 0.80,
        'output_price': 4.00,
        'max_tokens': 8192,
        'supports_tools': True,
        'supports_vision': False,
        'is_default': False
    },
    {
        'provider': 'anthropic',
        'model_id': 'claude-3-opus-20240229',
        'display_name': 'Claude 3 Opus',
        'input_price': 15.00,
        'output_price': 75.00,
        'max_tokens': 4096,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    
    # OpenAI models
    {
        'provider': 'openai',
        'model_id': 'gpt-4o',
        'display_name': 'GPT-4o',
        'input_price': 2.50,
        'output_price': 10.00,
        'max_tokens': 128000,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': True
    },
    {
        'provider': 'openai',
        'model_id': 'gpt-4o-mini',
        'display_name': 'GPT-4o Mini',
        'input_price': 0.15,
        'output_price': 0.60,
        'max_tokens': 128000,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    {
        'provider': 'openai',
        'model_id': 'gpt-4-turbo-2024-11-20',
        'display_name': 'GPT-4 Turbo',
        'input_price': 10.00,
        'output_price': 30.00,
        'max_tokens': 128000,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    {
        'provider': 'openai',
        'model_id': 'o1-preview',
        'display_name': 'OpenAI o1 Preview',
        'input_price': 15.00,
        'output_price': 60.00,
        'max_tokens': 128000,
        'supports_tools': False,
        'supports_vision': False,
        'is_default': False
    },
    {
        'provider': 'openai',
        'model_id': 'o1-mini',
        'display_name': 'OpenAI o1 Mini',
        'input_price': 3.00,
        'output_price': 12.00,
        'max_tokens': 128000,
        'supports_tools': False,
        'supports_vision': False,
        'is_default': False
    },
    
    # Google models
    {
        'provider': 'google',
        'model_id': 'gemini-2.0-flash-exp',
        'display_name': 'Gemini 2.0 Flash',
        'input_price': 0.10,
        'output_price': 0.40,
        'max_tokens': 1048576,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': True
    },
    {
        'provider': 'google',
        'model_id': 'gemini-1.5-pro-002',
        'display_name': 'Gemini 1.5 Pro',
        'input_price': 1.25,
        'output_price': 5.00,
        'max_tokens': 2097152,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    {
        'provider': 'google',
        'model_id': 'gemini-1.5-flash-002',
        'display_name': 'Gemini 1.5 Flash',
        'input_price': 0.075,
        'output_price': 0.30,
        'max_tokens': 1048576,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    
    # Amazon Bedrock models (using Bearer token authentication)
    # Note: Provider 'amazon' or 'bedrock' both map to AWS_BEARER_TOKEN_BEDROCK
    # IMPORTANT: Use inference profile IDs with region prefix (eu., us., etc.)
    {
        'provider': 'bedrock',  # Can also use 'amazon' - both work
        'model_id': 'eu.amazon.nova-pro-v1:0',  # EU region inference profile
        'display_name': 'Amazon Nova Pro (EU)',
        'input_price': 0.80,
        'output_price': 3.20,
        'max_tokens': 300000,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': True
    },
    {
        'provider': 'bedrock',
        'model_id': 'eu.amazon.nova-lite-v1:0',  # EU region inference profile
        'display_name': 'Amazon Nova Lite (EU)',
        'input_price': 0.06,
        'output_price': 0.24,
        'max_tokens': 300000,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    {
        'provider': 'bedrock',
        'model_id': 'eu.amazon.nova-micro-v1:0',  # EU region inference profile
        'display_name': 'Amazon Nova Micro (EU)',
        'input_price': 0.035,
        'output_price': 0.14,
        'max_tokens': 128000,
        'supports_tools': False,
        'supports_vision': False,
        'is_default': False
    },
    
    # Bedrock-hosted Anthropic models (using Bearer token authentication)
    {
        'provider': 'bedrock',
        'model_id': 'us.anthropic.claude-3-5-haiku-20241022-v1:0',
        'display_name': 'Claude 3.5 Haiku (Bedrock)',
        'input_price': 1.00,
        'output_price': 5.00,
        'max_tokens': 200000,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    {
        'provider': 'bedrock',
        'model_id': 'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
        'display_name': 'Claude 3.5 Sonnet (Bedrock)',
        'input_price': 3.00,
        'output_price': 15.00,
        'max_tokens': 200000,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    
    # xAI models
    {
        'provider': 'xai',
        'model_id': 'grok-2-1212',
        'display_name': 'Grok 2',
        'input_price': 2.00,
        'output_price': 10.00,
        'max_tokens': 131072,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': True
    },
    {
        'provider': 'xai',
        'model_id': 'grok-2-vision-1212',
        'display_name': 'Grok 2 Vision',
        'input_price': 2.00,
        'output_price': 10.00,
        'max_tokens': 32768,
        'supports_tools': True,
        'supports_vision': True,
        'is_default': False
    },
    
    # DeepSeek models (for future)
    {
        'provider': 'deepseek',
        'model_id': 'deepseek-chat',
        'display_name': 'DeepSeek Chat',
        'input_price': 0.14,
        'output_price': 0.28,
        'max_tokens': 64000,
        'supports_tools': True,
        'supports_vision': False,
        'is_default': True
    },
    {
        'provider': 'deepseek',
        'model_id': 'deepseek-reasoner',
        'display_name': 'DeepSeek Reasoner',
        'input_price': 0.55,
        'output_price': 2.19,
        'max_tokens': 64000,
        'supports_tools': True,
        'supports_vision': False,
        'is_default': False
    }
]

def populate_table():
    """Populate the DynamoDB table with model data."""
    print("Starting to populate LLMModels table...")
    
    # Create items for batch writing
    with table.batch_writer() as batch:
        for model_data in MODELS_DATA:
            item = create_model_item(**model_data)
            batch.put_item(Item=item)
            print(f"Added: {model_data['provider']} - {model_data['display_name']}")
    
    print(f"\nSuccessfully populated {len(MODELS_DATA)} models to LLMModels-prod table")
    
    # Verify by counting items
    response = table.scan()
    print(f"Table now contains {response['Count']} items")

if __name__ == "__main__":
    populate_table()