from aws_cdk import Stack, Fn
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.tool_definitions import CloudWatchTools, AllTools
from ..shared.base_agent_construct import BaseAgentConstruct
import json


class CloudWatchAgentStack(BaseAgentStack):
    """
    CloudWatch Agent Stack - Expert system analyst for root cause analysis
    
    This agent demonstrates:
    - CloudWatch Logs Insights query expertise
    - X-Ray service graph analysis
    - Root cause analysis methodology
    - Log pattern recognition and anomaly detection
    - Multi-service system troubleshooting
    
    The agent provides comprehensive monitoring capabilities including:
    - Log group discovery by tags
    - CloudWatch Insights query generation and execution
    - Service dependency mapping through X-Ray
    - Performance analysis and error tracking
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        # Import Claude Lambda ARN from shared LLM stack (best for analytical tasks)
        claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{env_name}")
        
        # Import CloudWatch tools Lambda ARN
        cloudwatch_lambda_arn = Fn.import_value(f"CloudWatchInsightsLambdaArn-{env_name}")
        
        # Define tool configurations
        tool_configs = [
            {
                "tool_name": "find_log_groups_by_tag",
                "lambda_arn": cloudwatch_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "execute_query",
                "lambda_arn": cloudwatch_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "get_query_generation_prompt",
                "lambda_arn": cloudwatch_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "get_service_graph",
                "lambda_arn": cloudwatch_lambda_arn,
                "requires_approval": False
            }
        ]
        
        # Validate tool names exist in centralized definitions
        tool_names = [config["tool_name"] for config in tool_configs]
        invalid_tools = AllTools.validate_tool_names(tool_names)
        if invalid_tools:
            raise ValueError(f"CloudWatch Agent uses invalid tools: {invalid_tools}. Available tools: {AllTools.get_all_tool_names()}")
        
        # Define system prompt for this agent
        system_prompt = """You are an expert software system analyst with deep knowledge of root cause analysis and CloudWatch monitoring.

You are working with users who are trying to understand the root cause of problems in software systems.

Your capabilities include:
- CloudWatch Logs Insights query expertise and pattern analysis
- X-Ray service graph analysis for dependency mapping
- Root cause analysis methodology and systematic troubleshooting
- Performance bottleneck identification and error pattern recognition
- Multi-service system architecture understanding

Available tools:
- find_log_groups_by_tag: Discover relevant log groups based on application tags
- get_query_generation_prompt: Get comprehensive guidance for CloudWatch Insights query creation
- execute_query: Run CloudWatch Insights queries to retrieve and analyze log data
- get_service_graph: Analyze X-Ray service graphs for dependency and performance insights

When helping users with system analysis:
1. Start by understanding the problem scope and identifying relevant log groups
2. Use the query generation prompt to craft effective CloudWatch Insights queries
3. Execute targeted queries to gather specific log data related to the issue
4. Analyze X-Ray service graphs to understand service dependencies and performance metrics
5. Look for patterns in errors, latency spikes, and service interactions
6. Provide systematic root cause analysis with evidence from the logs and metrics
7. Suggest actionable remediation steps based on your findings

Always base your analysis on actual retrieved log data and service metrics. Explain your methodology and cite specific evidence from the tools."""

        # Call BaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="cloudwatch-agent",
            llm_arn=claude_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Store env_name and system_prompt for registration
        self.env_name = env_name
        self.system_prompt = system_prompt
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this agent in the Agent Registry using BaseAgentConstruct"""
        
        # Define CloudWatch agent specification
        agent_spec = {
            "agent_name": "cloudwatch-agent",
            "version": "v1.0",
            "status": "active",
            "system_prompt": self.system_prompt,
            "description": "Expert system analyst for CloudWatch monitoring, log analysis, and root cause analysis",
            "llm_provider": "claude",
            "llm_model": "claude-3-5-sonnet-20241022",
            "tools": [
                {"tool_name": "find_log_groups_by_tag", "enabled": True, "version": "latest"},
                {"tool_name": "execute_query", "enabled": True, "version": "latest"},
                {"tool_name": "get_query_generation_prompt", "enabled": True, "version": "latest"},
                {"tool_name": "get_service_graph", "enabled": True, "version": "latest"}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/cloudwatch-agent-{self.env_name}",
                "metrics_namespace": "AIAgents/CloudWatch",
                "trace_enabled": True,
                "log_level": "INFO"
            },
            "parameters": {
                "max_iterations": 6,
                "temperature": 0.3,
                "timeout_seconds": 300,
                "max_tokens": 6144
            },
            "metadata": {
                "created_by": "system",
                "tags": ["monitoring", "logs", "analysis", "troubleshooting", "production"],
                "deployment_env": self.env_name
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "CloudWatchAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )