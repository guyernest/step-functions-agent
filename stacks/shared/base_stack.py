"""
Base Stack Class with Automatic Tagging

This module provides a base stack class that ensures consistent tagging
across all stacks in the Step Functions Agent project.
"""

from aws_cdk import Stack, Tags
from constructs import Construct
from typing import Optional


class BaseStack(Stack):
    """
    Base stack class that automatically applies consistent tags
    
    All stacks should inherit from this class to ensure proper tagging
    for discovery, cost allocation, and management.
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        application: str,
        component: str,
        owner: Optional[str] = None,
        cost_center: Optional[str] = None,
        deployment_mode: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize base stack with automatic tagging
        
        Args:
            scope: CDK scope
            construct_id: Stack ID
            env_name: Environment name (dev, prod, etc.)
            application: Application name for grouping related stacks
            component: Component type (Infrastructure, Tool, Agent, etc.)
            owner: Optional owner tag
            cost_center: Optional cost center for billing
            deployment_mode: Optional deployment mode (Standalone, Extended, Hybrid)
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)
        
        # Apply required tags
        Tags.of(self).add("Application", application)
        Tags.of(self).add("Environment", env_name)
        Tags.of(self).add("Component", component)
        Tags.of(self).add("ManagedBy", "CDK")
        
        # Apply optional tags if provided
        if owner:
            Tags.of(self).add("Owner", owner)
        if cost_center:
            Tags.of(self).add("CostCenter", cost_center)
        if deployment_mode:
            Tags.of(self).add("DeploymentMode", deployment_mode)
        
        # Store values for use in stack
        self.env_name = env_name
        self.application = application
        self.component = component
        
        # Log tag application
        print(f"📌 Tagged {construct_id}:")
        print(f"   Application: {application}")
        print(f"   Environment: {env_name}")
        print(f"   Component: {component}")


class StepFunctionsAgentStack(BaseStack):
    """Specialized base class for main Step Functions Agent stacks"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        component: str,
        **kwargs
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            env_name=env_name,
            application="AIAgents",
            component=component,
            **kwargs
        )


class LongContentStack(BaseStack):
    """Specialized base class for Long Content extension stacks"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        component: str,
        **kwargs
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            env_name=env_name,
            application="AIAgentsLongContent",
            component=component,
            **kwargs
        )
        
        # Add extension-specific tag
        Tags.of(self).add("ExtendedFrom", "AIAgents")


class FlexibleDeploymentStack(BaseStack):
    """Specialized base class for flexible deployment stacks"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        component: str,
        deployment_mode: str = "Hybrid",
        **kwargs
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            env_name=env_name,
            application="AIAgentsFlexible",
            component=component,
            deployment_mode=deployment_mode,
            **kwargs
        )