from aws_cdk import (
    Stack,
    Duration,
    Token,
    RemovalPolicy,
    aws_logs as logs,
    aws_stepfunctions as stepfunctions,
    aws_cloudwatch as cloudwatch,
    aws_lambda as lambda_,
    aws_resourcegroups as resourcegroups,
    aws_iam as iam,
    custom_resources as cr,
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
from typing import List

class AgentMonitoringStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, 
                 agents: List[str],
                 llm_functions: List[str],
                 tool_functions: List[str], 
                 log_group_name: str = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        high_level_facade = MonitoringFacade(
            self,
            "AIAgentMonitoring",
        )
        high_level_facade.add_large_header('AI Agent Monitoring Dashboard')

        # Adding the token metrics
        high_level_facade.add_medium_header('Token Metrics')

        metric_factory = high_level_facade.create_metric_factory()

        input_tokens_metrics = [
            metric_factory.create_metric(
                metric_name='InputTokens',
                namespace="AI-Agents",
                dimensions_map={
                    "state_machine_name": agent_name,
                },
                label=f'Input Tokens - {agent_name}',
                statistic=MetricStatistic.N,
                period=Duration.minutes(5),
            )
            for agent_name in agents
        ]

        output_tokens_metrics = [
            metric_factory.create_metric(
                metric_name='OutputTokens',
                namespace="AI-Agents",
                dimensions_map={
                    "state_machine_name": agent_name,
                },
                label=f'Output Tokens - {agent_name}',
                statistic=MetricStatistic.N,
                period=Duration.minutes(5),
            )
            for agent_name in agents
        ]

        group = CustomMetricGroup(
            metrics=(
                input_tokens_metrics +
                output_tokens_metrics
            ), 
            title='Token Usage'
        )
        high_level_facade.monitor_custom(
            metric_groups=[group], 
            human_readable_name='LLM Token Usage', 
            alarm_friendly_name='Tokens'
        )

        high_level_facade.add_medium_header('AI Agent Step Functions Monitoring')
        agent_step_functions_list = [
            stepfunctions.StateMachine.from_state_machine_name(
                self,
                name,
                name
            ) for name in agents
        ]

        for step_function in agent_step_functions_list:
            high_level_facade.monitor_step_function(
                state_machine=step_function,
            )

        high_level_facade.add_medium_header('AI Agent Lambda Functions Monitoring')

        agent_llm_lambda_functions_list = [
            lambda_.Function.from_function_name(
                self,
                name,
                name
            ) for name in llm_functions
        ]

        high_level_facade.add_widget(cloudwatch.GraphWidget(
            title="LLM Lambda Functions Invocations",
            left=[
                lambda_function.metric_invocations(
                    statistic="sum", 
                    period=Duration.minutes(5),
    
                )
                for lambda_function in agent_llm_lambda_functions_list
            ],
            width=24,
        ))

        agent_tools_lambda_functions_list = [
            lambda_.Function.from_function_name(
                self,
                name,
                name
            ) for name in tool_functions
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

        # Add error widget for all lambda functions that are using the same log group
        high_level_facade.add_widget(cloudwatch.GraphWidget(
            title="Lambda Functions Errors",
            left=[
                lambda_function.metric_errors(
                    statistic="sum",
                    period=Duration.minutes(5),

                )
                for lambda_function in agent_llm_lambda_functions_list + agent_tools_lambda_functions_list
            ],
            width=24,
        ))

        # Since all the lambda functions are using the same log group it is engouh to monitor one of them
        if log_group_name is not None:
            high_level_facade.monitor_log(
                log_group_name=log_group_name,
                human_readable_name='Error logs',
                pattern='ERROR',
                alarm_friendly_name='error logs',
            )
