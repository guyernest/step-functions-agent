from aws_cdk import (
    Fn,
    CustomResource,
    aws_iam as iam,
    custom_resources as cr
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timezone


class BatchedToolConstruct(Construct):
    """
    Batched Tool Construct - Registers multiple tools in a single Custom Resource operation
    
    This construct solves the concurrent deployment issue by:
    - Registering all tools in a single DynamoDB batch write operation
    - Reducing the number of Custom Resources created
    - Avoiding throttling issues when deploying with --all
    
    Usage:
        BatchedToolConstruct(
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
        secret_requirements: Optional[Dict[str, List[str]]] = None,
        **kwargs
    ) -> None:
        """
        Initialize BatchedToolConstruct
        
        Args:
            scope: CDK scope
            construct_id: Construct ID
            tool_specs: List of tool specifications
            lambda_function: Lambda function for the tools
            env_name: Environment name (prod, dev, etc.)
            secret_requirements: Optional dict mapping tool_name to list of required secret keys
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.tool_specs = tool_specs
        self.lambda_function = lambda_function
        self.env_name = env_name
        self.secret_requirements = secret_requirements or {}
        
        # Import shared resources
        self._import_shared_resources()
        
        # Register all tools in a single batch operation
        self._register_all_tools_batched()
        
        # Register secret requirements if provided
        if self.secret_requirements:
            self._register_secret_requirements()

    def _import_shared_resources(self):
        """Import shared DynamoDB tool registry resources"""
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )
        
        # Import the shared Custom Resource provider service token
        self.shared_cr_service_token = Fn.import_value(
            f"SharedCustomResourceProviderToken-{self.env_name}"
        )

    def _register_all_tools_batched(self):
        """Register all tools in a single batch write operation"""
        
        # Generate current timestamp
        current_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Prepare all tools for batch write
        batch_items = []
        self.tool_names = []  # Store at class level for delete operation
        
        for tool_spec in self.tool_specs:
            # Validate required fields
            required_fields = ["tool_name", "description", "input_schema"]
            for field in required_fields:
                if field not in tool_spec:
                    raise ValueError(f"Tool spec missing required field: {field}")
            
            self.tool_names.append(tool_spec["tool_name"])
            
            # Create complete tool specification
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
                "requires_activity": tool_spec.get("requires_activity", False),
                "activity_type": tool_spec.get("activity_type", ""),
                "activity_arn": tool_spec.get("activity_arn", ""),
                "created_at": tool_spec.get("created_at", current_timestamp),
                "updated_at": tool_spec.get("updated_at", current_timestamp)
            }
            
            # Convert complex objects to JSON strings
            tool_spec_for_dynamo = complete_tool_spec.copy()
            if not isinstance(complete_tool_spec["input_schema"], str):
                tool_spec_for_dynamo["input_schema"] = json.dumps(complete_tool_spec["input_schema"])
            if not isinstance(complete_tool_spec["tags"], str):
                tool_spec_for_dynamo["tags"] = json.dumps(complete_tool_spec["tags"])
            
            # Create DynamoDB item format
            item = {
                key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                for key, value in tool_spec_for_dynamo.items()
            }
            
            batch_items.append({
                "PutRequest": {
                    "Item": item
                }
            })
        
        # Split into batches of 25 (DynamoDB limit)
        batch_size = 25
        for i in range(0, len(batch_items), batch_size):
            batch = batch_items[i:i+batch_size]
            batch_index = i // batch_size
            
            # Create a single Custom Resource for this batch using shared provider
            CustomResource(
                self,
                f"RegisterToolsBatch{batch_index}",
                service_token=self.shared_cr_service_token,
                properties={
                    "Service": "dynamodb",
                    "Action": "batchWriteItem",
                    "Parameters": json.dumps({
                        "RequestItems": {
                            self.tool_registry_table_name: batch
                        }
                    }),
                    "DeleteParameters": json.dumps({
                        "RequestItems": {
                            self.tool_registry_table_name: [
                                {
                                    "DeleteRequest": {
                                        "Key": {
                                            "tool_name": {"S": tool_name}
                                        }
                                    }
                                }
                                for tool_name in self.tool_names[i:i+batch_size]
                            ]
                        }
                    }),
                    "PhysicalResourceId": f"tools-batch-{self.node.id}-{batch_index}-{self.env_name}"
                }
            )
    
    def _register_secret_requirements(self):
        """Register secret requirements for tools"""
        # Check if secret infrastructure is available
        if not self.secret_requirements:
            return
            
        # Try to import the secret infrastructure - it might not exist yet
        try:
            tool_secrets_table_name = Fn.import_value(
                f"ToolSecretsTableName-{self.env_name}"
            )
        except:
            print(f"⚠️  Skipping secret requirements registration - infrastructure not available")
            return
        
        for tool_name, required_keys in self.secret_requirements.items():
            # Convert required_keys to DynamoDB list format
            secret_keys_list = [{"S": key} for key in required_keys]
            
            CustomResource(
                self,
                f"SecretRequirement_{tool_name.replace('-', '_')}",
                service_token=self.shared_cr_service_token,
                properties={
                    "Service": "dynamodb",
                    "Action": "putItem",
                    "Parameters": json.dumps({
                        "TableName": tool_secrets_table_name,
                        "Item": {
                            "tool_name": {"S": tool_name},
                            "secret_keys": {"L": secret_keys_list},
                            "environment": {"S": self.env_name},
                            "description": {"S": ""},
                            "registered_at": {"S": datetime.now(timezone.utc).isoformat()}
                        }
                    }),
                    "DeleteParameters": json.dumps({
                        "TableName": tool_secrets_table_name,
                        "Key": {
                            "tool_name": {"S": tool_name}
                        }
                    }),
                    "PhysicalResourceId": f"secret-req-{tool_name}-{self.env_name}"
                }
            )