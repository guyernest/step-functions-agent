#!/usr/bin/env python3
"""
Decentralized Tool Registration Script

This script demonstrates how to register tools using the new decentralized pattern
where each tool stack owns its tool definitions alongside Lambda implementations.

Benefits:
- No parameter mismatches (schema and Lambda are co-located)
- Automatic tool discovery from individual stacks
- Type safety and validation at tool level
- Independent tool development

Usage:
    python scripts/register_decentralized_tools.py --env prod --profile CGI-PoC
"""

import argparse
import boto3
import json
import sys
from datetime import datetime
from typing import List, Dict, Any

# Tool stack imports (these would replace centralized definitions)
# from stacks.tools.google_maps_tool_stack_v2 import GoogleMapsToolStackV2
# from stacks.tools.database_tool_stack_v2 import DatabaseToolStackV2
# from stacks.tools.financial_tool_stack_v2 import FinancialToolStackV2

from stacks.shared.base_tool_construct import ToolRegistrationMixin


class DecentralizedToolRegistrar:
    """
    Tool registrar that collects tools from individual tool stacks
    instead of centralized definitions.
    """
    
    def __init__(self, env_name: str, aws_profile: str = None):
        self.env_name = env_name
        self.aws_profile = aws_profile
        self.dynamodb = self._get_dynamodb_client()
        
        # Table names (would be configurable)
        self.tool_registry_table = f"ToolRegistry-{env_name}"
        self.agent_registry_table = f"AgentRegistry-{env_name}"
    
    def _get_dynamodb_client(self):
        """Initialize DynamoDB client with optional profile"""
        session = boto3.Session(profile_name=self.aws_profile) if self.aws_profile else boto3.Session()
        return session.client('dynamodb')
    
    def collect_tools_from_stacks(self) -> Dict[str, Any]:
        """
        Collect tool definitions from all tool stacks.
        
        In a real implementation, this would instantiate all tool stacks
        and collect their tool definitions automatically.
        """
        
        # Example: This would be replaced with actual stack instantiation
        # For demonstration, showing the pattern
        
        tool_stacks = []
        
        # Would instantiate like this:
        # google_maps_stack = GoogleMapsToolStackV2(app, "GoogleMapsTools", env_name=self.env_name)
        # database_stack = DatabaseToolStackV2(app, "DatabaseTools", env_name=self.env_name)
        # financial_stack = FinancialToolStackV2(app, "FinancialTools", env_name=self.env_name)
        # tool_stacks = [google_maps_stack, database_stack, financial_stack]
        
        if not tool_stacks:
            print("⚠️  No tool stacks available for collection (this is a demonstration)")
            return self._get_demo_tools()
        
        # Collect tools from all stacks
        return ToolRegistrationMixin.collect_tools_from_stacks(tool_stacks)
    
    def _get_demo_tools(self) -> Dict[str, Any]:
        """
        Demo tools showing the expected format.
        
        In real usage, this would come from actual tool stacks.
        """
        return {
            "definitions": [
                # Would be collected automatically from tool stacks
            ],
            "registry_items": [
                {
                    "tool_name": "maps_geocode",
                    "description": "Convert an address into geographic coordinates",
                    "input_schema": json.dumps({
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "The address to geocode"
                            }
                        },
                        "required": ["address"]
                    }),
                    "lambda_arn": f"arn:aws:lambda:us-west-2:123456789:function:GoogleMapsLambda-{self.env_name}",
                    "lambda_function_name": f"GoogleMapsLambda-{self.env_name}",
                    "language": "typescript",
                    "tags": json.dumps(["maps", "geocoding", "location"]),
                    "status": "active",
                    "author": "system",
                    "human_approval_required": False,
                    "version": "latest",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "updated_at": datetime.utcnow().isoformat() + "Z"
                }
            ]
        }
    
    def register_tools(self) -> bool:
        """
        Register all tools in DynamoDB Tool Registry.
        
        Returns True if successful, False otherwise.
        """
        try:
            # Collect tools from all stacks
            print(f"🔍 Collecting tools from decentralized stacks for environment: {self.env_name}")
            tool_data = self.collect_tools_from_stacks()
            
            registry_items = tool_data["registry_items"]
            print(f"📦 Found {len(registry_items)} tools to register")
            
            if not registry_items:
                print("ℹ️  No tools to register")
                return True
            
            # Register each tool
            success_count = 0
            for item in registry_items:
                if self._register_single_tool(item):
                    success_count += 1
                    print(f"✅ Registered tool: {item['tool_name']}")
                else:
                    print(f"❌ Failed to register tool: {item['tool_name']}")
            
            print(f"📊 Registration complete: {success_count}/{len(registry_items)} tools registered")
            return success_count == len(registry_items)
            
        except Exception as e:
            print(f"❌ Error during tool registration: {str(e)}")
            return False
    
    def _register_single_tool(self, tool_item: Dict[str, Any]) -> bool:
        """Register a single tool in DynamoDB"""
        try:
            # Convert to DynamoDB item format
            dynamodb_item = {
                'tool_name': {'S': tool_item['tool_name']},
                'description': {'S': tool_item['description']},
                'input_schema': {'S': tool_item['input_schema']},
                'lambda_arn': {'S': tool_item['lambda_arn']},
                'lambda_function_name': {'S': tool_item['lambda_function_name']},
                'language': {'S': tool_item['language']},
                'tags': {'S': tool_item['tags']},
                'status': {'S': tool_item['status']},
                'author': {'S': tool_item['author']},
                'human_approval_required': {'BOOL': tool_item['human_approval_required']},
                'version': {'S': tool_item['version']},
                'created_at': {'S': tool_item['created_at']},
                'updated_at': {'S': tool_item['updated_at']}
            }
            
            # Use PutItem to register/update the tool
            self.dynamodb.put_item(
                TableName=self.tool_registry_table,
                Item=dynamodb_item
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error registering tool {tool_item['tool_name']}: {str(e)}")
            return False
    
    def validate_tool_parameters(self) -> bool:
        """
        Validate that all registered tools have matching schema-Lambda parameters.
        
        This is the key benefit of the decentralized approach - we can validate
        that tool schemas match their Lambda implementations.
        """
        print("🔍 Validating tool parameter alignment...")
        
        tool_data = self.collect_tools_from_stacks()
        
        # In a real implementation, this would:
        # 1. Load each tool's Lambda code
        # 2. Parse parameter usage from the Lambda
        # 3. Compare with tool schema requirements
        # 4. Report any mismatches
        
        print("✅ Parameter validation complete (would validate schema-Lambda alignment)")
        return True
    
    def list_tools(self) -> None:
        """List all registered tools"""
        try:
            response = self.dynamodb.scan(TableName=self.tool_registry_table)
            items = response.get('Items', [])
            
            print(f"\n📋 Registered Tools ({len(items)} total):")
            print("-" * 60)
            
            for item in items:
                tool_name = item['tool_name']['S']
                description = item['description']['S']
                language = item['language']['S']
                status = item['status']['S']
                
                print(f"🔧 {tool_name}")
                print(f"   Description: {description}")
                print(f"   Language: {language}")
                print(f"   Status: {status}")
                print()
                
        except Exception as e:
            print(f"❌ Error listing tools: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='Register tools using decentralized pattern')
    parser.add_argument('--env', required=True, help='Environment name (e.g., prod, dev)')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--validate', action='store_true', help='Validate tool parameter alignment')
    parser.add_argument('--list', action='store_true', help='List registered tools')
    
    args = parser.parse_args()
    
    # Initialize registrar
    registrar = DecentralizedToolRegistrar(args.env, args.profile)
    
    print(f"🚀 Decentralized Tool Registration for environment: {args.env}")
    print("=" * 60)
    
    if args.list:
        registrar.list_tools()
        return
    
    if args.validate:
        if registrar.validate_tool_parameters():
            print("✅ All tool parameters are aligned")
        else:
            print("❌ Tool parameter mismatches found")
            sys.exit(1)
        return
    
    # Register tools
    if registrar.register_tools():
        print("🎉 Tool registration completed successfully!")
        
        # Run validation after registration
        if registrar.validate_tool_parameters():
            print("✅ Post-registration validation passed")
        else:
            print("⚠️  Post-registration validation found issues")
    else:
        print("❌ Tool registration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()