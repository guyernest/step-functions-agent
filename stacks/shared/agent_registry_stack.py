from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    custom_resources as cr,
    aws_iam as iam
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
import json


class AgentRegistryStack(Stack):
    """
    Agent Registry Stack - Centralized agent configuration management
    
    This stack creates:
    - DynamoDB table for agent configurations
    - Global secondary indexes for queries
    - Initial agent configurations
    - IAM permissions for Step Functions access
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create Agent Registry table
        self._create_agent_registry_table()
        
        # Create initial agent configurations (DEPRECATED - agents now register themselves)
        # Individual agent stacks now register themselves using BaseAgentConstruct
        # This ensures agent definitions are maintained alongside their implementations
        # self._create_initial_agents()  # Commented out due to removed tool classes
        
        # Create stack exports
        self._create_stack_exports()

    def _create_agent_registry_table(self):
        """Create DynamoDB table for agent configurations"""
        
        self.agent_registry_table = dynamodb.Table(
            self,
            "AgentRegistryTable",
            table_name=f"AgentRegistry-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="agent_name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            )
        )
        
        # Add GSI for status queries
        self.agent_registry_table.add_global_secondary_index(
            index_name="AgentsByStatus",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for LLM provider queries
        self.agent_registry_table.add_global_secondary_index(
            index_name="AgentsByLLM",
            partition_key=dynamodb.Attribute(
                name="llm_provider",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="agent_name",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for environment queries
        self.agent_registry_table.add_global_secondary_index(
            index_name="AgentsByEnvironment",
            partition_key=dynamodb.Attribute(
                name="deployment_env",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="agent_name",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

    def _create_initial_agents(self):
        """Create initial agent configurations"""
        
        # Define initial agent configurations
        agents = [
            {
                "agent_name": "sql-agent",
                "version": "v1.0",
                "status": "active",
                "system_prompt": """You are an expert SQL assistant with deep knowledge of database systems and query optimization.
                
Your primary responsibilities:
- Analyze database schemas and understand table relationships
- Write efficient, optimized SQL queries
- Explain query results clearly
- Suggest performance improvements
- Handle complex joins and aggregations

Always ensure queries are safe and follow best practices.""",
                "description": "SQL query generation and database analysis agent",
                "llm_provider": "claude",
                "llm_model": "claude-3-5-sonnet-20241022",
                "tools": json.dumps([
                    {"tool_id": "get_db_schema", "enabled": True, "version": "latest"},
                    {"tool_id": "execute_sql_query", "enabled": True, "version": "latest"},
                    {"tool_id": "execute_python", "enabled": True, "version": "latest"}
                ]),
                "observability": json.dumps({
                    "log_group": f"/aws/lambda/sql-agent-{self.env_name}",
                    "metrics_namespace": "AIAgents/SQL",
                    "trace_enabled": True,
                    "log_level": "INFO"
                }),
                "parameters": json.dumps({
                    "max_iterations": 5,
                    "temperature": 0.3,
                    "timeout_seconds": 300,
                    "max_tokens": 4096
                }),
                "metadata": json.dumps({
                    "created_at": "2025-07-19T00:00:00Z",
                    "updated_at": "2025-07-19T00:00:00Z",
                    "created_by": "system",
                    "tags": ["sql", "database", "production"],
                    "deployment_env": self.env_name
                }),
                "deployment_env": self.env_name
            },
            {
                "agent_name": "google-maps-agent",
                "version": "v1.0", 
                "status": "active",
                "system_prompt": """You are a location services expert specializing in Google Maps functionality.

Your capabilities include:
- Geocoding addresses to coordinates
- Reverse geocoding coordinates to addresses  
- Finding places and businesses
- Calculating routes and directions
- Providing distance and time estimates
- Searching for nearby locations

