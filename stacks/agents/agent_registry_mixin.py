"""
Agent Registry Mixin

This module provides a mixin class for agent registration functionality
that can be used by any agent stack.
"""

from typing import Dict, Any, List


class AgentRegistryMixin:
    """
    Mixin class that provides agent registration functionality.
    
    Classes using this mixin should have:
    - self.agent_name: str
    - self.env_name: str
    - self.system_prompt: str
    - self.state_machine: State machine object with state_machine_arn
    - self.log_group: Log group object with log_group_name (optional)
    - self.tool_configs: List[Dict[str, Any]]
    """
    
    def register_agent_in_registry(self) -> None:
        """Register this agent in the Agent Registry"""
        from ..shared.base_agent_construct import BaseAgentConstruct
        
        # Get agent specification
        agent_spec = self.get_agent_specification()
        
        # Register the agent
        BaseAgentConstruct(
            self,
            f"{self.agent_name.replace('-', '')}Registration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )
        
        print(f"📝 Registered {self.agent_name} in agent registry")
    
    def get_agent_specification(self) -> Dict[str, Any]:
        """
        Get the agent specification for registry registration.
        
        Subclasses can override this method to provide custom specifications.
        """
        # Basic specification
        spec = {
            "agent_name": self.agent_name,
            "version": getattr(self, 'agent_version', 'v1.0'),
            "status": "active",
            "system_prompt": self.system_prompt,
            "description": self._get_agent_description(),
            "llm_provider": getattr(self, 'llm_provider', 'claude'),
            "llm_model": getattr(self, 'llm_model', 'claude-3-5-sonnet-20241022'),
            "tools": self._get_tools_specification(),
            "observability": self._get_observability_config(),
            "environment": self.env_name,
            "state_machine_arn": self.state_machine.state_machine_arn,
            "metadata": self._get_agent_metadata()
        }
        
        return spec
    
    def _get_agent_description(self) -> str:
        """Get agent description."""
        if hasattr(self, 'agent_description'):
            return self.agent_description
        return f"{self.agent_name} - AI-powered agent"
    
    def _get_tools_specification(self) -> List[Dict[str, Any]]:
        """Get tools specification for the agent."""
        return [
            {
                "tool_name": tool.get("tool_name"),
                "enabled": True,
                "version": "latest",
                "requires_approval": tool.get("requires_approval", False),
                "supports_long_content": tool.get("supports_long_content", False)
            }
            for tool in self.tool_configs
        ]
    
    def _get_observability_config(self) -> Dict[str, Any]:
        """Get observability configuration."""
        log_group_name = None
        if hasattr(self, 'log_group') and self.log_group:
            log_group_name = self.log_group.log_group_name
        else:
            log_group_name = f"/aws/stepfunctions/{self.agent_name}-{self.env_name}"
        
        return {
            "log_group": log_group_name,
            "metrics_namespace": f"AIAgents/{self.agent_name}",
            "trace_enabled": True,
            "log_level": "INFO"
        }
    
    def _get_agent_metadata(self) -> Dict[str, Any]:
        """Get agent-specific metadata."""
        metadata = {
            "created_by": self.__class__.__name__
        }
        
        # Add long content metadata if this is a long content agent
        if hasattr(self, 'content_table_name'):
            metadata.update({
                "supports_long_content": True,
                "content_table": self.content_table_name,
                "max_content_size": getattr(self, 'max_content_size', 5000),
                "max_direct_size": "256KB"
            })
        
        # Add any custom metadata
        if hasattr(self, 'agent_metadata'):
            metadata.update(self.agent_metadata)
        
        return metadata