from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_apprunner_alpha as apprunner,
    aws_logs as logs,
)
from constructs import Construct

import json

class AgentUIStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # Create the role for the UI backend
        ui_backend_role = iam.Role(self, "UI Backend Role",
            role_name=f"AppRunnerAgentUIRole-{self.region}",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
        )

        # Adding the permission to write to the X-Ray Daemon
        ui_backend_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AWSXRayDaemonWriteAccess"
            )
        )

        # Adding the permission to read from the parameter store
        ui_backend_role.add_to_policy(iam.PolicyStatement(
            sid="ReadSSM",
            effect=iam.Effect.ALLOW,
            actions=[
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath",
            ],
            resources=[
                f"arn:aws:ssm:{self.region}:{self.account}:parameter/ai-agents/*"
            ]
        ))

        # Adding the permission to list, start and describe the step functions agents
        ui_backend_role.add_to_policy(iam.PolicyStatement(
            sid="StartStepFunctionsAgents",
            effect=iam.Effect.ALLOW,
            actions=[
                "states:ListStateMachines",
                "states:StartExecution",
                "states:DescribeExecution",
            ],
            resources=[
                "*"
            ]
        ))

        # Adding the permission to write to the CloudWatch Logs
        ui_backend_role.add_to_policy(iam.PolicyStatement(
            sid="WriteLogs",
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:PutLogEvents",
                "logs:CreateLogStream",
                "logs:CreateLogGroup",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups",
                "logs:FilterLogEvents",
            ],
            resources=[
                f"arn:aws:logs:{self.region}:{self.account}:log-group:*",
                f"arn:aws:logs:{self.region}:{self.account}:log-group:*:log-stream:*"
            ]
        ))

        github_connection_arn = ssm.StringParameter.value_for_string_parameter(
            self, 
            "/step-function-agents/GitHubConnection"
        )

        repository_url = ssm.StringParameter.value_for_string_parameter(
            self, 
            "/step-function-agents/GitHubRepositoryURL"
        )

        # Create the UI backend using App Runner
        ui_hosting_service = apprunner.Service(
            self, 
            'Service', 
            source=apprunner.Source.from_git_hub(
                configuration_source= apprunner.ConfigurationSourceType.REPOSITORY,
                repository_url= repository_url,
                branch= 'main',
                connection= apprunner.GitHubConnection.from_connection_arn(github_connection_arn),
            ),
            service_name= "step-function-agents-chat-ui",
            auto_deployments_enabled= True,
            instance_role=ui_backend_role,
        )

        # Override the value of the SourceConfiguration.CodeRepository.SourceCodeVersion.
        # to the right value of "ui"
        ui_hosting_service.node.default_child.add_override(
            "Properties.SourceConfiguration.CodeRepository.SourceDirectory", 
            "ui"
        )
