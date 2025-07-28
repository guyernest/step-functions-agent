from aws_cdk import (
    Fn,
    aws_iam as iam,
    custom_resources as cr
)
from constructs import Construct
from .naming_conventions import NamingConventions
from typing import Dict, Any
import json
from datetime import datetime, timezone


class BaseAgentConstruct(Construct):
    """
    Base Agent Construct - Standardized agent registration for all agents
    
    This construct provides:
    - Automatic DynamoDB agent registry registration
    - Standardized agent specification format
    - IAM permissions management
    - Lifecycle management (create/update/delete)
    
    Usage:
        BaseAgentConstruct(
            self, "MyAgent",
            agent_spec={
                "agent_name": "my-agent",
                "system_prompt": "...",
                "tools": ["tool1", "tool2"],
                # ... other fields
            },
            env_name="prod"
        )
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        agent_spec: Dict[str, Any],
        env_name: str = "prod",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.agent_spec = agent_spec
        self.env_name = env_name
        
        # Import shared resources
        self._import_shared_resources()
        
        # Register agent in DynamoDB
        self._register_agent_in_registry()

    def _import_shared_resources(self):
        """Import shared DynamoDB agent registry resources"""
        self.agent_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "AgentRegistry", self.env_name)
        )
        self.agent_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "AgentRegistry", self.env_name)
        )

    def _register_agent_in_registry(self):
        """Register agent in the DynamoDB registry using direct API calls"""
        
        # Validate required fields
        required_fields = ["agent_name", "system_prompt", "description"]
        for field in required_fields:
            if field not in self.agent_spec:
                raise ValueError(f"Agent spec missing required field: {field}")
        
        # Generate current timestamp in ISO format
        current_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Create complete agent specification with defaults
        complete_agent_spec = {
            "agent_name": self.agent_spec["agent_name"],
            "version": self.agent_spec.get("version", "v1.0"),
            "status": self.agent_spec.get("status", "active"),
            "system_prompt": self.agent_spec["system_prompt"],
            "description": self.agent_spec["description"],
            "llm_provider": self.agent_spec.get("llm_provider", "claude"),
            "llm_model": self.agent_spec.get("llm_model", "claude-3-5-sonnet-20241022"),
            "tools": self.agent_spec.get("tools", []),
            "observability": self.agent_spec.get("observability", {}),
            "parameters": self.agent_spec.get("parameters", {}),
            "metadata": self.agent_spec.get("metadata", {}),
            "deployment_env": self.env_name,
            "created_at": current_timestamp,
            "updated_at": current_timestamp
        }
        
        # Convert complex objects to JSON strings for DynamoDB storage
        agent_spec_for_dynamo = complete_agent_spec.copy()
        
        # Convert lists and dicts to JSON strings
        if isinstance(complete_agent_spec["tools"], list):
            agent_spec_for_dynamo["tools"] = json.dumps(complete_agent_spec["tools"])
        if isinstance(complete_agent_spec["observability"], dict):
            agent_spec_for_dynamo["observability"] = json.dumps(complete_agent_spec["observability"])
        if isinstance(complete_agent_spec["parameters"], dict):
            agent_spec_for_dynamo["parameters"] = json.dumps(complete_agent_spec["parameters"])
        if isinstance(complete_agent_spec["metadata"], dict):
            agent_spec_for_dynamo["metadata"] = json.dumps(complete_agent_spec["metadata"])
        
        # Create the custom resource for direct DynamoDB registration
        cr.AwsCustomResource(
            self,
            "RegisterAgent",
            on_create=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters={
                    "TableName": self.agent_registry_table_name,
                    "Item": {
                        key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                        for key, value in agent_spec_for_dynamo.items()
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"agent-{complete_agent_spec['agent_name']}-{complete_agent_spec['version']}-{self.env_name}"
                )
            ),
            on_update=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters={
                    "TableName": self.agent_registry_table_name,
                    "Item": {
                        key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                        for key, value in agent_spec_for_dynamo.items()
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"agent-{complete_agent_spec['agent_name']}-{complete_agent_spec['version']}-{self.env_name}"
                )
            ),
            on_delete=cr.AwsSdkCall(
                service="dynamodb",
                action="deleteItem",
                parameters={
                    "TableName": self.agent_registry_table_name,
                    "Key": {
                        "agent_name": {"S": complete_agent_spec["agent_name"]},
                        "version": {"S": complete_agent_spec["version"]}
                    }
                }
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem", 
                        "dynamodb:DeleteItem"
                    ],
                    resources=[self.agent_registry_table_arn]
                )
            ])
        )