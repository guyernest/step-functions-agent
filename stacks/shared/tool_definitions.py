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
    
    LIST_INDUSTRIES = ToolDefinition(
        tool_name="list_industries",
        description="List all industries within a specific sector for market analysis",
        input_schema={
            "type": "object",
            "properties": {
                "sector_key": {
                    "type": "string",
                    "description": "The sector key. Valid sectors: real-estate, healthcare, financial-services, technology, consumer-cyclical, consumer-defensive, basic-materials, industrials, energy, utilities, communication-services"
                }
            },
            "required": ["sector_key"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["finance", "sectors", "industries", "yfinance"]
    )
    
    TOP_INDUSTRY_COMPANIES = ToolDefinition(
        tool_name="top_industry_companies",
        description="Get top companies within a specific industry for competitive analysis",
        input_schema={
            "type": "object",
            "properties": {
                "industry_key": {
                    "type": "string",
                    "description": "The industry key to get top companies for"
                }
            },
            "required": ["industry_key"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["finance", "companies", "industry", "rankings"]
    )
    
    TOP_SECTOR_COMPANIES = ToolDefinition(
        tool_name="top_sector_companies",
        description="Get top companies within a specific sector for market analysis",
        input_schema={
            "type": "object",
            "properties": {
                "sector_key": {
                    "type": "string",
                    "description": "The sector key to get top companies for"
                }
            },
            "required": ["sector_key"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["finance", "companies", "sector", "rankings"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all financial tool definitions"""
        return [
            cls.YFINANCE,
            cls.LIST_INDUSTRIES,
            cls.TOP_INDUSTRY_COMPANIES,
            cls.TOP_SECTOR_COMPANIES
        ]
    
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


class RustTools:
    """Rust-based analysis tool definitions"""
    
    HDBSCAN_CLUSTERING = ToolDefinition(
        tool_name="calculate_hdbscan_clusters",
        description="Perform HDBSCAN clustering on vector data stored in S3 using high-performance Rust implementation",
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {
                    "type": "string",
                    "description": "S3 bucket containing the CSV file with vector data"
                },
                "key": {
                    "type": "string",
                    "description": "S3 key path to the CSV file with named vectors"
                },
                "min_cluster_size": {
                    "type": "integer",
                    "description": "Minimum number of samples in a cluster",
                    "default": 2
                },
                "min_samples": {
                    "type": "integer", 
                    "description": "Number of samples in a neighborhood for a core point",
                    "default": 2
                }
            },
            "required": ["bucket", "key"]
        },
        language=ToolLanguage.RUST,
        lambda_handler="main",
        tags=["clustering", "hdbscan", "machine-learning", "rust", "s3"]
    )
    
    SEMANTIC_SEARCH = ToolDefinition(
        tool_name="semantic_search_rust",
        description="Perform semantic search using Qdrant vector database with Cohere embeddings in Rust",
        input_schema={
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "The text query to search for semantically similar documents"
                },
                "collection_name": {
                    "type": "string",
                    "description": "Name of the Qdrant collection to search",
                    "default": "star_charts"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 3
                }
            },
            "required": ["search_query"]
        },
        language=ToolLanguage.RUST,
        lambda_handler="main", 
        tags=["semantic-search", "vector-db", "qdrant", "embeddings", "rust"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all Rust tool definitions"""
        return [
            cls.HDBSCAN_CLUSTERING,
            cls.SEMANTIC_SEARCH
        ]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all Rust tool names"""
        return [tool.tool_name for tool in cls.get_all_tools()]


class JavaTools:
    """Java-based analysis tool definitions"""
    
    STOCK_ANALYZER = ToolDefinition(
        tool_name="calculate_moving_average",
        description="Calculate moving averages for stock price time series using high-performance Java Fork/Join framework",
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {
                    "type": "string",
                    "description": "S3 bucket containing the CSV file with stock price data"
                },
                "key": {
                    "type": "string",
                    "description": "S3 key path to the CSV file with stock ticker and price data"
                },
                "window": {
                    "type": "integer",
                    "description": "Moving average window size (number of periods)",
                    "default": 3
                }
            },
            "required": ["bucket", "key"]
        },
        language=ToolLanguage.JAVA,
        lambda_handler="tools.StockAnalyzerLambda::handleRequest",
        tags=["finance", "stocks", "moving-average", "java", "fork-join"]
    )
    
    VOLATILITY_ANALYZER = ToolDefinition(
        tool_name="calculate_volatility",
        description="Calculate historical volatility for stock price time series using statistical analysis in Java",
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {
                    "type": "string",
                    "description": "S3 bucket containing the CSV file with stock price data"
                },
                "key": {
                    "type": "string",
                    "description": "S3 key path to the CSV file with stock ticker and price data"
                }
            },
            "required": ["bucket", "key"]
        },
        language=ToolLanguage.JAVA,
        lambda_handler="tools.StockAnalyzerLambda::handleRequest",
        tags=["finance", "stocks", "volatility", "java", "statistics"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all Java tool definitions"""
        return [
            cls.STOCK_ANALYZER,
            cls.VOLATILITY_ANALYZER
        ]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all Java tool names"""
        return [tool.tool_name for tool in cls.get_all_tools()]


class SpecializedTools:
    """Additional specialized tool definitions"""
    
    EARTHQUAKE_QUERY = ToolDefinition(
        tool_name="query_earthquakes",
        description="Query earthquake data using USGS API with date range filtering",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                },
                "min_magnitude": {
                    "type": "number",
                    "description": "Minimum earthquake magnitude",
                    "default": 2.5
                }
            },
            "required": ["start_date", "end_date"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["earthquake", "seismic", "usgs", "disaster"]
    )
    
    BOOK_RECOMMENDATION = ToolDefinition(
        tool_name="get_nyt_books",
        description="Get book recommendations using New York Times Books API with genre and bestseller filtering",
        input_schema={
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "description": "Book genre (e.g., 'fiction', 'nonfiction', 'hardcover-fiction')",
                    "default": "combined-print-and-e-book-fiction"
                },
                "list_type": {
                    "type": "string",
                    "description": "List type (current, history, or overview)",
                    "default": "current"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of books to return",
                    "default": 10
                }
            }
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["books", "recommendations", "nyt", "bestsellers", "literature"]
    )
    
    LOCAL_AGENT = ToolDefinition(
        tool_name="local_agent_execute",
        description="Execute automation scripts on remote systems through a secure activity-based execution model",
        input_schema={
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "The automation script to execute on the remote system (PowerShell, Python, Bash, etc.)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Script execution timeout in seconds",
                    "default": 300
                }
            },
            "required": ["script"]
        },
        language=ToolLanguage.RUST,
        lambda_handler="main",
        tags=["local", "command", "execution", "system", "rust"],
        human_approval_required=True
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all specialized tool definitions"""
        return [
            cls.EARTHQUAKE_QUERY,
            cls.BOOK_RECOMMENDATION,
            cls.LOCAL_AGENT
        ]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all specialized tool names"""
        return [tool.tool_name for tool in cls.get_all_tools()]


class AdvancedTools:
    """Advanced specialized tool definitions for enterprise workflows"""
    
    MICROSOFT_GRAPH_API = ToolDefinition(
        tool_name="MicrosoftGraphAPI",
        description="Access Microsoft Graph API including emails, Teams messages, SharePoint, and user management",
        input_schema={
            "type": "object",
            "properties": {
                "endpoint": {
                    "type": "string",
                    "description": "Microsoft Graph API endpoint (e.g., 'users', 'me/messages', 'sites')"
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    "description": "HTTP method for the API call",
                    "default": "GET"
                },
                "data": {
                    "type": "object",
                    "description": "Request body data for POST/PUT/PATCH operations"
                }
            },
            "required": ["endpoint"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["microsoft", "graph", "email", "teams", "sharepoint", "enterprise"],
        human_approval_required=True
    )
    
    WEB_SCRAPER_MEMORY = ToolDefinition(
        tool_name="get_site_schema",
        description="Retrieve website schema and extraction scripts from memory for efficient web scraping",
        input_schema={
            "type": "object",
            "properties": {
                "site_url": {
                    "type": "string",
                    "description": "URL of the website to get schema for"
                }
            },
            "required": ["site_url"]
        },
        language=ToolLanguage.RUST,
        lambda_handler="main",
        tags=["webscraping", "memory", "schema", "rust", "automation"]
    )
    
    SAVE_EXTRACTION_SCRIPT = ToolDefinition(
        tool_name="save_extraction_script",
        description="Save extraction scripts to memory for reuse in web scraping operations",
        input_schema={
            "type": "object",
            "properties": {
                "site_url": {
                    "type": "string",
                    "description": "URL of the website the script is for"
                },
                "script_name": {
                    "type": "string",
                    "description": "Name of the extraction script"
                },
                "script_content": {
                    "type": "string",
                    "description": "The extraction script content"
                },
                "description": {
                    "type": "string",
                    "description": "Description of what the script extracts"
                }
            },
            "required": ["site_url", "script_name", "script_content"]
        },
        language=ToolLanguage.RUST,
        lambda_handler="main",
        tags=["webscraping", "memory", "script", "rust", "automation"]
    )
    
    GRAPHQL_INTERFACE = ToolDefinition(
        tool_name="execute_graphql_query",
        description="Execute GraphQL queries against AWS AppSync or other GraphQL endpoints with dynamic schema support",
        input_schema={
            "type": "object",
            "properties": {
                "graphql_query": {
                    "type": "string",
                    "description": "The GraphQL query or mutation to execute"
                },
                "variables": {
                    "type": "object",
                    "description": "Variables to pass to the GraphQL query"
                }
            },
            "required": ["graphql_query"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["graphql", "appsync", "api", "query", "mutation"]
    )
    
    GENERATE_GRAPHQL_PROMPT = ToolDefinition(
        tool_name="generate_query_prompt",
        description="Generate GraphQL query prompts based on schema analysis and user requirements",
        input_schema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the data or operation needed"
                }
            },
            "required": ["description"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["graphql", "query-generation", "schema", "ai-assist"]
    )
    
    IMAGE_ANALYSIS = ToolDefinition(
        tool_name="analyze_images",
        description="Analyze images using Google Gemini multi-modal AI capabilities with natural language queries",
        input_schema={
            "type": "object",
            "properties": {
                "image_locations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "bucket": {"type": "string"},
                            "key": {"type": "string"}
                        },
                        "required": ["bucket", "key"]
                    },
                    "description": "S3 locations of images to analyze"
                },
                "query": {
                    "type": "string",
                    "description": "Natural language query about the images"
                }
            },
            "required": ["image_locations", "query"]
        },
        language=ToolLanguage.PYTHON,
        lambda_handler="lambda_handler",
        tags=["image", "analysis", "gemini", "multimodal", "ai", "vision"]
    )
    
    WEB_SCRAPER = ToolDefinition(
        tool_name="web_scrape",
        description="Advanced web scraping with headless browser supporting navigation, interaction, and content extraction",
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to scrape"
                },
                "actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["search", "click", "hover", "select", "type", "wait", "waitForSelector", "clickAndWaitForSelector"]
                            },
                            "selector": {"type": "string"},
                            "text": {"type": "string"},
                            "timeout": {"type": "number"}
                        },
                        "required": ["type"]
                    },
                    "description": "Navigation and interaction actions to perform"
                },
                "extract_selectors": {
                    "type": "object",
                    "description": "CSS selectors for content extraction"
                },
                "screenshot": {
                    "type": "boolean",
                    "description": "Whether to take a screenshot",
                    "default": False
                }
            },
            "required": ["url"]
        },
        language=ToolLanguage.TYPESCRIPT,
        lambda_handler="handler",
        tags=["webscraping", "browser", "playwright", "automation", "extraction"]
    )
    
    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all advanced tool definitions"""
        return [
            cls.MICROSOFT_GRAPH_API,
            cls.WEB_SCRAPER_MEMORY,
            cls.SAVE_EXTRACTION_SCRIPT,
            cls.GRAPHQL_INTERFACE,
            cls.GENERATE_GRAPHQL_PROMPT,
            cls.IMAGE_ANALYSIS,
            cls.WEB_SCRAPER
        ]
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """Get all advanced tool names"""
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
            
        for tool in RustTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        for tool in JavaTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        for tool in SpecializedTools.get_all_tools():
            all_tools[tool.tool_name] = tool
            
        for tool in AdvancedTools.get_all_tools():
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