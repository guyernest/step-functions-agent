#!/usr/bin/env python3
"""
Fix Agent Registry Naming Issues

This script identifies and fixes naming inconsistencies between agent stack definitions
and registry entries in DynamoDB.
"""

import boto3
import json
from typing import Dict, List

def get_agent_registry_table(env_name: str = "prod"):
    """Get reference to Agent Registry DynamoDB table"""
    dynamodb = boto3.resource('dynamodb')
    table_name = f"AgentRegistry-{env_name}"
    return dynamodb.Table(table_name)

def scan_all_agents(table) -> List[Dict]:
    """Scan all agents from the registry"""
    response = table.scan()
    agents = response['Items']
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        agents.extend(response['Items'])
    
    return agents

def check_agent_consistency(env_name: str = "prod"):
    """Check for naming inconsistencies between expected and actual registry entries"""
    
    # Expected agent names from stack definitions
    expected_agents = {
        "sql-agent": "Database queries and analysis",
        "google-maps": "Location and mapping services", 
        "research-agent": "Web research and company analysis"
    }
    
    print(f"Checking Agent Registry consistency for environment: {env_name}")
    print("=" * 60)
    
    try:
        table = get_agent_registry_table(env_name)
        actual_agents = scan_all_agents(table)
        
        print(f"Found {len(actual_agents)} agents in registry:")
        
        for agent in actual_agents:
            agent_name = agent.get('agent_name', 'UNKNOWN')
            version = agent.get('version', 'UNKNOWN')
            status = agent.get('status', 'UNKNOWN')
            
            print(f"  - {agent_name} (v{version}) - {status}")
            
            if agent_name not in expected_agents:
                print(f"    ⚠️  WARNING: Agent '{agent_name}' not found in expected list")
                
                # Check if this might be a naming issue
                for expected_name in expected_agents:
                    if expected_name.replace('-', '-agent') == agent_name:
                        print(f"    💡 SUGGESTION: '{agent_name}' should be '{expected_name}'")
        
        print("\nExpected agents:")
        for name, description in expected_agents.items():
            found = any(a.get('agent_name') == name for a in actual_agents)
            status_icon = "✅" if found else "❌"
            print(f"  {status_icon} {name} - {description}")
            
        return actual_agents, expected_agents
        
    except Exception as e:
        print(f"Error accessing registry: {e}")
        return [], {}

def fix_agent_name(table, old_name: str, new_name: str, version: str = "v1.0"):
    """Fix an agent name by creating new entry and deleting old one"""
    
    print(f"Fixing agent name: '{old_name}' -> '{new_name}'")
    
    try:
        # Get the existing item
        response = table.get_item(
            Key={
                'agent_name': old_name,
                'version': version
            }
        )
        
        if 'Item' not in response:
            print(f"  ❌ Agent '{old_name}' v{version} not found")
            return False
            
        item = response['Item']
        
        # Create new item with corrected name
        new_item = item.copy()
        new_item['agent_name'] = new_name
        
        # Put new item
        table.put_item(Item=new_item)
        print(f"  ✅ Created new entry: '{new_name}' v{version}")
        
        # Delete old item
        table.delete_item(
            Key={
                'agent_name': old_name,
                'version': version
            }
        )
        print(f"  ✅ Deleted old entry: '{old_name}' v{version}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error fixing agent name: {e}")
        return False

def main():
    """Main function to check and optionally fix agent registry"""
    
    env_name = "prod"
    
    # Check current state
    actual_agents, expected_agents = check_agent_consistency(env_name)
    
    if not actual_agents:
        print("No agents found or unable to access registry")
        return
    
    # Look for agents that need fixing
    fixes_needed = []
    
    for agent in actual_agents:
        agent_name = agent.get('agent_name', '')
        
        # Check if this is google-maps-agent that should be google-maps
        if agent_name == 'google-maps-agent':
            fixes_needed.append(('google-maps-agent', 'google-maps', agent.get('version', 'v1.0')))
    
    if fixes_needed:
        print(f"\nFound {len(fixes_needed)} agents that need fixing:")
        for old_name, new_name, version in fixes_needed:
            print(f"  - '{old_name}' -> '{new_name}' (v{version})")
        
        response = input(f"\nApply fixes? (y/N): ").strip().lower()
        
        if response == 'y':
            table = get_agent_registry_table(env_name)
            
            for old_name, new_name, version in fixes_needed:
                fix_agent_name(table, old_name, new_name, version)
            
            print("\n" + "=" * 60)
            print("Verification - checking registry after fixes:")
            check_agent_consistency(env_name)
            
        else:
            print("No changes made.")
    else:
        print("\n✅ All agent names are consistent!")

if __name__ == "__main__":
    main()