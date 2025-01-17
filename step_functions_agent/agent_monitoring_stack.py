from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_logs as logs,
    aws_stepfunctions as stepfunctions,
    aws_cloudwatch as cloudwatch,
    aws_lambda as lambda_,
)

from constructs import Construct
from cdk_monitoring_constructs import (
    AlarmFactoryDefaults,
    CustomMetricGroup,
    ErrorRateThreshold,
    LatencyThreshold,
    MetricStatistic,
    MonitoringFacade,
    SnsAlarmActionStrategy,
)

import json
import os.path as path

class AgentMonitoringStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        high_level_facade = MonitoringFacade(
            self,
            "AIAgentMonitoring",
        )
        high_level_facade.add_large_header('AI Agent Monitoring Dashboard')

        high_level_facade.add_medium_header('AI Agent Step Functions Monitoring')
        agent_stap_function_names = [
            "SQLAgentWithToolsFlowAndClaude",
            "FiancialAgentWithToolsAndClaude",
            "GoogleMapsAgentWithToolsAndClaude",
            "ForecastingAgentWithToolsAndClaude",
            "ClusteringAgentWithToolsAndClaude",
            "AnalysisAgentWithToolsAndClaude",
            "ResearchAgentWithToolsAndClaude"
        ]
        agent_step_functions_list = [
            stepfunctions.StateMachine.from_state_machine_name(
                self,
                f"{name}SM",
                name
            ) for name in agent_stap_function_names
        ]

        for agent_step_functions in agent_step_functions_list:
            high_level_facade.monitor_step_function(
                state_machine=agent_step_functions,
                add_to_summary_dashboard=True,
            )

        high_level_facade.add_medium_header('AI Agent Tools Lambda Functions Monitoring')

        call_llma_function = lambda_.Function.from_function_name(
            self,
            "CallLLMFunction",
            "CallLLM"
        )
        high_level_facade.monitor_lambda_function(
            lambda_function=call_llma_function,
            add_to_summary_dashboard=True,
        )

        agent_tools_lambda_function_names = [
            "DBInterface",
            "CodeInterpreter",
            "ClusteringTools",
            "ResearchTools",
            "YFinance",
            "AnalysisTools",
            "GoogleMaps"
        ]
        agent_tools_lambda_functions_list = [
            lambda_.Function.from_function_name(
                self,
                f"{name}Tool",
                name
            ) for name in agent_tools_lambda_function_names
        ]

        high_level_facade.add_widget(cloudwatch.GraphWidget(
            title="Agent Tools Lambda Functions Invocations",
            left=[
                lambda_function.metric_invocations(
                    statistic="sum", 
                    period=Duration.minutes(5),
    
                )
                for lambda_function in agent_tools_lambda_functions_list
            ],
            width=24,
        ))

        # for agent_tools_lambda_function in agent_tools_lambda_functions_list:
        #     high_level_facade.monitor_lambda_function(
        #         lambda_function=agent_tools_lambda_function,
        #         add_to_summary_dashboard=True,
        #     )