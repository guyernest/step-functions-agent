"""
Tool Definition Base Classes

This module defines the base classes and types used for tool definitions.
Individual tool stacks should define their own specific tools locally.

The self-registration mechanism allows each tool stack to:
1. Define its own tools with schemas
2. Register them in DynamoDB at deployment time
3. Make them available to agents dynamically
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional
import json


class ToolLanguage(Enum):
    """Supported tool implementation languages"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"


class ToolStatus(Enum):
    """Tool status in registry"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TESTING = "testing"


@dataclass
class ToolDefinition:
    """Complete tool definition with metadata and schema"""
    
    # Core identification
    tool_name: str
    description: str
    
    # JSON schema for input validation
    input_schema: Dict[str, Any]
    
    # Implementation details
    language: ToolLanguage
    lambda_handler: str
    
    # Metadata
    tags: List[str]
    status: ToolStatus = ToolStatus.ACTIVE
    author: str = "system"
    human_approval_required: bool = False
    version: str = "latest"
    
    # Registry timestamps (will be set during registration)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_registry_item(self, lambda_arn: str, lambda_function_name: str) -> Dict[str, Any]:
        """Convert to DynamoDB registry item format"""
        return {
            "tool_name": self.tool_name,
            "description": self.description,
            "input_schema": json.dumps(self.input_schema),
            "lambda_arn": lambda_arn,
            "lambda_function_name": lambda_function_name,
            "language": self.language.value,
            "tags": json.dumps(self.tags),
            "status": self.status.value,
            "author": self.author,
            "human_approval_required": self.human_approval_required,
            "version": self.version,
            "created_at": self.created_at or "2025-07-19T00:00:00Z",
            "updated_at": self.updated_at or "2025-07-19T00:00:00Z"
        }
    
    def to_agent_tool_ref(self, enabled: bool = True) -> Dict[str, Any]:
        """Convert to agent registry tool reference format"""
        return {
            "tool_id": self.tool_name,
            "enabled": enabled,
            "version": self.version
        }


