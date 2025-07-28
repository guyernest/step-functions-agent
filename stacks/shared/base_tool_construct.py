"""
Base Tool Construct

Provides a base pattern for tool stacks to define both their Lambda implementation
and tool registry definitions in a single location, preventing parameter mismatches.

This architectural pattern ensures that:
1. Lambda implementation and tool schema are always in sync
2. Tool teams can develop independently without touching shared files  
3. Type safety is enforced at the tool level
4. Registry entries are generated automatically from the source of truth
"""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    CfnOutput
)
from constructs import Construct

from stacks.shared.tool_definitions import ToolDefinition, ToolLanguage, ToolStatus


@dataclass
class ToolExport:
    """Tool export information for cross-stack references"""
    tool_definition: ToolDefinition
    lambda_arn: str
    lambda_function_name: str
    export_name: str


class BaseToolConstruct(Construct):
    """
    Base construct for tool stacks that own their tool definitions.
    
    This pattern ensures Lambda implementation and tool schema are always in sync
    by defining them in the same stack.
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name
        self.tool_exports: List[ToolExport] = []
        
        # Subclasses must implement this to define their tools and Lambdas
        self._create_tools()
        
        # Export tool information for agent discovery
        self._create_exports()
    
    @abstractmethod
    def _create_tools(self) -> None:
        """
        Create Lambda functions and define tool schemas.
        
        Subclasses must:
        1. Create Lambda functions 
        2. Define ToolDefinition objects that match the Lambda parameters
        3. Call self._register_tool() for each tool
        """
        pass
    
    def _register_tool(
        self, 
        tool_definition: ToolDefinition, 
        lambda_function: _lambda.Function
    ) -> None:
        """
        Register a tool with its Lambda function.
        
        This creates the necessary exports for agent discovery and ensures
        the tool definition matches the Lambda implementation.
        """
        export_name = f"{tool_definition.tool_name.replace('_', '-').title()}LambdaArn-{self.env_name}"
        
        tool_export = ToolExport(
            tool_definition=tool_definition,
            lambda_arn=lambda_function.function_arn,
            lambda_function_name=lambda_function.function_name,
            export_name=export_name
        )
        
        self.tool_exports.append(tool_export)
    
    def _create_exports(self) -> None:
        """Create CloudFormation exports for all registered tools"""
        for tool_export in self.tool_exports:
            CfnOutput(
                self,
                f"{tool_export.tool_definition.tool_name}Export",
                value=tool_export.lambda_arn,
                export_name=tool_export.export_name,
                description=f"ARN of the {tool_export.tool_definition.tool_name} Lambda function"
            )
    
    def get_tool_definitions(self) -> List[ToolDefinition]:
        """Get all tool definitions for registry registration"""
        return [export.tool_definition for export in self.tool_exports]
    
    def get_tool_configs_for_agent(self, requires_approval: bool = False) -> List[Dict[str, Any]]:
        """
        Get tool configurations for agent stacks.
        
        Returns the format needed by agent stacks to configure their tools.
        """
        return [
            {
                "tool_name": export.tool_definition.tool_name,
                "lambda_arn": export.lambda_arn,
                "requires_approval": requires_approval or export.tool_definition.human_approval_required
            }
            for export in self.tool_exports
        ]
    
    def get_registry_items(self) -> List[Dict[str, Any]]:
        """
        Get tool registry items for DynamoDB registration.
        
        These can be used by registration scripts to populate the Tool Registry.
        """
        return [
            export.tool_definition.to_registry_item(
                lambda_arn=export.lambda_arn,
                lambda_function_name=export.lambda_function_name
            )
            for export in self.tool_exports
        ]


class ToolRegistrationMixin:
    """
    Mixin for stacks that need to register tools in DynamoDB.
    
    This can be used by registration scripts or bootstrap processes.
    """
    
    @staticmethod
    def collect_tools_from_stacks(stacks: List[BaseToolConstruct]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect tool definitions from multiple tool stacks.
        
        Returns:
            Dictionary with 'definitions' and 'registry_items' keys
        """
        all_definitions = []
        all_registry_items = []
        
        for stack in stacks:
            all_definitions.extend(stack.get_tool_definitions())
            all_registry_items.extend(stack.get_registry_items())
        
        return {
            "definitions": all_definitions,
            "registry_items": all_registry_items
        }