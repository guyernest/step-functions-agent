"""
Tool Secrets Helper Module (Python)
Provides easy access to tool secrets from the consolidated secret
"""

import json
import boto3
import os
from typing import Dict, Optional, Any
from functools import lru_cache

# Initialize AWS clients
secretsmanager = boto3.client('secretsmanager')


@lru_cache(maxsize=1)
def get_consolidated_secret_name() -> str:
    """Get the consolidated secret name from environment or default"""
    env_name = os.environ.get('ENVIRONMENT', 'prod')
    return os.environ.get('CONSOLIDATED_SECRET_NAME', f'/ai-agent/tool-secrets/{env_name}')


@lru_cache(maxsize=1)
def get_all_secrets() -> Dict[str, Dict[str, str]]:
    """
    Get all secrets from the consolidated secret.
    Results are cached for the Lambda execution context.
    
    Returns:
        Dict mapping tool names to their secrets
    """
    secret_name = get_consolidated_secret_name()
    
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving consolidated secrets: {e}")
        return {}


def get_tool_secrets(tool_name: str) -> Dict[str, str]:
    """
    Get secrets for a specific tool from the consolidated secret.
    
    Args:
        tool_name: Name of the tool (e.g., 'google-maps', 'execute-code')
    
    Returns:
        Dict of secret key-value pairs for the tool
    """
    all_secrets = get_all_secrets()
    return all_secrets.get(tool_name, {})


def get_secret_value(tool_name: str, secret_key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a specific secret value for a tool.
    
    Args:
        tool_name: Name of the tool
        secret_key: Key of the secret (e.g., 'GOOGLE_MAPS_API_KEY')
        default: Default value if secret not found
    
    Returns:
        Secret value or default
    """
    tool_secrets = get_tool_secrets(tool_name)
    value = tool_secrets.get(secret_key, default)
    
    # Check if it's a placeholder
    if value and value.startswith('PLACEHOLDER_'):
        print(f"Warning: Using placeholder value for {tool_name}/{secret_key}")
        return default
    
    return value


# Backward compatibility functions for existing tools
def get_legacy_secret(secret_path: str) -> Dict[str, str]:
    """
    Get secrets from a legacy individual secret path.
    This function provides backward compatibility for tools
    that haven't been migrated yet.
    
    Args:
        secret_path: Legacy secret path (e.g., '/ai-agent/tools/google-maps/prod')
    
    Returns:
        Dict of secret key-value pairs
    """
    try:
        # First try the legacy path
        response = secretsmanager.get_secret_value(SecretId=secret_path)
        return json.loads(response['SecretString'])
    except secretsmanager.exceptions.ResourceNotFoundException:
        # Fall back to consolidated secret
        # Extract tool name from path
        parts = secret_path.split('/')
        if 'tools' in parts:
            tool_idx = parts.index('tools')
            if tool_idx + 1 < len(parts):
                tool_name = parts[tool_idx + 1]
                return get_tool_secrets(tool_name)
        return {}
    except Exception as e:
        print(f"Error retrieving legacy secret from {secret_path}: {e}")
        return {}


# Environment variable helper for tools that use env vars
def load_secrets_to_env(tool_name: str) -> None:
    """
    Load tool secrets into environment variables.
    Useful for tools that expect secrets in env vars.
    
    Args:
        tool_name: Name of the tool
    """
    secrets = get_tool_secrets(tool_name)
    for key, value in secrets.items():
        if not value.startswith('PLACEHOLDER_'):
            os.environ[key] = value


# Clear cache function for testing
def clear_cache() -> None:
    """Clear the cached secrets (useful for testing)"""
    get_all_secrets.cache_clear()
    get_consolidated_secret_name.cache_clear()