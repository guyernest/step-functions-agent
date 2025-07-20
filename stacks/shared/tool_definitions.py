"""
Centralized Tool Definitions

This module defines all available tools in a type-safe way to prevent mismatches
between tool registration, agent configuration, and runtime execution.

Usage:
1. Tool stacks register tools from these definitions
2. Agent stacks reference tools by name with validation
3. Step Functions templates use validated tool names
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


class GoogleMapsTools:
    """Google Maps tool definitions"""
    
    GEOCODE = ToolDefinition(
        tool_name="maps_geocode",
        description="Convert an address into geographic coordinates",
        input_schema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "The address to geocode"
                }
            },
            "required": ["address"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["maps", "geocoding", "location"]
    )
    
    REVERSE_GEOCODE = ToolDefinition(
        tool_name="maps_reverse_geocode",
        description="Convert coordinates into an address",
        input_schema={
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Latitude coordinate"
                },
                "longitude": {
                    "type": "number", 
                    "description": "Longitude coordinate"
                }
            },
            "required": ["latitude", "longitude"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["maps", "geocoding", "location"]
    )
    
    SEARCH_PLACES = ToolDefinition(
        tool_name="maps_search_places",
        description="Search for places using Google Places API",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "location": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"}
                    },
                    "description": "Optional center point for the search"
                },
                "radius": {
                    "type": "number",
                    "description": "Search radius in meters (max 50000)"
                }
            },
            "required": ["query"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["maps", "places", "search", "location"]
    )
    
    PLACE_DETAILS = ToolDefinition(
        tool_name="maps_place_details",
        description="Get detailed information about a specific place",
        input_schema={
            "type": "object",
            "properties": {
                "place_id": {
                    "type": "string",
                    "description": "The place ID to get details for"
                }
            },
            "required": ["place_id"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["maps", "places", "details", "location"]
    )
    
    DISTANCE_MATRIX = ToolDefinition(
        tool_name="maps_distance_matrix",
        description="Calculate distances and travel times between multiple origins and destinations",
        input_schema={
            "type": "object",
            "properties": {
                "origins": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of origin addresses or coordinates"
                },
                "destinations": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of destination addresses or coordinates"
                },
                "mode": {
                    "type": "string",
                    "enum": ["driving", "walking", "bicycling", "transit"],
                    "description": "Travel mode"
                }
            },
            "required": ["origins", "destinations"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["maps", "distance", "travel", "routing"]
    )
    
    ELEVATION = ToolDefinition(
        tool_name="maps_elevation",
        description="Get elevation data for specified locations",
        input_schema={
            "type": "object",
            "properties": {
                "locations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    },
                    "description": "List of coordinates to get elevation for"
                }
            },
            "required": ["locations"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["maps", "elevation", "geography"]
    )
    
    DIRECTIONS = ToolDefinition(
        tool_name="maps_directions",
        description="Get turn-by-turn directions between locations",
        input_schema={
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "Starting location address or coordinates"
                },
                "destination": {
                    "type": "string",
                    "description": "Ending location address or coordinates"
                },
                "mode": {
                    "type": "string",
                    "enum": ["driving", "walking", "bicycling", "transit"],
                    "description": "Travel mode"
                },
                "waypoints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional intermediate waypoints"
                }
            },
            "required": ["origin", "destination"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["maps", "directions", "routing", "navigation"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all Google Maps tool definitions"""
        return [
            cls.GEOCODE,
            cls.REVERSE_GEOCODE,
            cls.SEARCH_PLACES,
            cls.PLACE_DETAILS,
            cls.DISTANCE_MATRIX,
            cls.ELEVATION,
            cls.DIRECTIONS
        ]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all Google Maps tool names for agent configuration"""
        return [tool.tool_name for tool in cls.get_all_tools()]


class DatabaseTools:
    """Database interface tool definitions"""
    
    GET_SCHEMA = ToolDefinition(
        tool_name="get_db_schema",
        description="Get database schema information including tables and columns",
        input_schema={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Optional specific table name to get schema for"
                }
            }
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["database", "schema", "sql", "metadata"]
    )
    
    EXECUTE_QUERY = ToolDefinition(
        tool_name="execute_sql_query", 
        description="Execute a SQL query and return results",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                },
                "limit": {
                    "type": "integer",
                    "description": "Optional row limit for results",
                    "default": 100
                }
            },
            "required": ["query"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["database", "sql", "query", "data"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all database tool definitions"""
        return [cls.GET_SCHEMA, cls.EXECUTE_QUERY]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all database tool names"""
        return [tool.tool_name for tool in cls.get_all_tools()]


class CodeExecutionTools:
    """Code execution tool definitions"""
    
    EXECUTE_PYTHON = ToolDefinition(
        tool_name="execute_python",
        description="Execute Python code in a secure sandbox environment",
        input_schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 30
                }
            },
            "required": ["code"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["code", "python", "execution", "sandbox"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all code execution tool definitions"""
        return [cls.EXECUTE_PYTHON]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all code execution tool names"""
        return [tool.tool_name for tool in cls.get_all_tools()]


class FinancialTools:
    """Financial data tool definitions"""
    
    YFINANCE = ToolDefinition(
        tool_name="yfinance",
        description="Get financial data and stock information using Yahoo Finance",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., AAPL, MSFT)"
                },
                "action": {
                    "type": "string",
                    "enum": ["info", "history", "financials", "balance_sheet", "cashflow"],
                    "description": "Type of financial data to retrieve"
                },
                "period": {
                    "type": "string",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                    "description": "Time period for historical data",
                    "default": "1mo"
                }
            },
            "required": ["symbol", "action"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["finance", "stocks", "yahoo", "market-data"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all financial tool definitions"""
        return [cls.YFINANCE]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all financial tool names"""
        return [tool.tool_name for tool in cls.get_all_tools()]


class ResearchTools:
    """Research tool definitions"""
    
    RESEARCH_COMPANY = ToolDefinition(
        tool_name="research_company",
        description="Perform comprehensive web research on a company using AI-powered search",
        input_schema={
            "type": "object",
            "properties": {
                "company": {
                    "type": "string",
                    "description": "The name of the company to research"
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional specific research topics"
                }
            },
            "required": ["company"]
        },
        language=ToolLanguage.GO,
        lambda_handler="main",
        tags=["research", "web", "company", "perplexity", "ai"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all research tool definitions"""
        return [cls.RESEARCH_COMPANY]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all research tool names"""
        return [tool.tool_name for tool in cls.get_all_tools()]


class CloudWatchTools:
    """CloudWatch monitoring and logging tool definitions"""
    
    FIND_LOG_GROUPS_BY_TAG = ToolDefinition(
        tool_name="find_log_groups_by_tag",
        description="Find CloudWatch log groups that have a specific tag for targeted log analysis",
        input_schema={
            "type": "object",
            "properties": {
                "tag_name": {
                    "type": "string",
                    "description": "The name of the tag, such as 'application' or 'environment'"
                },
                "tag_value": {
                    "type": "string", 
                    "description": "The value of the tag, such as 'shipping' or 'production'"
                }
            },
            "required": ["tag_name", "tag_value"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["cloudwatch", "logs", "tags", "discovery"]
    )
    
    EXECUTE_QUERY = ToolDefinition(
        tool_name="execute_query",
        description="Execute a CloudWatch Logs Insights query to retrieve relevant log data for analysis",
        input_schema={
            "type": "object",
            "properties": {
                "log_groups": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The list of log groups to query"
                },
                "query": {
                    "type": "string",
                    "description": "The CloudWatch Insights query to execute"
                },
                "time_range": {
                    "type": "string",
                    "enum": ["last_hour", "last_day", "last_week", "last_month"],
                    "description": "The time range to query"
                }
            },
            "required": ["log_groups", "query", "time_range"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["cloudwatch", "logs", "query", "insights"]
    )
    
    GET_QUERY_GENERATION_PROMPT = ToolDefinition(
        tool_name="get_query_generation_prompt",
        description="Get the prompt to generate CloudWatch Insights queries, including examples and instructions",
        input_schema={
            "type": "object",
            "properties": {}
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["cloudwatch", "query", "help", "guidance"]
    )
    
    GET_SERVICE_GRAPH = ToolDefinition(
        tool_name="get_service_graph",
        description="Get the X-Ray service graph showing relationships between services with latency and error statistics",
        input_schema={
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "integer",
                    "description": "Epoch time in seconds of the start time of the traces to analyze"
                },
                "end_time": {
                    "type": "integer", 
                    "description": "Epoch time in seconds of the end time of the traces to analyze"
                },
                "group_name": {
                    "type": "string",
                    "description": "Optional group name to filter the service graph"
                }
            },
            "required": ["start_time", "end_time"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["xray", "service-graph", "tracing", "monitoring"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all CloudWatch tool definitions"""
        return [
            cls.FIND_LOG_GROUPS_BY_TAG,
            cls.EXECUTE_QUERY,
            cls.GET_QUERY_GENERATION_PROMPT,
            cls.GET_SERVICE_GRAPH
        ]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all CloudWatch tool names for agent configuration"""
        return [tool.tool_name for tool in cls.get_all_tools()]


# Central registry of all available tools
class AllTools:
    """Central registry of all available tools"""
    
    @classmethod
    def get_all_tool_definitions(cls) -> Dict[str, ToolDefinition]:
        """Get all tool definitions mapped by name"""
        all_tools = {}
        
        # Add all tool categories
        for tool in GoogleMapsTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        for tool in DatabaseTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        for tool in CodeExecutionTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        for tool in FinancialTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        for tool in ResearchTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        for tool in CloudWatchTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        return all_tools
    
    @classmethod
    def get_all_tool_names(cls) -> List[str]:
        """Get all available tool names"""
        return list(cls.get_all_tool_definitions().keys())
    
    @classmethod
    def validate_tool_names(cls, tool_names: List[str]) -> List[str]:
        """Validate tool names and return any invalid ones"""
        available_tools = cls.get_all_tool_names()
        invalid_tools = [name for name in tool_names if name not in available_tools]
        return invalid_tools
    
    @classmethod
    def get_tools_by_names(cls, tool_names: List[str]) -> List[ToolDefinition]:
        """Get tool definitions for specified names with validation"""
        invalid_tools = cls.validate_tool_names(tool_names)
        if invalid_tools:
            raise ValueError(f"Invalid tool names: {invalid_tools}. Available tools: {cls.get_all_tool_names()}")
        
        all_tools = cls.get_all_tool_definitions()
        return [all_tools[name] for name in tool_names]