Always provide accurate location information and helpful suggestions.""",
                "description": "Location services agent using Google Maps APIs",
                "llm_provider": "gemini",
                "llm_model": "gemini-1.5-flash",
                "tools": json.dumps([
                    tool_def.to_agent_tool_ref() for tool_def in GoogleMapsTools.get_all_tools()
                ]),
                "observability": json.dumps({
                    "log_group": f"/aws/lambda/google-maps-agent-{self.env_name}",
                    "metrics_namespace": "AIAgents/GoogleMaps",
                    "trace_enabled": True,
                    "log_level": "INFO"
                }),
                "parameters": json.dumps({
                    "max_iterations": 3,
                    "temperature": 0.5,
                    "timeout_seconds": 180,
                    "max_tokens": 2048
                }),
                "metadata": json.dumps({
                    "created_at": "2025-07-19T00:00:00Z",
                    "updated_at": "2025-07-19T00:00:00Z",
                    "created_by": "system",
                    "tags": ["location", "maps", "geocoding", "production"],
                    "deployment_env": self.env_name
                }),
                "deployment_env": self.env_name
            },
            {
                "agent_name": "research-agent",
                "version": "v1.0",
                "status": "active", 
                "system_prompt": """You are an expert financial analyst and research assistant with specialization in comprehensive market analysis.

Your capabilities include:
- Deep company research using AI-powered web search
- Financial sector and industry analysis
- Competitive intelligence and market positioning
- Recent performance and market trends analysis

Available tools:
- research_company: Perform comprehensive web research on any company using AI search
- list_industries: Get all industries within a specific sector
- top_industry_companies: Find leading companies in specific industries  
- top_sector_companies: Identify top companies in market sectors

When conducting research:
1. Start with broad sector/industry analysis when appropriate
2. Use web research for current, qualitative insights
3. Combine multiple data sources for comprehensive analysis
4. Focus on recent developments and market positioning
5. Provide actionable insights and clear summaries

Always explain your research methodology and cite the specific tools used for transparency.""",
                "description": "Financial research agent with web and market data capabilities",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": json.dumps([
                    {"tool_id": "research_company", "enabled": True, "version": "latest"},
                    {"tool_id": "list_industries", "enabled": True, "version": "latest"},
                    {"tool_id": "top_industry_companies", "enabled": True, "version": "latest"},
                    {"tool_id": "top_sector_companies", "enabled": True, "version": "latest"}
                ]),
                "observability": json.dumps({
                    "log_group": f"/aws/lambda/research-agent-{self.env_name}",
                    "metrics_namespace": "AIAgents/Research", 
                    "trace_enabled": True,
                    "log_level": "INFO"
                }),
                "parameters": json.dumps({
                    "max_iterations": 5,
                    "temperature": 0.7,
                    "timeout_seconds": 300,
                    "max_tokens": 4096
                }),
                "metadata": json.dumps({
                    "created_at": "2025-07-19T00:00:00Z",
                    "updated_at": "2025-07-19T00:00:00Z",
                    "created_by": "system",
                    "tags": ["research", "financial", "production"],
                    "deployment_env": self.env_name
                }),
                "deployment_env": self.env_name
            }
        ]
        
        # Create custom resources to populate initial data
        for i, agent in enumerate(agents):
            cr.AwsCustomResource(
                self,
                f"InitialAgent{i}",
                on_create=cr.AwsSdkCall(
                    service="dynamodb",
                    action="putItem",
                    parameters={
                        "TableName": self.agent_registry_table.table_name,
                        "Item": {
                            key: {"S": str(value)} if isinstance(value, str) else {"N": str(value)}
                            for key, value in agent.items()
                        }
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(
                        f"agent-{agent['agent_name']}-{agent['version']}"
                    )
                ),
                policy=cr.AwsCustomResourcePolicy.from_statements([
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["dynamodb:PutItem"],
                        resources=[self.agent_registry_table.table_arn]
                    )
                ])
            )

    def _create_stack_exports(self):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export table name
        CfnOutput(
            self,
            "AgentRegistryTableName",
            value=self.agent_registry_table.table_name,
            export_name=NamingConventions.stack_export_name(
                "Table", "AgentRegistry", self.env_name
            ),
            description="Agent Registry DynamoDB table name"
        )
        
        # Export table ARN
        CfnOutput(
            self,
            "AgentRegistryTableArn",
            value=self.agent_registry_table.table_arn,
            export_name=NamingConventions.stack_export_name(
                "TableArn", "AgentRegistry", self.env_name
            ),
            description="Agent Registry DynamoDB table ARN"
        )