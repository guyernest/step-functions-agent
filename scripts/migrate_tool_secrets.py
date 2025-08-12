#!/usr/bin/env python3
"""
Tool Secrets Migration Script
Discovers existing tool secrets and migrates them to the consolidated secret
"""

import json
import boto3
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from glob import glob
from dotenv import load_dotenv

# Initialize AWS clients
secretsmanager = boto3.client('secretsmanager')
lambda_client = boto3.client('lambda')


def discover_env_files() -> Dict[str, Path]:
    """
    Discover .env files in the project
    Returns a mapping of tool names to their .env file paths
    """
    print("🔍 Discovering .env files...")
    
    env_files = {}
    
    # Look for .env files in the project root
    root_path = Path(__file__).parent.parent
    
    # Pattern variations to check
    patterns = [
        '.env.*',  # .env.google_maps, .env.execute_code, etc.
        'lambda/tools/*/.env*',  # Tool-specific .env files
    ]
    
    for pattern in patterns:
        for env_file in glob(str(root_path / pattern)):
            env_path = Path(env_file)
            if env_path.is_file():
                # Extract tool name from filename
                filename = env_path.name
                if filename.startswith('.env.'):
                    tool_name = filename.replace('.env.', '').replace('_', '-')
                    env_files[tool_name] = env_path
                    print(f"  Found: {tool_name} -> {env_path}")
    
    return env_files


def load_secrets_from_env(env_path: Path) -> Dict[str, str]:
    """
    Load secrets from an .env file
    """
    secrets = {}
    
    # Clear existing environment variables to avoid conflicts
    temp_env = os.environ.copy()
    
    # Load the .env file
    load_dotenv(env_path, override=True)
    
    # Common patterns for API keys
    key_patterns = [
        'API_KEY', 'SECRET', 'TOKEN', 'PASSWORD',
        'CLIENT_ID', 'CLIENT_SECRET', 'ACCESS_KEY'
    ]
    
    # Extract relevant environment variables
    for key, value in os.environ.items():
        if any(pattern in key.upper() for pattern in key_patterns):
            if key not in temp_env or temp_env[key] != value:
                secrets[key] = value
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(temp_env)
    
    return secrets


def discover_existing_secrets(env_name: str) -> Dict[str, Dict[str, str]]:
    """
    Discover existing secrets in AWS Secrets Manager
    """
    print(f"🔍 Discovering existing secrets in AWS Secrets Manager for {env_name}...")
    
    existing_secrets = {}
    
    # Common tool secret patterns
    patterns = [
        '/ai-agent/tools/',
        '/ai-agent/tool-',
    ]
    
    try:
        # List all secrets
        paginator = secretsmanager.get_paginator('list_secrets')
        
        for page in paginator.paginate():
            for secret in page.get('SecretList', []):
                secret_name = secret['Name']
                
                # Check if it matches our tool patterns
                if any(pattern in secret_name for pattern in patterns):
                    # Extract tool name
                    parts = secret_name.split('/')
                    if 'tools' in parts or 'tool-' in secret_name:
                        try:
                            # Get secret value
                            response = secretsmanager.get_secret_value(SecretId=secret_name)
                            secret_data = json.loads(response['SecretString'])
                            
                            # Determine tool name
                            if 'tools' in parts:
                                tool_idx = parts.index('tools')
                                if tool_idx + 1 < len(parts):
                                    tool_name = parts[tool_idx + 1]
                                    existing_secrets[tool_name] = secret_data
                                    print(f"  Found: {tool_name} -> {secret_name}")
                            elif 'tool-' in secret_name:
                                tool_name = secret_name.split('tool-')[1].split('/')[0]
                                existing_secrets[tool_name] = secret_data
                                print(f"  Found: {tool_name} -> {secret_name}")
                        except Exception as e:
                            print(f"  ⚠️  Error reading {secret_name}: {e}")
    
    except Exception as e:
        print(f"  ⚠️  Error listing secrets: {e}")
    
    return existing_secrets


def merge_secrets(
    env_secrets: Dict[str, Dict[str, str]], 
    aws_secrets: Dict[str, Dict[str, str]]
) -> Dict[str, Dict[str, str]]:
    """
    Merge secrets from .env files and AWS Secrets Manager
    AWS secrets take precedence over .env files
    """
    merged = {}
    
    # Start with env file secrets
    for tool_name, secrets in env_secrets.items():
        merged[tool_name] = secrets.copy()
    
    # Override with AWS secrets
    for tool_name, secrets in aws_secrets.items():
        if tool_name in merged:
            merged[tool_name].update(secrets)
        else:
            merged[tool_name] = secrets
    
    return merged


