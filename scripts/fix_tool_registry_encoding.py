#!/usr/bin/env python3
"""
Fix double JSON encoding in Tool Registry

This script fixes tools that have been double-encoded during registration.
"""

import boto3
import json

def fix_tool_registry_encoding(env_name: str = "prod"):
    """Fix double JSON encoding in tool registry entries"""
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(f"ToolRegistry-{env_name}")
    
    # Scan all tools
    response = table.scan()
    tools = response['Items']
    
    print(f"Found {len(tools)} tools in registry")
    
    fixed_count = 0
    
    for tool in tools:
        tool_name = tool.get('tool_name', 'UNKNOWN')
        
        # Check if input_schema is double-encoded
        input_schema_str = tool.get('input_schema', '')
        
        # Skip if not a string (might be dict from scan)
        if not isinstance(input_schema_str, str):
            continue
            
        try:
            # Check if it starts and ends with quotes inside the string value
            if input_schema_str.startswith('"{') and input_schema_str.endswith('}"'):
                # Double-encoded! Parse to get the actual schema
                actual_schema = json.loads(input_schema_str)
                
                print(f"Fixing double-encoded schema for tool: {tool_name}")
                print(f"  Before: {input_schema_str[:50]}...")
                print(f"  After: {actual_schema[:50]}...")
                
                # Update the item with properly encoded schema
                table.update_item(
                    Key={'tool_name': tool_name},
                    UpdateExpression='SET input_schema = :schema',
                    ExpressionAttributeValues={
                        ':schema': actual_schema
                    }
                )
                
                fixed_count += 1
                
        except json.JSONDecodeError:
            print(f"Tool {tool_name} has invalid JSON in input_schema")
        except Exception as e:
            print(f"Error processing tool {tool_name}: {e}")
    
    print(f"\nFixed {fixed_count} tools with double-encoded schemas")

if __name__ == "__main__":
    import sys
    
    env = sys.argv[1] if len(sys.argv) > 1 else "prod"
    fix_tool_registry_encoding(env)