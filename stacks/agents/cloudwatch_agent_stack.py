from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack
import json


class CloudWatchAgentStack(ModularBaseAgentStack):
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

        # Set agent-specific properties for registry
        self.agent_description = "Expert system analyst for CloudWatch monitoring, log analysis, and root cause analysis"
        self.llm_provider = "claude"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ['monitoring', 'logs', 'cloudwatch', 'analysis', 'root-cause']
        }
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

        # Call ModularBaseAgentStack constructor
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
        
        # Set agent-specific properties for registry
        self.agent_description = "Expert system analyst for CloudWatch monitoring, log analysis, and root cause analysis"
        self.llm_provider = "claude"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ["monitoring", "logs", "analysis", "troubleshooting", "production"],
            "max_iterations": 6,
            "temperature": 0.3,
            "timeout_seconds": 300,
            "max_tokens": 6144
        }