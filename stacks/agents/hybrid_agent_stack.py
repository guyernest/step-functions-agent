"""
Hybrid Agent Stack - Supports both Lambda tools and nested State Machine agents
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    Fn,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_iam as iam,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct
import json
from typing import Dict, List, Any


class HybridAgentStack(Stack):
    """
    Stack for hybrid agents that can invoke both Lambda tools and other State Machine agents
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import shared LLM function
        self.llm_function = _lambda.Function.from_function_arn(
            self, "SharedLLM",
            Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{self.env_name}")
        )
        
        # Create S3 bucket for web search results
        self.results_bucket = s3.Bucket(
            self, "WebSearchResultsBucket",
            bucket_name=f"web-search-results-{self.env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(7),
                    prefix="results/"
                ),
                s3.LifecycleRule(
                    expiration=Duration.days(1),
                    prefix="screenshots/"
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        
        # Create Nova Act browser tool Lambda
        self.nova_act_browser = self._create_nova_act_browser_lambda()
        
        # Create Web Search Agent state machine
        self.web_search_agent = self._create_web_search_agent()
        
        # Create example Lambda tools
        self.sql_tool = self._create_example_tool("sql_query")
        self.code_tool = self._create_example_tool("code_execute")
        
        # Create hybrid supervisor state machine
        self.hybrid_supervisor = self._create_hybrid_supervisor()
        
        # Output values
        self._create_outputs()
    
    def _create_nova_act_browser_lambda(self) -> _lambda.Function:
        """Create the Nova Act browser automation Lambda"""
        
        role = iam.Role(
            self, "NovaActBrowserRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant S3 permissions
        self.results_bucket.grant_read_write(role)
        
        return _lambda_python.PythonFunction(
            self, "NovaActBrowserFunction",
            function_name=f"nova-act-browser-{self.env_name}",
            entry="lambda/tools/nova_act_browser",
            index="handler.py",
            handler="lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            timeout=Duration.seconds(60),
            memory_size=512,
            role=role,
            environment={
                "RESULTS_BUCKET": self.results_bucket.bucket_name,
                "ENVIRONMENT": self.env_name
            }
        )
    
    def _create_web_search_agent(self) -> sfn.StateMachine:
        """Create the Web Search Agent state machine"""
        
        # Read the state machine definition
        with open("step-functions/web-search-agent.json", "r") as f:
            definition_template = f.read()
        
        # Replace placeholders with actual ARNs
        definition = definition_template.replace(
            "${NovaActBrowserFunction}",
            self.nova_act_browser.function_arn
        )
        
        # Create IAM role for the state machine
        role = iam.Role(
            self, "WebSearchAgentRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                "WebSearchPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["lambda:InvokeFunction"],
                            resources=[self.nova_act_browser.function_arn]
                        ),
                        iam.PolicyStatement(
                            actions=["bedrock:InvokeModel"],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        return sfn.StateMachine(
            self, "WebSearchAgent",
            state_machine_name=f"web-search-agent-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(definition),
            role=role,
            tracing_enabled=True
        )
    
    def _create_example_tool(self, tool_name: str) -> _lambda.Function:
        """Create a placeholder Lambda tool for demonstration"""
        
        return _lambda.Function(
            self, f"{tool_name.title().replace('_', '')}Tool",
            function_name=f"{tool_name}-tool-{self.env_name}",
            code=_lambda.Code.from_inline(f"""
import json

def lambda_handler(event, context):
    # Placeholder tool implementation
    return {{
        'statusCode': 200,
        'tool': '{tool_name}',
        'output': f'Executed {tool_name} with input: {{event}}'
    }}
"""),
            handler="index.lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            timeout=Duration.seconds(30)
        )
    
    def _create_hybrid_supervisor(self) -> sfn.StateMachine:
        """Create the hybrid supervisor state machine"""
        
        # Define available tools and agents
        tools = {
            "sql_query": {
                "arn": self.sql_tool.function_arn,
                "description": "Execute SQL queries against databases"
            },
            "code_execute": {
                "arn": self.code_tool.function_arn,
                "description": "Execute Python code in a sandboxed environment"
            },
            "nova_browser": {
                "arn": self.nova_act_browser.function_arn,
                "description": "Control a browser for web automation"
            }
        }
        
        agents = {
            "web_search": {
                "arn": self.web_search_agent.state_machine_arn,
                "description": "Search web portals and extract information"
            }
        }
        
        # Create the state machine definition with JSONata
        definition = self._generate_hybrid_supervisor_definition(tools, agents)
        
        # Create IAM role
        role = iam.Role(
            self, "HybridSupervisorRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                "SupervisorPolicy": iam.PolicyDocument(
                    statements=[
                        # Lambda invocation for tools and LLM
                        iam.PolicyStatement(
                            actions=["lambda:InvokeFunction"],
                            resources=[
                                self.llm_function.function_arn,
                                *[tool["arn"] for tool in tools.values()]
                            ]
                        ),
                        # State machine execution for agents
                        iam.PolicyStatement(
                            actions=[
                                "states:StartExecution",
                                "states:DescribeExecution",
                                "states:StopExecution"
                            ],
                            resources=[
                                agent["arn"] for agent in agents.values()
                            ]
                        ),
                        # Events for async execution
                        iam.PolicyStatement(
                            actions=["events:PutTargets", "events:PutRule", "events:DescribeRule"],
                            resources=[f"arn:aws:events:{self.region}:{self.account}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule"]
                        )
                    ]
                )
            }
        )
        
        return sfn.StateMachine(
            self, "HybridSupervisor",
            state_machine_name=f"hybrid-supervisor-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(json.dumps(definition)),
            role=role,
            tracing_enabled=True
        )
    
    def _generate_hybrid_supervisor_definition(self, tools: Dict, agents: Dict) -> Dict:
        """Generate the hybrid supervisor state machine definition"""
        
        return {
            "Comment": "Hybrid supervisor that can invoke both Lambda tools and State Machine agents",
            "StartAt": "InitializeConversation",
            
            "States": {
                "InitializeConversation": {
                    "Type": "Pass",
                    "Parameters": {
                        "messages.$": "$.messages",
                        "available_tools": list(tools.keys()),
                        "available_agents": list(agents.keys()),
                        "tool_configs": tools,
                        "agent_configs": agents,
                        "max_iterations.$": "States.Default($.max_iterations, 10)",
                        "iteration_count": 0
                    },
                    "Next": "ProcessWithLLM"
                },
                
                "ProcessWithLLM": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": self.llm_function.function_arn,
                        "Payload": {
                            "messages.$": "$.messages",
                            "available_tools.$": "$.available_tools",
                            "available_agents.$": "$.available_agents",
                            "tool_descriptions.$": "$.tool_configs",
                            "agent_descriptions.$": "$.agent_configs"
                        }
                    },
                    "ResultPath": "$.llm_response",
                    "Next": "CheckIterationLimit"
                },
                
                "CheckIterationLimit": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.iteration_count",
                            "NumericGreaterThanPath": "$.max_iterations",
                            "Next": "MaxIterationsReached"
                        }
                    ],
                    "Default": "RouteAction"
                },
                
                "RouteAction": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.llm_response.Payload.action_type",
                            "StringEquals": "tool",
                            "Next": "InvokeTool"
                        },
                        {
                            "Variable": "$.llm_response.Payload.action_type",
                            "StringEquals": "agent",
                            "Next": "InvokeAgent"
                        },
                        {
                            "Variable": "$.llm_response.Payload.action_type",
                            "StringEquals": "final_answer",
                            "Next": "FormatFinalResponse"
                        }
                    ],
                    "Default": "HandleUnknownAction"
                },
                
                "InvokeTool": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName.$": "States.ArrayGetItem($.tool_configs.*.arn, States.ArrayContains($.available_tools, $.llm_response.Payload.tool_name))",
                        "Payload.$": "$.llm_response.Payload.tool_input"
                    },
                    "ResultPath": "$.tool_result",
                    "Next": "AppendToolMessage"
                },
                
                "InvokeAgent": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::states:startExecution.sync:2",
                    "Parameters": {
                        "StateMachineArn.$": "States.ArrayGetItem($.agent_configs.*.arn, States.ArrayContains($.available_agents, $.llm_response.Payload.agent_name))",
                        "Input": {
                            "messages.$": "$.messages",
                            "agent_config.$": "$.llm_response.Payload.agent_config",
                            "session_id.$": "$$.Execution.Name"
                        }
                    },
                    "ResultPath": "$.agent_result",
                    "OutputPath": "$.agent_result.Output",
                    "Next": "AppendAgentMessages"
                },
                
                "AppendToolMessage": {
                    "Type": "Pass",
                    "Parameters": {
                        "messages.$": "States.Array($.messages[0], States.StringToJson(States.Format('[{\"role\":\"tool\",\"tool_name\":\"{}\",\"content\":\"{}\"}]', $.llm_response.Payload.tool_name, $.tool_result.Payload.output)))",
                        "available_tools.$": "$.available_tools",
                        "available_agents.$": "$.available_agents",
                        "tool_configs.$": "$.tool_configs",
                        "agent_configs.$": "$.agent_configs",
                        "max_iterations.$": "$.max_iterations",
                        "iteration_count.$": "States.MathAdd($.iteration_count, 1)"
                    },
                    "Next": "ProcessWithLLM"
                },
                
                "AppendAgentMessages": {
                    "Type": "Pass",
                    "Parameters": {
                        "messages.$": "States.Array($.messages[0], $.agent_messages[0])",
                        "available_tools.$": "$.available_tools",
                        "available_agents.$": "$.available_agents",
                        "tool_configs.$": "$.tool_configs",
                        "agent_configs.$": "$.agent_configs",
                        "max_iterations.$": "$.max_iterations",
                        "iteration_count.$": "States.MathAdd($.iteration_count, 1)"
                    },
                    "Next": "ProcessWithLLM"
                },
                
                "FormatFinalResponse": {
                    "Type": "Pass",
                    "Parameters": {
                        "final_answer.$": "$.llm_response.Payload.final_answer",
                        "conversation.$": "$.messages",
                        "metadata": {
                            "iterations.$": "$.iteration_count",
                            "execution_id.$": "$$.Execution.Name"
                        }
                    },
                    "End": True
                },
                
                "MaxIterationsReached": {
                    "Type": "Pass",
                    "Parameters": {
                        "error": "Maximum iterations reached",
                        "iterations.$": "$.iteration_count",
                        "last_response.$": "$.llm_response"
                    },
                    "End": True
                },
                
                "HandleUnknownAction": {
                    "Type": "Fail",
                    "Error": "UnknownAction",
                    "Cause": "LLM returned an unknown action type"
                }
            }
        }
    
    def _create_outputs(self):
        """Create stack outputs"""
        
        CfnOutput(
            self, "HybridSupervisorArn",
            value=self.hybrid_supervisor.state_machine_arn,
            description="ARN of the hybrid supervisor state machine"
        )
        
        CfnOutput(
            self, "WebSearchAgentArn",
            value=self.web_search_agent.state_machine_arn,
            description="ARN of the web search agent state machine"
        )
        
        CfnOutput(
            self, "NovaActBrowserArn",
            value=self.nova_act_browser.function_arn,
            description="ARN of the Nova Act browser Lambda function"
        )
        
        CfnOutput(
            self, "ResultsBucketName",
            value=self.results_bucket.bucket_name,
            description="Name of the S3 bucket for search results"
        )