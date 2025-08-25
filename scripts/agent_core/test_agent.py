#!/usr/bin/env python3
"""
Test Agent Core agent invocation
"""

import boto3
import json
import argparse
import uuid
from typing import Optional

def test_agent(agent_id: str, alias_id: str, test_query: str, region: str = "us-west-2", profile: Optional[str] = None):
    """Test an Agent Core agent"""
    
    # Create session
    if profile:
        session = boto3.Session(profile_name=profile)
    else:
        session = boto3.Session()
    
    bedrock_runtime = session.client("bedrock-agent-runtime", region_name=region)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    print(f"Testing agent {agent_id} with query: {test_query}")
    print(f"Session ID: {session_id}")
    print("-" * 50)
    
    try:
        # Invoke the agent
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=test_query,
            enableTrace=True
        )
        
        # Process the streaming response
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    print(text, end='', flush=True)
        
        print("\n" + "-" * 50)
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Test Agent Core agent")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    parser.add_argument("--alias-id", required=True, help="Alias ID")
    parser.add_argument("--query", default="Hello, can you help me search for information?", help="Test query")
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--profile", help="AWS profile name")
    
    args = parser.parse_args()
    
    success = test_agent(
        args.agent_id,
        args.alias_id,
        args.query,
        args.region,
        args.profile
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())