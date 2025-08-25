#!/usr/bin/env python3
"""
Deploy Web Search Agent to Bedrock Agent Core
"""

import boto3
import json
import time
import sys
import os
from pathlib import Path
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

def create_agentcore_role(agent_name: str, region: str = "us-west-2"):
    """
    Create IAM role for Agent Core runtime
    """
    iam_client = boto3.client('iam')
    role_name = f"AgentCoreRuntime-{agent_name}"
    
    # Trust policy for Agent Core
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Execution policy
    execution_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters"
                ],
                "Resource": "arn:aws:ssm:*:*:parameter/agentcore/*"
            }
        ]
    }
    
    try:
        # Check if role exists
        try:
            response = iam_client.get_role(RoleName=role_name)
            print(f"Using existing role: {role_name}")
            return response['Role']
        except iam_client.exceptions.NoSuchEntityException:
            pass
        
        # Create role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Execution role for Agent Core agent: {agent_name}"
        )
        
        # Add inline policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="AgentCoreExecutionPolicy",
            PolicyDocument=json.dumps(execution_policy)
        )
        
        print(f"Created role: {role_name}")
        
        # Wait for role to propagate
        time.sleep(10)
        
        return response['Role']
        
    except Exception as e:
        print(f"Error creating role: {e}")
        raise


def deploy_agent(agent_name: str = "web-search-agent", region: str = "us-west-2"):
    """
    Deploy the web search agent to Agent Core
    """
    print(f"Deploying {agent_name} to Agent Core in {region}...")
    
    # Create session
    boto_session = Session(region_name=region)
    
    # Create IAM role
    print("Creating IAM role...")
    role = create_agentcore_role(agent_name, region)
    role_arn = role['Arn']
    
    # Initialize Agent Core runtime
    print("Initializing Agent Core runtime...")
    agentcore_runtime = Runtime()
    
    # Configure the runtime
    print("Configuring runtime...")
    
    # Check which agent file to use
    if Path("shopping_agent.py").exists():
        entrypoint_file = "shopping_agent.py"
    elif Path("simple_web_search_agent.py").exists():
        entrypoint_file = "simple_web_search_agent.py"
    else:
        entrypoint_file = "web_search_agent.py"
    
    print(f"Using entrypoint: {entrypoint_file}")
    
    try:
        response = agentcore_runtime.configure(
            entrypoint=entrypoint_file,
            execution_role=role_arn,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region
        )
        print(f"Configuration response: {response}")
    except Exception as e:
        print(f"Configuration error: {e}")
        return False
    
    # Launch the agent
    print("Launching agent to Agent Core...")
    try:
        launch_result = agentcore_runtime.launch()
        print(f"Launch result: {launch_result}")
        
        agent_id = launch_result.agent_id
        agent_arn = launch_result.agent_arn
        ecr_uri = launch_result.ecr_uri
        
        print(f"Agent ID: {agent_id}")
        print(f"Agent ARN: {agent_arn}")
        print(f"ECR URI: {ecr_uri}")
        
    except Exception as e:
        print(f"Launch error: {e}")
        return False
    
    # Check deployment status
    print("Checking deployment status...")
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait:
        try:
            status_response = agentcore_runtime.status()
            status = status_response.endpoint['status']
            print(f"Status: {status}")
            
            if status == 'READY':
                print("✅ Agent deployed successfully!")
                
                # Save deployment info
                deployment_info = {
                    "agent_id": agent_id,
                    "agent_arn": agent_arn,
                    "ecr_uri": ecr_uri,
                    "role_arn": role_arn,
                    "region": region,
                    "status": status,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                output_file = f"agentcore-deployment-{agent_name}.json"
                with open(output_file, "w") as f:
                    json.dump(deployment_info, f, indent=2)
                
                print(f"Deployment info saved to: {output_file}")
                return True
                
            elif status in ['CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']:
                print(f"❌ Deployment failed with status: {status}")
                return False
            
            time.sleep(10)
            
        except Exception as e:
            print(f"Status check error: {e}")
            time.sleep(10)
    
    print("⏱️ Timeout waiting for deployment")
    return False


def test_agent(agent_arn: str, region: str = "us-west-2"):
    """
    Test the deployed agent
    """
    print(f"Testing agent: {agent_arn}")
    
    agentcore_client = boto3.client(
        'bedrock-agentcore',
        region_name=region
    )
    
    test_payload = {
        "prompt": "Can you search for Python programming books?",
        "url": "https://www.amazon.com"
    }
    
    try:
        response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps(test_payload)
        )
        
        # Process response
        if "text/event-stream" in response.get("contentType", ""):
            content = []
            for line in response["response"].iter_lines(chunk_size=1):
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        line = line[6:]
                        print(line)
                        content.append(line)
            return "\n".join(content)
        else:
            events = []
            for event in response.get("response", []):
                events.append(event)
            if events:
                return json.loads(events[0].decode("utf-8"))
        
    except Exception as e:
        print(f"Test error: {e}")
        return None


def main():
    """
    Main deployment function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy Web Search Agent to Bedrock Agent Core")
    parser.add_argument("--agent-name", default="web-search-agent", help="Agent name")
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--test", action="store_true", help="Test after deployment")
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("web_search_agent.py").exists():
        print("Error: web_search_agent.py not found in current directory")
        print("Please run this script from the agent_core directory")
        return 1
    
    # Deploy the agent
    success = deploy_agent(args.agent_name, args.region)
    
    if success and args.test:
        # Load deployment info
        deployment_file = f"agentcore-deployment-{args.agent_name}.json"
        if Path(deployment_file).exists():
            with open(deployment_file, "r") as f:
                deployment_info = json.load(f)
            
            # Test the agent
            result = test_agent(deployment_info["agent_arn"], args.region)
            if result:
                print(f"Test result: {result}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())