"""
Test script for the enhanced GraphQL tool with dynamic endpoint selection.
This script validates that the tool can handle multiple GraphQL endpoints.
"""

import json
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the AWS SDK and tool_secrets
class MockToolSecrets:
    def get_tool_secrets(self, tool_name):
        """Mock tool secrets for testing."""
        if tool_name == 'graphql-interface':
            return {
                'LogisticZ': json.dumps({
                    'endpoint': 'https://logisticz-api.example.com/graphql',
                    'api_key': 'test-api-key-logisticz'
                }),
                'CustomerService': json.dumps({
                    'endpoint': 'https://customer-api.example.com/graphql',
                    'api_key': 'test-api-key-customer',
                    'headers': {
                        'X-Custom-Header': 'CustomValue'
                    }
                })
            }
        return {}

    def get_secret_value(self, tool_name, key, default=None):
        secrets = self.get_tool_secrets(tool_name)
        return secrets.get(key, default)

# Replace the import with our mock
sys.modules['tool_secrets'] = MockToolSecrets()

# Now import the module to test
from index import get_graphql_client, lambda_handler

def test_get_graphql_client():
    """Test that we can get GraphQL clients for different endpoints."""
    print("Testing get_graphql_client...")

    try:
        # Test getting a client for LogisticZ
        client = get_graphql_client('LogisticZ')
        assert client.endpoint == 'https://logisticz-api.example.com/graphql'
        print("✓ Successfully created client for LogisticZ")

        # Test getting a client for CustomerService
        client = get_graphql_client('CustomerService')
        assert client.endpoint == 'https://customer-api.example.com/graphql'
        print("✓ Successfully created client for CustomerService")

        # Test invalid ID
        try:
            client = get_graphql_client('InvalidID')
            print("✗ Should have raised error for invalid ID")
        except ValueError as e:
            if "not found" in str(e):
                print("✓ Correctly raised error for invalid ID")
            else:
                print(f"✗ Unexpected error: {e}")

    except Exception as e:
        print(f"✗ Test failed: {e}")

def test_lambda_handler():
    """Test the lambda_handler with different tool calls."""
    print("\nTesting lambda_handler...")

    # Test get_graphql_schema tool
    event = {
        'name': 'get_graphql_schema',
        'id': 'test-123',
        'input': {
            'graphql_id': 'LogisticZ'
        }
    }

    result = lambda_handler(event, {})
    assert result['type'] == 'tool_result'
    assert result['name'] == 'get_graphql_schema'
    assert result['tool_use_id'] == 'test-123'
    print("✓ get_graphql_schema tool works")

    # Test generate_query_prompt tool
    event = {
        'name': 'generate_query_prompt',
        'id': 'test-456',
        'input': {
            'graphql_id': 'CustomerService',
            'description': 'Get all customers with their orders'
        }
    }

    result = lambda_handler(event, {})
    assert result['type'] == 'tool_result'
    assert result['name'] == 'generate_query_prompt'
    print("✓ generate_query_prompt tool works")

    # Test execute_graphql_query tool
    event = {
        'name': 'execute_graphql_query',
        'id': 'test-789',
        'input': {
            'graphql_id': 'LogisticZ',
            'graphql_query': 'query { test }'
        }
    }

    result = lambda_handler(event, {})
    assert result['type'] == 'tool_result'
    assert result['name'] == 'execute_graphql_query'
    print("✓ execute_graphql_query tool works")

    # Test missing graphql_id
    event = {
        'name': 'get_graphql_schema',
        'id': 'test-error',
        'input': {}
    }

    result = lambda_handler(event, {})
    content = result.get('content', '')
    assert 'graphql_id parameter is required' in content
    print("✓ Correctly handles missing graphql_id")

if __name__ == "__main__":
    print("Running GraphQL Dynamic Endpoints Tests")
    print("=" * 50)

    test_get_graphql_client()
    test_lambda_handler()

    print("\n" + "=" * 50)
    print("All tests completed!")