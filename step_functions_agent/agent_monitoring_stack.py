from aws_cdk import (
    Stack,
    Duration,
    aws_stepfunctions as stepfunctions,
    aws_cloudwatch as cloudwatch,
    aws_lambda as lambda_,
)

from constructs import Construct
from cdk_monitoring_constructs import (
    CustomMetricGroup,
    MetricStatistic,
    MonitoringFacade,
)

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

        # metric_factory = high_level_facade.create_metric_factory()

        # input_tokens_metrics = [
        #     metric_factory.create_metric(
        #         metric_name='InputTokens',
        #         namespace="AI-Agents",
        #         dimensions_map={
        #             "state_machine_name": agent_name,
        #         },
        #         label=f'Input Tokens - {agent_name}',
        #         statistic=MetricStatistic.N,
        #         period=Duration.minutes(5),
        #     )
        #     for agent_name in agents
        # ]

        # output_tokens_metrics = [
        #     metric_factory.create_metric(
        #         metric_name='OutputTokens',
        #         namespace="AI-Agents",
        #         dimensions_map={
        #             "state_machine_name": agent_name,
        #         },
        #         label=f'Output Tokens - {agent_name}',
        #         statistic=MetricStatistic.SUM,
        #         period=Duration.minutes(5),
        #     )
        #     for agent_name in agents
        # ]

        # token_usage_group = CustomMetricGroup(
        #     metrics=(
        #         input_tokens_metrics +
        #         output_tokens_metrics
        #     ), 
        #     title='Token Usage'
        # )
        # high_level_facade.monitor_custom(
        #     metric_groups=[token_usage_group], 
        #     human_readable_name='LLM Token Usage', 
        #     alarm_friendly_name='Tokens',
        # )

        for agent in agents:
            high_level_facade.add_medium_header(f'Agent: {agent}')

             # Create the query
            input_tokens_query = cloudwatch.MathExpression(
                expression=f"SELECT SUM(InputTokens) FROM \"AI-Agents\" WHERE state_machine_name = '{agent}' GROUP BY model",
                label="Input Tokens"  # Label that will appear on the dashboard
            )

            input_tokens_widget = cloudwatch.GraphWidget(
                title="Top Models by Input Tokens",
                left=[input_tokens_query],
                width=12  # Setting width to half the dashboard (24 units is full width)
            )

            output_tokens_query = cloudwatch.MathExpression(
                expression=f"SELECT SUM(OutputTokens) FROM \"AI-Agents\" WHERE state_machine_name = '{agent}' GROUP BY model",
                label="Output Tokens"  # Label that will appear on the dashboard
            )

            output_tokens_widget = cloudwatch.GraphWidget(
                title="Top Models by Output Tokens",
                left=[output_tokens_query],
                width=12  # Setting width to half the dashboard
            )

            # Add them as a row 
            high_level_facade.add_widget(
                cloudwatch.Row(
                    input_tokens_widget,
                    output_tokens_widget
                )
            )

        # Calculate the total cost of tokens. We use the model dimensions to get the cost per token.
        # We use the input and output tokens to calculate the cost.
        # We use the following pricing:
        # gpt-4: input $0.03 / 1K tokens, output $0.06 / 1K tokens
        # gpt-3.5-turbo: input $0.0015 / 1K tokens, output $0.002 / 1K tokens


            # Create the math expression
        math_expression = cloudwatch.MathExpression(
            expression="""
            SUM(SEARCH('{AI-Agents,model,state_machine_name} InputTokens gpt-4o', 'Sum')) * 2.50 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} OutputTokens gpt-4o', 'Sum')) * 10.00 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} InputTokens gpt-4o-mini', 'Sum')) * 0.15 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} OutputTokens gpt-4o-mini', 'Sum')) * 0.60 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} InputTokens claude sonnet', 'Sum')) * 3.00 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} OutputTokens claude sonnet', 'Sum')) * 15.00 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} InputTokens gemini-2.0-flash', 'Sum')) * 0.10 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} OutputTokens gemini-2.0-flash', 'Sum')) * 0.40 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} InputTokens amazon.nova-pro', 'Sum')) * 0.8 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} OutputTokens amazon.nova-pro', 'Sum')) * 3.20 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} InputTokens grok-2', 'Sum')) * 2.0 / 10^6 +
            SUM(SEARCH('{AI-Agents,model,state_machine_name} OutputTokens grok-2', 'Sum')) * 10.00 / 10^6
            """,
            label="Cost Calculation"  # Label that will appear on the dashboard
        )

        # Add the math expression to the dashboard
        high_level_facade.add_widget(
            cloudwatch.GraphWidget(
                title="Model Usage Cost (USD)",
                left=[math_expression],
            ),
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
