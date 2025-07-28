from aws_cdk import (
    Fn,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct
from .flexible_long_content_agent_stack import FlexibleLongContentAgentStack
from typing import Dict, Any, List


class TestExtendedLongContentAgentStack(FlexibleLongContentAgentStack):
    """
    Example: Long Content Agent that Extends Existing Infrastructure
    
    This example shows how developers can directly specify which resources
    to import vs create when adding long content support to existing agents.
    
    In this example:
    - Reuses existing agent registry from production
    - Reuses existing Claude LLM function
    - Reuses some existing tools (web_scraper, google_maps)
    - Creates new long-content versions of SQL tools
    - Uses existing approval activity
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        
        # === DEVELOPER CONFIGURATION ===
        # Simply specify what you want to import vs create
        
        # 1. Import existing LLM function
        llm_arn = "arn:aws:lambda:us-east-1:145023107515:function:shared-claude-prod"
        # Or from CloudFormation export:
        # llm_arn = Fn.import_value("SharedClaudeLambdaArn-prod")
        
        # 2. Import existing agent registry
        agent_registry_table = "tool-registry-prod"
        # Or by ARN:
        # agent_registry_arn = "arn:aws:dynamodb:us-east-1:145023107515:table/tool-registry-prod"
        
        # 3. Import existing approval activity (optional)
        approval_activity_arn = "arn:aws:states:us-east-1:145023107515:activity:sql-approval-prod"
        
        # Configure the agent
        agent_config = {
            # Use existing agent registry
            "use_agent_registry": True,
            "agent_registry_table_name": agent_registry_table,
            
            # Use existing LLM
            "llm_arn": llm_arn,
            
            # Use existing approval activity
            "create_approval_activity": False,
            "existing_approval_activity_arn": approval_activity_arn
        }
        
        # System prompt
        system_prompt = """You are a test agent demonstrating how to extend existing infrastructure 
with long content support. You have access to both existing tools and new long-content tools."""
        
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="TestLongContentExtension",
            env_name=env_name,
            agent_config=agent_config,
            system_prompt=system_prompt,
            max_content_size=10000,
            **kwargs
        )
        
        print(f"✅ Created test agent extending existing infrastructure")
    
    def _get_tool_configs(self) -> List[Dict[str, Any]]:
        """
        Mix of existing tools and new long-content tools
        
        This is where developers specify exactly which tools to reuse
        and which to create new versions of.
        """
        
        return [
            # === REUSE EXISTING TOOLS ===
            {
                "tool_name": "web_scraper",
                "lambda_arn": "arn:aws:lambda:us-east-1:145023107515:function:tool-web-scraper-prod",
                "requires_approval": False,
                "supports_long_content": False  # Existing tool without long content
            },
            {
                "tool_name": "google_maps", 
                # Import from CloudFormation export
                "lambda_arn": Fn.import_value("GoogleMapsLambdaArn-prod"),
                "requires_approval": False,
                "supports_long_content": False
            },
            
            # === NEW LONG CONTENT TOOLS ===
            {
                "tool_name": "sql_query_executor_v2",
                # New tool with long content support
                "lambda_arn": Fn.import_value(f"SqlQueryExecutorLongContentArn-{self.env_name}"),
                "requires_activity": True,
                "activity_type": "human_approval", 
                "supports_long_content": True
            },
            {
                "tool_name": "web_scraper_large",
                # New enhanced version
                "lambda_arn": Fn.import_value(f"WebScraperLargeLambdaArn-{self.env_name}"),
                "requires_approval": False,
                "supports_long_content": True
            }
        ]
    
    def _import_resources(self):
        """
        Override to handle custom imports
        
        This shows how developers can import additional resources
        beyond the standard ones.
        """
        
        # Call parent to handle standard imports
        super()._import_resources()
        
        # === CUSTOM IMPORTS ===
        
        # Import existing S3 bucket for artifacts
        self.artifacts_bucket_name = "step-functions-artifacts-prod"
        
        # Import existing SNS topic for notifications
        self.notification_topic_arn = "arn:aws:sns:us-east-1:145023107515:agent-notifications-prod"
        
        # Import existing Lambda layer (if you have custom layers)
        self.custom_layer_arn = "arn:aws:lambda:us-east-1:145023107515:layer:custom-utils:3"
    
    def _add_permissions(self):
        """
        Override to add custom permissions
        """
        
        # Call parent for standard permissions
        super()._add_permissions()
        
        # Add permission to use imported resources
        if hasattr(self, 'notification_topic_arn'):
            self.agent_role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sns:Publish"],
                    resources=[self.notification_topic_arn]
                )
            )


# === ALTERNATIVE PATTERNS ===

class MinimalLongContentAgentStack(FlexibleLongContentAgentStack):
    """
    Minimal example: Only add long content to one specific tool
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        
        # Reuse everything except create long content version of one tool
        agent_config = {
            "use_agent_registry": True,
            "import_registry_from": "AgentRegistry-prod",
            "llm_arn": Fn.import_value("SharedClaudeLambdaArn-prod")
        }
        
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="MinimalLongContent",
            agent_config=agent_config,
            **kwargs
        )
    
    def _get_tool_configs(self):
        # All existing tools except one new long content version
        return [
            {
                "tool_name": "document_processor_v2",
                "lambda_arn": Fn.import_value("DocumentProcessorLongContentArn-dev"),
                "supports_long_content": True
            }
        ]


class HybridDeploymentAgentStack(FlexibleLongContentAgentStack):
    """
    Hybrid example: Import from multiple environments
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        
        agent_config = {
            # Use prod agent registry
            "use_agent_registry": True,
            "agent_registry_table_name": "agent-registry-prod",
            
            # Use staging LLM for testing
            "llm_arn": "arn:aws:lambda:us-east-1:145023107515:function:claude-llm-staging"
        }
        
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="HybridAgent",
            agent_config=agent_config,
            **kwargs
        )
    
    def _get_tool_configs(self):
        return [
            # Mix of prod and dev tools
            {
                "tool_name": "stable_tool",
                "lambda_arn": "arn:aws:lambda:us-east-1:145023107515:function:stable-tool-prod",
                "supports_long_content": False
            },
            {
                "tool_name": "experimental_tool", 
                "lambda_arn": "arn:aws:lambda:us-east-1:145023107515:function:experimental-tool-dev",
                "supports_long_content": True
            }
        ]