#!/usr/bin/env python3
"""
Clean up existing Agent Core agent before redeployment
"""

import boto3
import argparse
import sys
from typing import Optional


def delete_agent(agent_id: str, region: str = "us-west-2", profile: Optional[str] = None):
    """Delete an agent and its resources"""
    
    # Create session
    if profile:
        session = boto3.Session(profile_name=profile)
    else:
        session = boto3.Session()
    
    bedrock_agent = session.client("bedrock-agent", region_name=region)
    
    try:
        # Get agent details
        print(f"Getting agent details for: {agent_id}")
        agent = bedrock_agent.get_agent(agentId=agent_id)["agent"]
        agent_name = agent.get("agentName", "unknown")
        
        print(f"Deleting agent: {agent_name} ({agent_id})")
        
        # Delete all agent aliases first
        try:
            aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
            for alias in aliases.get("agentAliasSummaries", []):
                if alias["agentAliasName"] != "TSTALIASID":  # Skip default test alias
                    print(f"  Deleting alias: {alias['agentAliasId']}")
                    bedrock_agent.delete_agent_alias(
                        agentId=agent_id,
                        agentAliasId=alias["agentAliasId"]
                    )
        except Exception as e:
            print(f"  Warning: Could not delete aliases: {e}")
        
        # Delete all action groups
        try:
            action_groups = bedrock_agent.list_agent_action_groups(
                agentId=agent_id,
                agentVersion="DRAFT"
            )
            for ag in action_groups.get("actionGroupSummaries", []):
                print(f"  Deleting action group: {ag['actionGroupName']}")
                bedrock_agent.delete_agent_action_group(
                    agentId=agent_id,
                    actionGroupId=ag["actionGroupId"],
                    agentVersion="DRAFT"
                )
        except Exception as e:
            print(f"  Warning: Could not delete action groups: {e}")
        
        # Delete the agent
        response = bedrock_agent.delete_agent(agentId=agent_id)
        
        print(f"✅ Successfully deleted agent: {agent_name}")
        return True
        
    except bedrock_agent.exceptions.ResourceNotFoundException:
        print(f"❌ Agent not found: {agent_id}")
        return False
    except Exception as e:
        print(f"❌ Error deleting agent: {e}")
        return False


def find_and_delete_agent(agent_name: str, region: str = "us-west-2", profile: Optional[str] = None):
    """Find an agent by name and delete it"""
    
    # Create session
    if profile:
        session = boto3.Session(profile_name=profile)
    else:
        session = boto3.Session()
    
    bedrock_agent = session.client("bedrock-agent", region_name=region)
    
    try:
        # List all agents
        response = bedrock_agent.list_agents()
        
        for agent in response.get("agentSummaries", []):
            if agent["agentName"] == agent_name:
                print(f"Found agent: {agent_name} (ID: {agent['agentId']})")
                return delete_agent(agent["agentId"], region, profile)
        
        print(f"No agent found with name: {agent_name}")
        return False
        
    except Exception as e:
        print(f"Error finding agent: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Clean up Agent Core agents")
    parser.add_argument("--agent-id", help="Agent ID to delete")
    parser.add_argument("--agent-name", help="Agent name to find and delete")
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--profile", help="AWS profile name")
    
    args = parser.parse_args()
    
    if not args.agent_id and not args.agent_name:
        print("❌ Please specify either --agent-id or --agent-name")
        sys.exit(1)
    
    if args.agent_id:
        success = delete_agent(args.agent_id, args.region, args.profile)
    else:
        success = find_and_delete_agent(args.agent_name, args.region, args.profile)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()