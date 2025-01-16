from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ecr as ecr,
    aws_ecr_assets as assets,
    aws_apprunner_alpha as apprunner,
    aws_logs as logs,
)
from aws_cdk.aws_ecr_assets import DockerImageAsset, Platform

from constructs import Construct

import json
import os.path as path

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
                "states:ListTagsForResource",
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

        # Build and push the Docker image to ECR
        ui_image_asset = assets.DockerImageAsset(
            self, 
            "AgentUIImage",
            asset_name="step-function-agents-chat-ui",
            directory=path.join(path.dirname(__file__), "../ui"),
            platform=Platform.LINUX_AMD64,
        )

        # Create App Runner service using the pushed image
        ui_hosting_service = apprunner.Service(
            self, 
            'UIHostingService',
            source=apprunner.Source.from_ecr(
                image_configuration=apprunner.ImageConfiguration(
                    port=8080
                ),
                repository=ui_image_asset.repository,
                tag_or_digest=ui_image_asset.image_tag  # Use the tag from the built image
            ),
            auto_deployments_enabled=True,
            service_name="step-function-agents-chat-ui",
            instance_role=ui_backend_role,
        )
