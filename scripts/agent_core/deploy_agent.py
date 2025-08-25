#!/usr/bin/env python3
"""
Deploy agents to AWS Bedrock Agent Core service
This script manages the lifecycle of Agent Core agents until CDK support is available.
"""

import json
import boto3
import argparse
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import time
from pathlib import Path


class AgentCoreDeployer:
    """Deploy and manage agents in AWS Bedrock Agent Core"""
    
    def __init__(self, region: str = "us-west-2", profile: Optional[str] = None):
        """
        Initialize the Agent Core deployer
        
        Args:
            region: AWS region (default: us-west-2)
            profile: AWS profile name (optional, uses default session if not provided)
        """
        if profile:
            print(f"Using AWS profile: {profile}")
            session = boto3.Session(profile_name=profile)
        else:
            # Use default session (from environment or assumed role)
            session = boto3.Session()
            # Check if we have credentials
            try:
                caller = session.client("sts").get_caller_identity()
                print(f"Using AWS account: {caller['Account']} (ARN: {caller['Arn'][:50]}...)")
            except Exception as e:
                print(f"Warning: Could not verify AWS credentials: {e}")
            
        self.bedrock_agent = session.client("bedrock-agent", region_name=region)
        self.bedrock_runtime = session.client("bedrock-agent-runtime", region_name=region)
        self.iam = session.client("iam", region_name=region)
        self.region = region
        print(f"Using region: {region}")
        
    def create_agent_role(self, agent_name: str) -> str:
        """
        Create IAM role for the agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Role ARN
        """
        role_name = f"AgentCoreRole-{agent_name}"
        
        # Trust policy for Bedrock Agent Core
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceAccount": boto3.client("sts").get_caller_identity()["Account"]
                        },
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:bedrock:{self.region}:*:agent/*"
                        }
                    }
                }
            ]
        }
        
        try:
            # Check if role exists
            response = self.iam.get_role(RoleName=role_name)
            print(f"Using existing role: {response['Role']['Arn']}")
            return response['Role']['Arn']
        except self.iam.exceptions.NoSuchEntityException:
            # Create new role
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Role for Agent Core agent: {agent_name}",
                Tags=[
                    {"Key": "ManagedBy", "Value": "AgentCoreDeployer"},
                    {"Key": "AgentName", "Value": agent_name}
                ]
            )
            
            # Attach necessary policies
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
            )
            
            print(f"Created role: {response['Role']['Arn']}")
            return response['Role']['Arn']
    
    def create_or_update_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update an agent in Agent Core
        
        Args:
            config: Agent configuration
            
        Returns:
            Agent details
        """
        agent_name = config["agent_name"]
        
        # Check if agent exists
        existing_agent = self.find_agent(agent_name)
        
        if existing_agent:
            print(f"Updating existing agent: {agent_name}")
            return self.update_agent(existing_agent["agentId"], config)
        else:
            print(f"Creating new agent: {agent_name}")
            return self.create_agent(config)
    
    def find_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Find an agent by name"""
        try:
            response = self.bedrock_agent.list_agents()
            for agent in response.get("agentSummaries", []):
                if agent["agentName"] == agent_name:
                    return self.bedrock_agent.get_agent(agentId=agent["agentId"])["agent"]
            return None
        except Exception as e:
            print(f"Error finding agent: {e}")
            return None
    
    def wait_for_agent_ready(self, agent_id: str, max_wait: int = 60) -> bool:
        """
        Wait for agent to be in a ready state
        
        Args:
            agent_id: Agent ID to wait for
            max_wait: Maximum seconds to wait (default: 60)
            
        Returns:
            True if agent is ready, False if timeout
        """
        print(f"Waiting for agent {agent_id} to be ready...")
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait:
            try:
                response = self.bedrock_agent.get_agent(agentId=agent_id)
                agent_status = response["agent"]["agentStatus"]
                
                if agent_status in ["PREPARED", "NOT_PREPARED", "READY"]:
                    print(f"✅ Agent is ready (status: {agent_status})")
                    return True
                elif agent_status in ["FAILED", "DELETING"]:
                    print(f"❌ Agent is in failed state: {agent_status}")
                    return False
                else:
                    print(f"⏳ Agent status: {agent_status}, waiting...")
                    time.sleep(2)
            except Exception as e:
                print(f"Error checking agent status: {e}")
                time.sleep(2)
        
        print(f"⏱️ Timeout waiting for agent to be ready after {max_wait} seconds")
        return False
    
    def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent"""
        agent_name = config["agent_name"]
        role_arn = self.create_agent_role(agent_name)
        
        # Prepare agent configuration
        agent_params = {
            "agentName": agent_name,
            "description": config.get("description", f"Agent Core agent: {agent_name}"),
            "agentResourceRoleArn": role_arn,
            "foundationModel": config.get("foundation_model", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
            "instruction": config.get("instruction", "You are a helpful AI assistant."),
            "idleSessionTTLInSeconds": config.get("idle_timeout", 600)
        }
        
        # Add prompt override if provided
        if "prompt_override" in config:
            agent_params["promptOverrideConfiguration"] = config["prompt_override"]
        
        # Add guardrails if provided
        if "guardrail_id" in config:
            agent_params["guardrailConfiguration"] = {
                "guardrailIdentifier": config["guardrail_id"],
                "guardrailVersion": config.get("guardrail_version", "DRAFT")
            }
        
        response = self.bedrock_agent.create_agent(**agent_params)
        agent = response["agent"]
        agent_id = agent["agentId"]
        
        print(f"Created agent: {agent_id}")
        
        # Wait for agent to be ready before adding action groups
        if not self.wait_for_agent_ready(agent_id):
            print("Warning: Agent may not be fully ready, but continuing...")
        
        # Add action groups if defined
        if "action_groups" in config:
            for action_group in config["action_groups"]:
                try:
                    self.add_action_group(agent_id, action_group)
                except Exception as e:
                    if "Agent is in Creating state" in str(e):
                        print("Agent still creating, waiting longer...")
                        time.sleep(5)
                        self.add_action_group(agent_id, action_group)
                    else:
                        raise
        
        # Add knowledge bases if defined
        if "knowledge_bases" in config:
            for kb in config["knowledge_bases"]:
                self.associate_knowledge_base(agent_id, kb)
        
        # Prepare the agent (make it ready for use)
        print("Preparing agent for use...")
        self.bedrock_agent.prepare_agent(agentId=agent_id)
        
        # Wait for preparation to complete
        self.wait_for_agent_ready(agent_id)
        
        return agent
    
    def update_agent(self, agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent"""
        agent_name = config["agent_name"]
        
        # Get existing agent to retrieve the role ARN
        existing = self.bedrock_agent.get_agent(agentId=agent_id)["agent"]
        role_arn = existing.get("agentResourceRoleArn")
        
        # If no role exists, create one
        if not role_arn:
            role_arn = self.create_agent_role(agent_name)
        
        update_params = {
            "agentId": agent_id,
            "agentName": agent_name,
            "agentResourceRoleArn": role_arn,
            "description": config.get("description", f"Agent Core agent: {agent_name}"),
            "foundationModel": config.get("foundation_model", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
            "instruction": config.get("instruction", "You are a helpful AI assistant."),
            "idleSessionTTLInSeconds": config.get("idle_timeout", 600)
        }
        
        response = self.bedrock_agent.update_agent(**update_params)
        agent = response["agent"]
        
        # Wait for agent to be ready after update
        if not self.wait_for_agent_ready(agent_id):
            print("Warning: Agent may not be fully ready after update")
        
        # Update action groups if defined
        if "action_groups" in config:
            # Note: You may need to delete existing action groups first
            # For now, we'll skip updating action groups on existing agents
            print("Note: Action group updates not implemented for existing agents")
        
        # Prepare the agent after update
        print("Preparing agent after update...")
        self.bedrock_agent.prepare_agent(agentId=agent_id)
        
        # Wait for preparation to complete
        self.wait_for_agent_ready(agent_id)
        
        print(f"Updated agent: {agent_id}")
        return agent
    
    def add_action_group(self, agent_id: str, action_group_config: Dict[str, Any]):
        """Add an action group to an agent"""
        params = {
            "agentId": agent_id,
            "agentVersion": "DRAFT",
            "actionGroupName": action_group_config["name"],
            "description": action_group_config.get("description", ""),
            "actionGroupExecutor": {}
        }
        
        # Configure executor (Lambda or custom)
        if "lambda_arn" in action_group_config:
            params["actionGroupExecutor"]["lambda"] = action_group_config["lambda_arn"]
        elif "custom_control" in action_group_config:
            params["actionGroupExecutor"]["customControl"] = action_group_config["custom_control"]
        
        # Add API schema if provided
        if "api_schema" in action_group_config:
            if isinstance(action_group_config["api_schema"], dict):
                params["apiSchema"] = {
                    "payload": json.dumps(action_group_config["api_schema"])
                }
            else:
                # Assume it's a file path
                with open(action_group_config["api_schema"], "r") as f:
                    params["apiSchema"] = {
                        "payload": f.read()
                    }
        
        # Add function schema if provided (for function calling)
        if "function_schema" in action_group_config:
            params["functionSchema"] = action_group_config["function_schema"]
        
        response = self.bedrock_agent.create_agent_action_group(**params)
        print(f"Added action group: {action_group_config['name']}")
        return response
    
    def associate_knowledge_base(self, agent_id: str, kb_config: Dict[str, Any]):
        """Associate a knowledge base with an agent"""
        params = {
            "agentId": agent_id,
            "agentVersion": "DRAFT",
            "knowledgeBaseId": kb_config["id"],
            "description": kb_config.get("description", ""),
            "knowledgeBaseState": kb_config.get("state", "ENABLED")
        }
        
        response = self.bedrock_agent.associate_agent_knowledge_base(**params)
        print(f"Associated knowledge base: {kb_config['id']}")
        return response
    
    def create_agent_alias(self, agent_id: str, alias_name: str = "latest") -> str:
        """
        Create an alias for the agent
        
        Args:
            agent_id: Agent ID
            alias_name: Alias name
            
        Returns:
            Alias ID
        """
        try:
            response = self.bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName=alias_name,
                description=f"Alias for agent {agent_id}"
            )
            print(f"Created alias: {response['agentAlias']['agentAliasId']}")
            return response['agentAlias']['agentAliasId']
        except Exception as e:
            # Alias might already exist
            response = self.bedrock_agent.list_agent_aliases(agentId=agent_id)
            for alias in response.get("agentAliasSummaries", []):
                if alias["agentAliasName"] == alias_name:
                    print(f"Using existing alias: {alias['agentAliasId']}")
                    return alias["agentAliasId"]
            raise e
    
    def deploy_agent_from_file(self, config_file: str) -> Dict[str, Any]:
        """
        Deploy an agent from a configuration file
        
        Args:
            config_file: Path to YAML or JSON configuration file
            
        Returns:
            Deployment details
        """
        try:
            # Load configuration
            with open(config_file, "r") as f:
                if config_file.endswith(".yaml") or config_file.endswith(".yml"):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            # Create or update agent
            agent = self.create_or_update_agent(config)
            
            # Create alias
            alias_id = self.create_agent_alias(agent["agentId"])
            
            # Generate output for Step Functions integration
            output = {
                "agent_id": agent["agentId"],
                "agent_arn": agent["agentArn"],
                "alias_id": alias_id,
                "agent_name": agent["agentName"],
                "region": self.region,
                "invoke_url": f"https://bedrock-agent-runtime.{self.region}.amazonaws.com",
                "state_machine_config": self.generate_state_machine_config(agent, alias_id)
            }
            
            # Save output
            output_file = f"agent-core-output-{agent['agentName']}.json"
            with open(output_file, "w") as f:
                json.dump(output, f, indent=2)
            
            print(f"\n✅ Deployment complete! Output saved to: {output_file}")
            print(f"Agent ID: {agent['agentId']}")
            print(f"Alias ID: {alias_id}")
            
            return output
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            raise  # Re-raise to ensure non-zero exit code
    
    def generate_state_machine_config(self, agent: Dict[str, Any], alias_id: str) -> Dict[str, Any]:
        """Generate Step Functions state machine configuration for the agent"""
        return {
            "Comment": f"Wrapper state machine for Agent Core agent: {agent['agentName']}",
            "StartAt": "InvokeAgent",
            "States": {
                "InvokeAgent": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::bedrock:invokeAgent",
                    "Parameters": {
                        "AgentId": agent["agentId"],
                        "AgentAliasId": alias_id,
                        "SessionId.$": "$.session_id",
                        "InputText.$": "$.input_text",
                        "EnableTrace": True,
                        "EndSession": False
                    },
                    "ResultPath": "$.agent_response",
                    "Next": "FormatResponse"
                },
                "FormatResponse": {
                    "Type": "Pass",
                    "Parameters": {
                        "agent_messages": [{
                            "role": "assistant",
                            "content.$": "$.agent_response.completion"
                        }],
                        "trace.$": "$.agent_response.trace",
                        "session_id.$": "$.session_id",
                        "citations.$": "$.agent_response.citations"
                    },
                    "End": True
                }
            }
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Deploy agents to AWS Bedrock Agent Core")
    parser.add_argument("config_file", help="Path to agent configuration file (YAML or JSON)")
    parser.add_argument("--region", default="us-west-2", help="AWS region (default: us-west-2)")
    parser.add_argument("--profile", help="AWS profile name (optional, uses default or environment)")
    
    args = parser.parse_args()
    
    # Validate config file exists
    if not Path(args.config_file).exists():
        print(f"Error: Configuration file not found: {args.config_file}")
        sys.exit(1)
    
    # Deploy agent
    deployer = AgentCoreDeployer(region=args.region, profile=args.profile)
    result = deployer.deploy_agent_from_file(args.config_file)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())