def update_consolidated_secret(
    env_name: str, 
    tool_secrets: Dict[str, Dict[str, str]],
    dry_run: bool = False
) -> bool:
    """
    Update the consolidated secret with discovered secrets
    """
    secret_name = f"/ai-agent/tool-secrets/{env_name}"
    
    print(f"\n📦 Updating consolidated secret: {secret_name}")
    
    if dry_run:
        print("  🔍 DRY RUN - Would update with:")
        for tool_name, secrets in tool_secrets.items():
            print(f"    {tool_name}:")
            for key in secrets.keys():
                print(f"      - {key}")
        return True
    
    try:
        # Try to get existing consolidated secret
        try:
            response = secretsmanager.get_secret_value(SecretId=secret_name)
            existing_data = json.loads(response['SecretString'])
            print(f"  ✅ Found existing consolidated secret")
        except secretsmanager.exceptions.ResourceNotFoundException:
            existing_data = {}
            print(f"  ℹ️  Consolidated secret doesn't exist yet")
        
        # Merge with existing data
        for tool_name, secrets in tool_secrets.items():
            if tool_name not in existing_data:
                existing_data[tool_name] = {}
            
            # Only update non-placeholder values
            for key, value in secrets.items():
                if not value.startswith('PLACEHOLDER_'):
                    existing_data[tool_name][key] = value
                    print(f"  ✅ Updated {tool_name}/{key}")
        
        # Update the secret
        try:
            secretsmanager.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(existing_data, indent=2)
            )
            print(f"  ✅ Successfully updated consolidated secret")
        except secretsmanager.exceptions.ResourceNotFoundException:
            print(f"  ⚠️  Consolidated secret doesn't exist. Please deploy SharedInfrastructureStack first.")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating secret: {e}")
        return False


def register_tools_in_table(
    env_name: str, 
    tool_secrets: Dict[str, Dict[str, str]],
    dry_run: bool = False
) -> bool:
    """
    Register tools in the ToolSecrets DynamoDB table
    """
    print(f"\n📝 Registering tools in ToolSecrets table...")
    
    if dry_run:
        print("  🔍 DRY RUN - Would register:")
        for tool_name in tool_secrets.keys():
            print(f"    - {tool_name}")
        return True
    
    try:
        # Invoke the secret structure manager Lambda
        lambda_function_name = f"tool-secrets-manager-{env_name}"
        
        for tool_name, secrets in tool_secrets.items():
            payload = {
                "operation": "register_tool",
                "tool_name": tool_name,
                "secret_keys": list(secrets.keys()),
                "description": f"Migrated secrets for {tool_name}"
            }
            
            try:
                response = lambda_client.invoke(
                    FunctionName=lambda_function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                result = json.loads(response['Payload'].read())
                if result.get('statusCode') == 200:
                    print(f"  ✅ Registered {tool_name}")
                else:
                    print(f"  ⚠️  Failed to register {tool_name}: {result.get('body')}")
                    
            except lambda_client.exceptions.ResourceNotFoundException:
                print(f"  ⚠️  Lambda {lambda_function_name} not found. Deploy SharedInfrastructureStack first.")
                return False
            except Exception as e:
                print(f"  ⚠️  Error registering {tool_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error registering tools: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Migrate tool secrets to consolidated secret')
    parser.add_argument('--env', default='prod', help='Environment name (default: prod)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--from-env-files', action='store_true', help='Load secrets from .env files')
    parser.add_argument('--from-aws', action='store_true', help='Load secrets from existing AWS Secrets Manager')
    parser.add_argument('--register-only', action='store_true', help='Only register tools, don\'t update secrets')
    
    args = parser.parse_args()
    
    # If neither source is specified, use both
    if not args.from_env_files and not args.from_aws:
        args.from_env_files = True
        args.from_aws = True
    
    print(f"🚀 Tool Secrets Migration Script")
    print(f"   Environment: {args.env}")
    print(f"   Dry Run: {args.dry_run}")
    print()
    
    # Collect secrets from various sources
    all_secrets = {}
    
    if args.from_env_files:
        # Discover and load from .env files
        env_files = discover_env_files()
        
        if env_files:
            print(f"\n📄 Loading secrets from .env files...")
            env_secrets = {}
            for tool_name, env_path in env_files.items():
                secrets = load_secrets_from_env(env_path)
                if secrets:
                    env_secrets[tool_name] = secrets
                    print(f"  ✅ Loaded {len(secrets)} secrets for {tool_name}")
            
            all_secrets.update(env_secrets)
    
    if args.from_aws:
        # Discover existing AWS secrets
        aws_secrets = discover_existing_secrets(args.env)
        if aws_secrets:
            all_secrets = merge_secrets(all_secrets, aws_secrets)
    
    if not all_secrets:
        print("\n⚠️  No secrets found to migrate")
        return 1
    
    print(f"\n📊 Summary:")
    print(f"   Tools found: {len(all_secrets)}")
    total_secrets = sum(len(secrets) for secrets in all_secrets.values())
    print(f"   Total secrets: {total_secrets}")
    
    if not args.register_only:
        # Update consolidated secret
        if not update_consolidated_secret(args.env, all_secrets, args.dry_run):
            return 1
    
    # Register tools in DynamoDB
    if not register_tools_in_table(args.env, all_secrets, args.dry_run):
        return 1
    
    if not args.dry_run:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Deploy the SharedInfrastructureStack if not already deployed")
        print("2. Update tool Lambda functions to use the consolidated secret")
        print("3. Test each tool to ensure secrets are accessible")
        print("4. Remove old individual secrets once confirmed working")
    else:
        print("\n✅ Dry run completed. Run without --dry-run to apply changes.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())