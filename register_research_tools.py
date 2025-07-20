#!/usr/bin/env python3
"""
Register research tools in DynamoDB tool registry
"""

import boto3
import json
from datetime import datetime

def register_research_tools():
    """Register all research tools in the DynamoDB tool registry"""
    
    # Create DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name='eu-west-1')
    table_name = 'tool-registry-prod'
    
    # Define research tools
    research_tools = [
        {
            "tool_name": "research_company",
            "description": "Perform comprehensive web research on a company using AI-powered search",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "The name of the company to research"
                    },
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Specific research topics (e.g., 'recent financial performance', 'market position')"
                        },
                        "description": "Optional list of specific topics to research. If not provided, will research general topics."
                    }
                },
                "required": ["company"]
            },
            "lambda_function_name": "tool-web-research-prod",
            "lambda_arn": "arn:aws:lambda:eu-west-1:YOUR_ACCOUNT:function:tool-web-research-prod",
            "language": "go",
            "tags": ["research", "web", "company", "perplexity", "ai"],
            "author": "research-team@company.com",
            "human_approval_required": False
        },
        {
            "tool_name": "list_industries",
            "description": "List all industries within a specific sector for market analysis",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sector_key": {
                        "type": "string",
                        "description": "The sector key. Valid sectors: real-estate, healthcare, financial-services, technology, consumer-cyclical, consumer-defensive, basic-materials, industrials, energy, utilities, communication-services"
                    }
                },
                "required": ["sector_key"]
            },
            "lambda_function_name": "tool-financial-data-prod",
            "lambda_arn": "arn:aws:lambda:eu-west-1:YOUR_ACCOUNT:function:tool-financial-data-prod",
            "language": "python",
            "tags": ["finance", "sectors", "industries", "yfinance"],
            "author": "research-team@company.com",
            "human_approval_required": False
        },
        {
            "tool_name": "top_industry_companies",
            "description": "Get top companies within a specific industry for competitive analysis",
            "input_schema": {
                "type": "object",
                "properties": {
                    "industry_key": {
                        "type": "string",
                        "description": "The industry key to get top companies for"
                    }
                },
                "required": ["industry_key"]
            },
            "lambda_function_name": "tool-financial-data-prod",
            "lambda_arn": "arn:aws:lambda:eu-west-1:YOUR_ACCOUNT:function:tool-financial-data-prod",
            "language": "python",
            "tags": ["finance", "companies", "industry", "rankings"],
            "author": "research-team@company.com",
            "human_approval_required": False
        },
        {
            "tool_name": "top_sector_companies",
            "description": "Get top companies within a specific sector for market analysis",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sector_key": {
                        "type": "string",
                        "description": "The sector key to get top companies for"
                    }
                },
                "required": ["sector_key"]
            },
            "lambda_function_name": "tool-financial-data-prod",
            "lambda_arn": "arn:aws:lambda:eu-west-1:YOUR_ACCOUNT:function:tool-financial-data-prod",
            "language": "python",
            "tags": ["finance", "companies", "sector", "rankings"],
            "author": "research-team@company.com",
            "human_approval_required": False
        }
    ]
    
    # Register each tool
    for tool in research_tools:
        print(f"Registering tool: {tool['tool_name']}")
        
        item = {
            'tool_name': {'S': tool['tool_name']},
            'description': {'S': tool['description']},
            'input_schema': {'S': json.dumps(tool['input_schema'])},
            'lambda_function_name': {'S': tool['lambda_function_name']},
            'lambda_arn': {'S': tool['lambda_arn']},
            'language': {'S': tool['language']},
            'tags': {'S': json.dumps(tool['tags'])},
            'created_at': {'S': datetime.now().isoformat()},
            'updated_at': {'S': datetime.now().isoformat()},
            'status': {'S': 'active'},
            'author': {'S': tool['author']},
            'human_approval_required': {'BOOL': tool['human_approval_required']}
        }
        
        try:
            response = dynamodb.put_item(
                TableName=table_name,
                Item=item,
                ConditionExpression='attribute_not_exists(tool_name)'
            )
            print(f"✅ Successfully registered {tool['tool_name']}")
        except dynamodb.exceptions.ConditionalCheckFailedException:
            print(f"⚠️  Tool {tool['tool_name']} already exists, updating...")
            # Update existing tool
            response = dynamodb.put_item(
                TableName=table_name,
                Item=item
            )
            print(f"✅ Successfully updated {tool['tool_name']}")
        except Exception as e:
            print(f"❌ Failed to register {tool['tool_name']}: {e}")

if __name__ == "__main__":
    register_research_tools()