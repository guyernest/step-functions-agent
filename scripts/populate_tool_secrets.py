#!/usr/bin/env python3
"""
Script to populate the ToolSecrets DynamoDB table with tool secret requirements.
This script only populates the metadata about which secrets each tool needs,
not the actual secret values (which are managed separately through AWS Secrets Manager).
"""

import boto3
import json
from datetime import datetime
from typing import List, Dict, Any
import os
import sys

def load_tool_secrets_config(config_file: str = 'data/tool_secrets_config.json') -> List[Dict[str, Any]]:
    """Load tool secrets configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('tools', [])
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)

def populate_tool_secrets_table(tools: List[Dict[str, Any]], profile: str = None, region: str = 'us-west-2'):
    """Populate the ToolSecrets DynamoDB table with tool secret requirements."""
    
    # Initialize DynamoDB client
    if profile:
        session = boto3.Session(profile_name=profile, region_name=region)
        dynamodb = session.resource('dynamodb')
    else:
        dynamodb = boto3.resource('dynamodb', region_name=region)
    
    table = dynamodb.Table('ToolSecrets-prod')
    
    # Add each tool's secret requirements
    success_count = 0
    error_count = 0
    
    for tool in tools:
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            item = {
                'tool_name': tool['tool_name'],
                'secret_keys': set(tool['secret_keys']),  # Using SS (String Set) type
                'description': tool.get('description', f"Secrets for {tool['tool_name']}"),
                'registered_at': timestamp,
                'environment': 'prod'
            }
            
            # Put item into DynamoDB
            table.put_item(Item=item)
            print(f"✓ Added tool secrets config for: {tool['tool_name']}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Error adding {tool['tool_name']}: {e}")
            error_count += 1
    
    print(f"\n{'='*50}")
    print(f"Summary: {success_count} tools added, {error_count} errors")
    
    if error_count > 0:
        sys.exit(1)

def verify_table_exists(profile: str = None, region: str = 'us-west-2'):
    """Verify that the ToolSecrets table exists."""
    try:
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
            dynamodb = session.client('dynamodb')
        else:
            dynamodb = boto3.client('dynamodb', region_name=region)
        
        response = dynamodb.describe_table(TableName='ToolSecrets-prod')
        print(f"✓ Found ToolSecrets-prod table (Status: {response['Table']['TableStatus']})")
        return True
    except dynamodb.exceptions.ResourceNotFoundException:
        print("✗ Error: ToolSecrets-prod table not found.")
        print("  Please ensure the SharedInfrastructureStack has been deployed.")
        return False
    except Exception as e:
        print(f"✗ Error checking table: {e}")
        return False

def main():
    """Main function to populate tool secrets."""
    
    # Get AWS profile from environment or command line
    profile = os.environ.get('AWS_PROFILE')
    # Default to eu-west-1 for CGI-PoC, us-west-2 for others
    default_region = 'eu-west-1' if profile == 'CGI-PoC' else 'us-west-2'
    region = os.environ.get('AWS_DEFAULT_REGION', default_region)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("Usage: python populate_tool_secrets.py [profile] [region]")
            print("\nPopulates the ToolSecrets DynamoDB table with tool secret requirements.")
            print("\nOptions:")
            print("  profile  AWS profile to use (default: from AWS_PROFILE env var)")
            print("  region   AWS region (default: eu-west-1 for CGI-PoC, us-west-2 for others)")
            print("\nExample:")
            print("  python populate_tool_secrets.py CGI-PoC eu-west-1")
            sys.exit(0)
        
        profile = sys.argv[1]
        # Update default region based on the profile argument
        if profile == 'CGI-PoC' and len(sys.argv) <= 2:
            region = 'eu-west-1'
        
        if len(sys.argv) > 2:
            region = sys.argv[2]
    
    print(f"Tool Secrets Table Population Script")
    print(f"{'='*50}")
    print(f"Profile: {profile or 'default'}")
    print(f"Region: {region}")
    print(f"{'='*50}\n")
    
    # Verify table exists
    if not verify_table_exists(profile, region):
        sys.exit(1)
    
    print()
    
    # Load configuration
    tools = load_tool_secrets_config()
    print(f"Loaded {len(tools)} tool configurations from config file\n")
    
    # Populate the table
    populate_tool_secrets_table(tools, profile, region)
    
    print("\n✓ Tool secrets configuration complete!")
    print("\nNote: This script only configures which secrets each tool needs.")
    print("Actual secret values must be set through the UI or AWS Secrets Manager.")

if __name__ == "__main__":
    main()