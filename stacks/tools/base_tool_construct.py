from aws_cdk import (
    Fn,
    aws_iam as iam,
    custom_resources as cr
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
from typing import List, Dict, Any
import json
from datetime import datetime, timezone


class BaseToolConstruct(Construct):
    """
    Base Tool Construct - Standardized tool registration for all languages
    
    This construct provides:
    - Automatic DynamoDB tool registry registration
    - Standardized tool specification format
    - IAM permissions management
    - Lifecycle management (create/update/delete)
    
    Usage:
        BaseToolConstruct(
            self, "MyTools",
            tool_specs=[{tool spec dict}],
            lambda_function=my_lambda,
            env_name="prod"
        )
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        tool_specs: List[Dict[str, Any]],
        lambda_function: Any,
        env_name: str = "prod",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.tool_specs = tool_specs
        self.lambda_function = lambda_function
        self.env_name = env_name
        
        # Import shared resources
        self._import_shared_resources()
        
        # Register all tools in DynamoDB
        self._register_tools_in_registry()

    def _import_shared_resources(self):
        """Import shared DynamoDB tool registry resources"""
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )

    def _register_tools_in_registry(self):
        """Register all tools in the DynamoDB registry using CDK custom resources"""
        
        for i, tool_spec in enumerate(self.tool_specs):
            self._create_tool_registration(i, tool_spec)

    def _create_tool_registration(self, index: int, tool_spec: Dict[str, Any]):
        """Create a custom resource to register a single tool in DynamoDB using direct API calls"""
        
        # Validate required fields
        required_fields = ["tool_name", "description", "input_schema"]
        for field in required_fields:
            if field not in tool_spec:
                raise ValueError(f"Tool spec missing required field: {field}")
        
        # Generate current timestamp in ISO format
        current_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Create complete tool specification with defaults for missing fields
        complete_tool_spec = {
            "tool_name": tool_spec["tool_name"],
            "description": tool_spec["description"],
            "input_schema": tool_spec["input_schema"],
            "lambda_arn": tool_spec.get("lambda_arn", self.lambda_function.function_arn),
            "lambda_function_name": tool_spec.get("lambda_function_name", self.lambda_function.function_name),
            "language": tool_spec.get("language", "python"),
            "tags": tool_spec.get("tags", []),
            "status": tool_spec.get("status", "active"),
            "author": tool_spec.get("author", "system"),
            "human_approval_required": tool_spec.get("human_approval_required", False),
            "created_at": tool_spec.get("created_at", current_timestamp),
            "updated_at": tool_spec.get("updated_at", current_timestamp)
        }
        
        # Add any additional fields from the tool spec (like version)
        for key, value in tool_spec.items():
            if key not in complete_tool_spec:
                complete_tool_spec[key] = value
        
        # Convert complex objects to JSON strings for DynamoDB storage if needed
        tool_spec_for_dynamo = complete_tool_spec.copy()
        # Only convert to JSON if not already a string (from centralized definitions)
        if not isinstance(complete_tool_spec["input_schema"], str):
            tool_spec_for_dynamo["input_schema"] = json.dumps(complete_tool_spec["input_schema"])
        if not isinstance(complete_tool_spec["tags"], str):
            tool_spec_for_dynamo["tags"] = json.dumps(complete_tool_spec["tags"])
        
        # Create the custom resource for direct DynamoDB registration
        cr.AwsCustomResource(
            self,
            f"RegisterTool{index}",
            on_create=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Item": {
                        key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                        for key, value in tool_spec_for_dynamo.items()
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"tool-{complete_tool_spec['tool_name']}-{self.env_name}"
                )
            ),
            on_update=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Item": {
                        key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                        for key, value in tool_spec_for_dynamo.items()
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"tool-{complete_tool_spec['tool_name']}-{self.env_name}"
                )
            ),
            on_delete=cr.AwsSdkCall(
                service="dynamodb",
                action="deleteItem",
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Key": {
                        "tool_name": {"S": complete_tool_spec["tool_name"]}
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
                    resources=[self.tool_registry_table_arn]
                )
            ])
        )


class MultiToolConstruct(Construct):
    """
    Multi-Tool Construct - For tools that span multiple Lambda functions
    
    This construct handles the special case where multiple tools
    are deployed across different Lambda functions (like research tools
    with both Go and Python functions).
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        tool_groups: List[Dict[str, Any]],
        env_name: str = "prod",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create a BaseToolConstruct for each tool group
        for i, tool_group in enumerate(tool_groups):
            BaseToolConstruct(
                self,
                f"ToolGroup{i}",
                tool_specs=tool_group["tool_specs"],
                lambda_function=tool_group["lambda_function"],
                env_name=env_name
            )