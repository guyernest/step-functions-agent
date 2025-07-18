import re
from typing import Optional


class NamingConventions:
    """
    Naming conventions utility for consistent resource naming across all stacks.
    
    This class provides standardized naming patterns for:
    - Tool Lambda functions
    - LLM Lambda functions  
    - Secrets Manager paths
    - DynamoDB tables
    - IAM roles and policies
    """

    @staticmethod
    def tool_lambda_name(tool_id: str, environment: str = "prod") -> str:
        """
        Generate consistent tool Lambda function name.
        
        Args:
            tool_id: Tool identifier (e.g., "web_scraper", "html_parser")
            environment: Environment name (e.g., "prod", "dev", "staging")
            
        Returns:
            Standardized Lambda function name: "tool-{tool_id}-{environment}"
        """
        # Ensure tool_id is valid
        if not NamingConventions.validate_tool_id(tool_id):
            raise ValueError(f"Invalid tool_id: {tool_id}. Must contain only lowercase letters, numbers, and hyphens.")
        
        return f"tool-{tool_id}-{environment}"

    @staticmethod
    def tool_lambda_arn(tool_id: str, region: str, account: str, environment: str = "prod") -> str:
        """
        Generate consistent tool Lambda ARN.
        
        Args:
            tool_id: Tool identifier
            region: AWS region
            account: AWS account ID
            environment: Environment name
            
        Returns:
            Full Lambda function ARN
        """
        function_name = NamingConventions.tool_lambda_name(tool_id, environment)
        return f"arn:aws:lambda:{region}:{account}:function:{function_name}"

    @staticmethod
    def llm_lambda_name(llm_provider: str, environment: str = "prod") -> str:
        """
        Generate consistent LLM Lambda function name.
        
        Args:
            llm_provider: LLM provider name (e.g., "claude", "openai", "gemini")
            environment: Environment name
            
        Returns:
            Standardized LLM Lambda function name: "shared-{llm_provider}-llm-{environment}"
        """
        return f"shared-{llm_provider}-llm-{environment}"

    @staticmethod
    def llm_lambda_arn(llm_provider: str, region: str, account: str, environment: str = "prod") -> str:
        """
        Generate consistent LLM Lambda ARN.
        
        Args:
            llm_provider: LLM provider name
            region: AWS region
            account: AWS account ID
            environment: Environment name
            
        Returns:
            Full LLM Lambda function ARN
        """
        function_name = NamingConventions.llm_lambda_name(llm_provider, environment)
        return f"arn:aws:lambda:{region}:{account}:function:{function_name}"

    @staticmethod
    def tool_secret_path(tool_id: str, environment: str = "prod") -> str:
        """
        Generate consistent tool-specific secret path.
        
        Args:
            tool_id: Tool identifier
            environment: Environment name
            
        Returns:
            Secrets Manager path: "/ai-agent/tools/{tool_id}/{environment}"
        """
        if not NamingConventions.validate_tool_id(tool_id):
            raise ValueError(f"Invalid tool_id: {tool_id}")
        
        return f"/ai-agent/tools/{tool_id}/{environment}"

    @staticmethod
    def llm_secret_path(environment: str = "prod") -> str:
        """
        Generate consistent LLM secrets path.
        
        Args:
            environment: Environment name
            
        Returns:
            Secrets Manager path: "/ai-agent/llm-secrets/{environment}"
        """
        return f"/ai-agent/llm-secrets/{environment}"

    @staticmethod
    def infrastructure_secret_path(environment: str = "prod") -> str:
        """
        Generate consistent infrastructure secrets path.
        
        Args:
            environment: Environment name
            
        Returns:
            Secrets Manager path: "/ai-agent/infrastructure/{environment}"
        """
        return f"/ai-agent/infrastructure/{environment}"

    @staticmethod
    def tool_registry_table_name(environment: str = "prod") -> str:
        """
        Generate consistent tool registry table name.
        
        Args:
            environment: Environment name
            
        Returns:
            DynamoDB table name: "ToolRegistry-{environment}"
        """
        return f"ToolRegistry-{environment}"

    @staticmethod
    def tool_execution_role_name(tool_id: str, environment: str = "prod") -> str:
        """
        Generate consistent tool execution role name.
        
        Args:
            tool_id: Tool identifier
            environment: Environment name
            
        Returns:
            IAM role name: "ToolExecutionRole-{tool_id}-{environment}"
        """
        if not NamingConventions.validate_tool_id(tool_id):
            raise ValueError(f"Invalid tool_id: {tool_id}")
        
        return f"ToolExecutionRole-{tool_id}-{environment}"

    @staticmethod
    def agent_execution_role_name(agent_name: str, environment: str = "prod") -> str:
        """
        Generate consistent agent execution role name.
        
        Args:
            agent_name: Agent identifier
            environment: Environment name
            
        Returns:
            IAM role name: "AgentExecutionRole-{agent_name}-{environment}"
        """
        return f"AgentExecutionRole-{agent_name}-{environment}"

    @staticmethod
    def stack_export_name(resource_type: str, resource_name: str, environment: str = "prod") -> str:
        """
        Generate consistent CloudFormation export name.
        
        Args:
            resource_type: Type of resource (e.g., "Lambda", "Secret", "Table")
            resource_name: Name of the resource
            environment: Environment name
            
        Returns:
            Export name: "Shared{resource_type}{resource_name}-{environment}"
        """
        return f"Shared{resource_type}{resource_name}-{environment}"

    @staticmethod
    def validate_tool_id(tool_id: str) -> bool:
        """
        Validate tool ID follows naming convention.
        
        Args:
            tool_id: Tool identifier to validate
            
        Returns:
            True if valid, False otherwise
            
        Rules:
            - Only lowercase letters, numbers, and hyphens
            - Must start with letter
            - Cannot end with hyphen
            - Length between 3-50 characters
        """
        if not tool_id or len(tool_id) < 3 or len(tool_id) > 50:
            return False
        
        # Must start with letter, contain only lowercase letters, numbers, and hyphens
        # Cannot end with hyphen
        pattern = r'^[a-z][a-z0-9-]*[a-z0-9]$'
        return bool(re.match(pattern, tool_id))

    @staticmethod
    def validate_environment(environment: str) -> bool:
        """
        Validate environment name follows convention.
        
        Args:
            environment: Environment name to validate
            
        Returns:
            True if valid, False otherwise
            
        Rules:
            - Only lowercase letters and numbers
            - Length between 2-20 characters
        """
        if not environment or len(environment) < 2 or len(environment) > 20:
            return False
        
        pattern = r'^[a-z0-9]+$'
        return bool(re.match(pattern, environment))

    @staticmethod
    def get_supported_llm_providers() -> list:
        """
        Get list of supported LLM providers.
        
        Returns:
            List of supported LLM provider names
        """
        return [
            "claude",
            "openai", 
            "gemini",
            "bedrock",
            "deepseek",
            "xai"
        ]

    @staticmethod
    def validate_llm_provider(llm_provider: str) -> bool:
        """
        Validate LLM provider name.
        
        Args:
            llm_provider: LLM provider name to validate
            
        Returns:
            True if valid, False otherwise
        """
        return llm_provider in NamingConventions.get_supported_llm_providers()


# Convenience functions for common operations
def generate_tool_lambda_arns(tool_ids: list, region: str, account: str, environment: str = "prod") -> list:
    """
    Generate Lambda ARNs for a list of tool IDs.
    
    Args:
        tool_ids: List of tool identifiers
        region: AWS region
        account: AWS account ID
        environment: Environment name
        
    Returns:
        List of Lambda function ARNs
    """
    return [
        NamingConventions.tool_lambda_arn(tool_id, region, account, environment)
        for tool_id in tool_ids
    ]


def validate_tool_configuration(tool_config: dict) -> bool:
    """
    Validate tool configuration follows naming conventions.
    
    Args:
        tool_config: Dictionary containing tool configuration
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["tool_id", "environment"]
    
    for field in required_fields:
        if field not in tool_config:
            return False
    
    if not NamingConventions.validate_tool_id(tool_config["tool_id"]):
        return False
    
    if not NamingConventions.validate_environment(tool_config["environment"]):
        return False
    
    return True