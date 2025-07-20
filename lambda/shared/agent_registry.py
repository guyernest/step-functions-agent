"""
Agent Registry Utilities

This module provides utility functions for interacting with the Agent Registry
DynamoDB table, including reading configurations, updating prompts, and
managing agent versions.
"""

import boto3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from aws_lambda_powertools import Logger

logger = Logger()
dynamodb = boto3.resource('dynamodb')


class AgentRegistry:
    """Helper class for Agent Registry operations"""
    
    def __init__(self, table_name: str = None, env_name: str = "prod"):
        """Initialize Agent Registry client
        
        Args:
            table_name: DynamoDB table name (defaults to AgentRegistry-{env_name})
            env_name: Environment name (prod, dev, staging)
        """
        self.table_name = table_name or f"AgentRegistry-{env_name}"
        self.table = dynamodb.Table(self.table_name)
        self.env_name = env_name
    
    def get_agent_config(self, agent_name: str, version: str = "latest") -> Dict[str, Any]:
        """Get agent configuration from registry
        
        Args:
            agent_name: Name of the agent
            version: Version to retrieve (defaults to "latest")
            
        Returns:
            Dict containing agent configuration
        """
        try:
            if version == "latest":
                # Query for the most recent active version
                response = self.table.query(
                    KeyConditionExpression='agent_name = :name',
                    ExpressionAttributeValues={
                        ':name': agent_name,
                        ':active': 'active'
                    },
                    FilterExpression='#status = :active',
                    ExpressionAttributeNames={
                        '#status': 'status'
                    },
                    ScanIndexForward=False,  # Sort by version descending
                    Limit=1
                )
                
                if not response['Items']:
                    raise ValueError(f"No active agent found with name: {agent_name}")
                
                item = response['Items'][0]
            else:
                # Get specific version
                response = self.table.get_item(
                    Key={
                        'agent_name': agent_name,
                        'version': version
                    }
                )
                
                if 'Item' not in response:
                    raise ValueError(f"Agent not found: {agent_name} version {version}")
                
                item = response['Item']
            
            # Parse JSON fields
            return self._parse_agent_item(item)
            
        except Exception as e:
            logger.error(f"Error retrieving agent config: {str(e)}")
            raise
    
    def update_system_prompt(self, agent_name: str, version: str, 
                           new_prompt: str, updated_by: str = "system") -> Dict[str, Any]:
        """Update system prompt for an agent
        
        Args:
            agent_name: Name of the agent
            version: Version to update
            new_prompt: New system prompt
            updated_by: User making the update
            
        Returns:
            Updated agent configuration
        """
        try:
            # Get current configuration
            current = self.get_agent_config(agent_name, version)
            
            # Update metadata
            metadata = current.get('metadata', {})
            metadata['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            metadata['updated_by'] = updated_by
            
            # Update the item
            response = self.table.update_item(
                Key={
                    'agent_name': agent_name,
                    'version': version
                },
                UpdateExpression='SET system_prompt = :prompt, metadata = :metadata, updated_at = :updated',
                ExpressionAttributeValues={
                    ':prompt': new_prompt,
                    ':metadata': json.dumps(metadata),
                    ':updated': metadata['updated_at']
                },
                ReturnValues='ALL_NEW'
            )
            
            return self._parse_agent_item(response['Attributes'])
            
        except Exception as e:
            logger.error(f"Error updating system prompt: {str(e)}")
            raise
    
    def create_agent_version(self, agent_name: str, base_version: str,
                           changes: Dict[str, Any], created_by: str = "system") -> str:
        """Create a new version of an agent based on existing version
        
        Args:
            agent_name: Name of the agent
            base_version: Version to base new version on
            changes: Dictionary of changes to apply
            created_by: User creating the version
            
        Returns:
            New version identifier
        """
        try:
            # Get base configuration
            base_config = self.get_agent_config(agent_name, base_version)
            
            # Generate new version
            new_version = self._generate_version(agent_name)
            
            # Apply changes
            new_config = base_config.copy()
            new_config.update(changes)
            
            # Update metadata
            metadata = new_config.get('metadata', {})
            metadata['created_at'] = datetime.utcnow().isoformat() + 'Z'
            metadata['updated_at'] = metadata['created_at']
            metadata['created_by'] = created_by
            metadata['base_version'] = base_version
            
            # Prepare item for DynamoDB
            item = {
                'agent_name': agent_name,
                'version': new_version,
                'updated_at': metadata['updated_at'],
                **new_config
            }
            
            # Convert complex fields to JSON strings
            for field in ['tools', 'observability', 'parameters', 'metadata']:
                if field in item and isinstance(item[field], (dict, list)):
                    item[field] = json.dumps(item[field])
            
            # Create new version
            self.table.put_item(Item=item)
            
            logger.info(f"Created new agent version: {agent_name} {new_version}")
            return new_version
            
        except Exception as e:
            logger.error(f"Error creating agent version: {str(e)}")
            raise
    
    def list_agents(self, status: str = "active", llm_provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """List agents with optional filtering
        
        Args:
            status: Filter by status (active, deprecated, testing)
            llm_provider: Filter by LLM provider
            
        Returns:
            List of agent configurations
        """
        try:
            if llm_provider:
                # Use GSI for LLM provider
                response = self.table.query(
                    IndexName='AgentsByLLM',
                    KeyConditionExpression='llm_provider = :provider',
                    ExpressionAttributeValues={
                        ':provider': llm_provider,
                        ':status': status
                    },
                    FilterExpression='#status = :status',
                    ExpressionAttributeNames={
                        '#status': 'status'
                    }
                )
            else:
                # Use GSI for status
                response = self.table.query(
                    IndexName='AgentsByStatus',
                    KeyConditionExpression='#status = :status',
                    ExpressionAttributeValues={
                        ':status': status
                    },
                    ExpressionAttributeNames={
                        '#status': 'status'
                    }
                )
            
            return [self._parse_agent_item(item) for item in response['Items']]
            
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            raise
    
    def _parse_agent_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DynamoDB item and convert JSON strings to objects"""
        parsed = item.copy()
        
        # Parse JSON string fields
        for field in ['tools', 'observability', 'parameters', 'metadata']:
            if field in parsed and isinstance(parsed[field], str):
                try:
                    parsed[field] = json.loads(parsed[field])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON field: {field}")
        
        return parsed
    
    def _generate_version(self, agent_name: str) -> str:
        """Generate a new version identifier"""
        # Get all versions for this agent
        response = self.table.query(
            KeyConditionExpression='agent_name = :name',
            ExpressionAttributeValues={
                ':name': agent_name
            },
            ProjectionExpression='version',
            ScanIndexForward=False
        )
        
        versions = [item['version'] for item in response['Items']]
        
        # Extract version numbers and increment
        max_num = 0
        for v in versions:
            if v.startswith('v') and '.' in v:
                try:
                    major, minor = v[1:].split('.')
                    num = int(major) * 100 + int(minor)
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        
        # Generate next version
        next_major = (max_num // 100) + (1 if max_num % 100 == 99 else 0)
        next_minor = (max_num % 100 + 1) if max_num % 100 < 99 else 0
        
        return f"v{next_major}.{next_minor}"


# Lambda handler for Step Functions integration
def get_agent_config_handler(event, context):
    """Lambda handler for retrieving agent configuration
    
    This can be used as a Lambda function invoked by Step Functions
    to dynamically load agent configurations.
    """
    try:
        agent_name = event['agent_name']
        version = event.get('version', 'latest')
        env_name = event.get('env_name', 'prod')
        
        registry = AgentRegistry(env_name=env_name)
        config = registry.get_agent_config(agent_name, version)
        
        return {
            'statusCode': 200,
            'body': config
        }
        
    except Exception as e:
        logger.error(f"Error in get_agent_config_handler: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }