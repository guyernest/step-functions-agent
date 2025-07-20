from aws_cdk import (
    Duration,
    Stack,
    Fn,
    RemovalPolicy,
    aws_logs as logs,
    aws_iam as iam,
    aws_stepfunctions as sfn,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
from typing import List
import json


class BaseAgentStack(Stack):
    """
    Base Agent Stack - Common patterns for all agents
    
    This base class provides:
    - Agent execution role with standard permissions
    - Log group creation with consistent naming
    - Tool permission generation based on tool IDs
    - Step Functions template processing
    - State machine creation with standard settings
    
    Derived agent stacks just need to specify:
    - LLM ARN to use
    - List of tool IDs from registry
    - Agent-specific configuration
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        agent_name: str,
        llm_arn: str, 
        tool_ids: List[str], 
        env_name: str = "prod",
        system_prompt: str = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.agent_name = agent_name
        self.llm_arn = llm_arn
        self.tool_ids = tool_ids
        self.system_prompt = system_prompt or f"You are a helpful AI assistant with access to various tools."
        
        # Import shared resources
        self._import_shared_resources()
        
        # Create agent execution role
        self._create_agent_execution_role()
        
        # Create Step Functions workflow from template
        self._create_step_functions_from_template()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import tool registry table name and ARN
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )
        
        # Import agent registry table name and ARN
        self.agent_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "AgentRegistry", self.env_name)
        )
        
        self.agent_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "AgentRegistry", self.env_name)
        )
        
        # Import tool Lambda ARNs for IAM permissions
        # We'll generate permissions for all tools the agent might use
        self._import_tool_lambda_arns()

    def _import_tool_lambda_arns(self):
        """Import Lambda ARNs for tools this agent uses"""
        self.tool_lambda_arns = {}
        
        # Map of known tool stacks and their export names
        tool_stack_exports = {
            # DB Interface tools
            "get_db_schema": f"DBInterfaceLambdaArn-{self.env_name}",
            "execute_sql_query": f"DBInterfaceLambdaArn-{self.env_name}",
            
            # E2B tools  
            "execute_python": f"ExecuteCodeLambdaArn-{self.env_name}",
            
            # Google Maps tools
            "maps_geocode": f"GoogleMapsLambdaArn-{self.env_name}",
            "maps_reverse_geocode": f"GoogleMapsLambdaArn-{self.env_name}",
            "maps_search_places": f"GoogleMapsLambdaArn-{self.env_name}",
            "maps_place_details": f"GoogleMapsLambdaArn-{self.env_name}",
            "maps_distance_matrix": f"GoogleMapsLambdaArn-{self.env_name}",
            "maps_elevation": f"GoogleMapsLambdaArn-{self.env_name}",
            "maps_directions": f"GoogleMapsLambdaArn-{self.env_name}",
            
            # Research tools (Go + Python)
            "research_company": f"WebResearchLambdaArn-{self.env_name}",
            "list_industries": f"FinancialToolsLambdaArn-{self.env_name}",
            "top_industry_companies": f"FinancialToolsLambdaArn-{self.env_name}",
            "top_sector_companies": f"FinancialToolsLambdaArn-{self.env_name}",
            
            # Financial data tools
            "yfinance": f"FinancialToolsLambdaArn-{self.env_name}",
            
            # CloudWatch tools
            "find_log_groups_by_tag": f"CloudWatchToolsLambdaArn-{self.env_name}",
            "execute_query": f"CloudWatchToolsLambdaArn-{self.env_name}",
            "get_query_generation_prompt": f"CloudWatchToolsLambdaArn-{self.env_name}",
            "get_service_graph": f"CloudWatchToolsLambdaArn-{self.env_name}",
        }
        
        # Import ARNs for tools this agent uses
        for tool_id in self.tool_ids:
            if tool_id in tool_stack_exports:
                export_name = tool_stack_exports[tool_id]
                self.tool_lambda_arns[tool_id] = Fn.import_value(export_name)

    def _create_agent_execution_role(self):
        """Create IAM role for Step Functions execution with tool permissions"""
        
        # Create agent-specific log group
        self.log_group = logs.LogGroup(
            self,
            f"{self.agent_name}AgentLogGroup",
            log_group_name=f"/aws/stepfunctions/{self.agent_name}-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        role = iam.Role(
            self,
            f"{self.agent_name}AgentExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com")
        )
        
        # Grant Step Functions logging permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream", 
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams",
                    "logs:DescribeLogGroups"
                ],
                resources=[
                    self.log_group.log_group_arn,
                    f"{self.log_group.log_group_arn}:*"
                ]
            )
        )
        
        # Grant CloudWatch metrics permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"]
            )
        )
        
        # Grant access to DynamoDB tool registry
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ],
                resources=[
                    self.tool_registry_table_arn,
                    f"{self.tool_registry_table_arn}/index/*"
                ]
            )
        )
        
        # Grant access to DynamoDB agent registry
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ],
                resources=[
                    self.agent_registry_table_arn,
                    f"{self.agent_registry_table_arn}/index/*"
                ]
            )
        )
        
        # Grant access to LLM Lambda function
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    self.llm_arn
                ]
            )
        )
        
        # Grant access to tool Lambda functions
        unique_lambda_arns = set(self.tool_lambda_arns.values())
        if unique_lambda_arns:
            role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "lambda:InvokeFunction"
                    ],
                    resources=list(unique_lambda_arns)
                )
            )
        
        # Grant X-Ray permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        self.agent_execution_role = role

    def _create_step_functions_from_template(self):
        """Create Step Functions workflow from dynamic template"""
        
        # Read the template file - now using registry-aware template
        template_path = "step-functions/dynamic-agent-with-registry-template.json"
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace placeholders with actual values
        
        # 1. Replace agent registry table name
        template_content = template_content.replace(
            "AGENT_REGISTRY_TABLE_NAME",
            self.agent_registry_table_name
        )
        
        # 2. Replace agent name
        template_content = template_content.replace(
            "AGENT_NAME",
            self.agent_name
        )
        
        # 3. Replace tool registry table name
        template_content = template_content.replace(
            "TOOL_REGISTRY_TABLE_NAME",
            self.tool_registry_table_name
        )
        
        # 4. Replace LLM Lambda ARN
        template_content = template_content.replace(
            "SHARED_CLAUDE_LAMBDA_ARN",
            self.llm_arn
        )
        
        # 4. Generate dynamic routing choices and execution states
        routing_choices = []
        execution_states = {}
        
        # Create one execution state per TOOL
        for tool_id in self.tool_ids:
            if tool_id in self.tool_lambda_arns:
                actual_lambda_arn = self.tool_lambda_arns[tool_id]
                
                # Create state name based on tool name
                state_name = f"Execute {tool_id.replace('_', ' ').title()} Tool"
                
                # Add routing choice
                choice = {
                    "Next": state_name,
                    "Condition": "{% $states.input.name = \"" + tool_id + "\" %}"
                }
                routing_choices.append(choice)
                
                # Create execution state for this specific tool
                execution_states[state_name] = {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Arguments": {
                        "FunctionName": actual_lambda_arn,
                        "Payload": {
                            "name": "{% $states.input.name %}",
                            "id": "{% $states.input.id %}",
                            "input": "{% $states.input.input %}"
                        }
                    },
                    "Retry": [
                        {
                            "ErrorEquals": [
                                "Lambda.ServiceException",
                                "Lambda.AWSLambdaException", 
                                "Lambda.SdkClientException",
                                "Lambda.TooManyRequestsException"
                            ],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                            "JitterStrategy": "FULL"
                        }
                    ],
                    "End": True,
                    "Comment": f"Execute {tool_id} tool",
                    "Output": "{% $states.result.Payload %}"
                }
        
        # Replace routing choices
        routing_choices_json = json.dumps(routing_choices, indent=6)
        template_content = template_content.replace(
            '"DYNAMIC_ROUTING_CHOICES"',
            routing_choices_json
        )
        
        # Parse template as JSON to add execution states
        template_json = json.loads(template_content)
        
        # Add execution states to the ItemProcessor states
        item_processor_states = template_json["States"]["For each tool use"]["ItemProcessor"]["States"]
        
        # Add each execution state
        for state_name, state_def in execution_states.items():
            item_processor_states[state_name] = state_def
        
        # Convert back to JSON string
        template_content = json.dumps(template_json, indent=2)
        
        # Create the state machine using the processed template
        self.state_machine = sfn.StateMachine(
            self,
            f"{self.agent_name}AgentStateMachine",
            state_machine_name=f"{self.agent_name}-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(template_content),
            role=self.agent_execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )