"""
AgentCore Runtime Construct - Reusable L2-like wrapper for CfnRuntime

This construct simplifies the deployment of AWS Bedrock AgentCore runtimes by:
1. Creating ECR repository for the agent container
2. Setting up IAM role with required permissions
3. Deploying the CfnRuntime with proper configuration
4. Outputting runtime ARN and endpoint for consumption by Lambda tools

Usage:
    runtime = AgentCoreRuntimeConstruct(
        self, "BroadbandAgent",
        runtime_name="broadband_checker_agent",
        container_uri="123456789012.dkr.ecr.us-west-2.amazonaws.com/broadband-agent:latest",
        description="UK broadband availability checker using Nova Act",
        environment_variables={"AWS_REGION": "us-west-2"},
        protocol="HTTP"
    )
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_bedrockagentcore as agentcore,
    RemovalPolicy
)
from constructs import Construct
from typing import Dict, Optional


class AgentCoreRuntimeConstruct(Construct):
    """
    Reusable construct for deploying Bedrock AgentCore runtimes

    Creates:
    - ECR repository for agent container
    - IAM execution role with AgentCore permissions
    - CfnRuntime resource with container configuration
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        runtime_name: str,
        container_uri: Optional[str] = None,
        description: str = "",
        environment_variables: Optional[Dict[str, str]] = None,
        protocol: str = "HTTP",
        network_mode: str = "PUBLIC",
        create_ecr_repository: bool = True,
        env_name: str = "prod",
        **kwargs
    ) -> None:
        """
        Initialize AgentCore Runtime construct

        Args:
            scope: CDK construct scope
            construct_id: Unique construct ID
            runtime_name: Name for the AgentCore runtime (must match [a-zA-Z][a-zA-Z0-9_]{0,47})
            container_uri: ECR container URI (if not provided, will use created ECR repo)
            description: Description of the agent runtime
            environment_variables: Environment variables for the agent container
            protocol: Protocol configuration (HTTP or MCP)
            network_mode: Network mode (PUBLIC or VPC)
            create_ecr_repository: Whether to create an ECR repository
            env_name: Environment name for tagging
        """
        super().__init__(scope, construct_id, **kwargs)

        self.runtime_name = runtime_name
        self.env_name = env_name

        # Create ECR repository for agent container (if requested)
        if create_ecr_repository:
            repo_name = f"bedrock-agentcore-{runtime_name}"
            self.ecr_repository = ecr.Repository(
                self, "Repository",
                repository_name=repo_name,
                removal_policy=RemovalPolicy.DESTROY,  # Allow deletion
                image_scan_on_push=True,
                lifecycle_rules=[
                    ecr.LifecycleRule(
                        description="Keep last 10 images",
                        max_image_count=10
                    )
                ]
            )

            # Use the repository URI if container_uri not provided
            if not container_uri:
                container_uri = f"{self.ecr_repository.repository_uri}:latest"

        elif not container_uri:
            raise ValueError("Either create_ecr_repository must be True or container_uri must be provided")

        self.container_uri = container_uri

        # Create IAM execution role for AgentCore runtime
        self.execution_role = iam.Role(
            self, "ExecutionRole",
            role_name=f"BedrockAgentCoreRuntime-{runtime_name}-{env_name}",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description=f"Execution role for AgentCore runtime {runtime_name}",
        )

        # Grant permissions for AgentCore runtime
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockAgentCoreRuntimePermissions",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )
        )

        # Grant ECR pull permissions
        if create_ecr_repository:
            self.ecr_repository.grant_pull(self.execution_role)
        else:
            # Grant generic ECR pull permissions if using external repository
            self.execution_role.add_to_policy(
                iam.PolicyStatement(
                    sid="ECRPullPermissions",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:GetAuthorizationToken"
                    ],
                    resources=["*"]
                )
            )

        # Create CfnRuntime
        self.runtime = agentcore.CfnRuntime(
            self, "Runtime",
            agent_runtime_name=runtime_name,
            role_arn=self.execution_role.role_arn,
            agent_runtime_artifact=agentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=agentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=container_uri
                )
            ),
            network_configuration=agentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode=network_mode
            ),
            description=description or f"AgentCore runtime for {runtime_name}",
            environment_variables=environment_variables or {},
            protocol_configuration=protocol,
        )

        # Make runtime depend on role and ECR repository to ensure proper creation order
        self.runtime.node.add_dependency(self.execution_role)
        if create_ecr_repository and hasattr(self, 'ecr_repository'):
            self.runtime.node.add_dependency(self.ecr_repository)

        # Store runtime ARN for consumption
        self.runtime_arn = self.runtime.attr_agent_runtime_arn
        self.runtime_id = self.runtime.ref

        # Create outputs (replace underscores with hyphens for CloudFormation export names)
        safe_runtime_name = runtime_name.replace('_', '-')

        CfnOutput(
            self, "RuntimeArn",
            value=self.runtime_arn,
            description=f"ARN of the AgentCore runtime for {runtime_name}",
            export_name=f"AgentCoreRuntime-{safe_runtime_name}-{env_name}-Arn"
        )

        CfnOutput(
            self, "RuntimeId",
            value=self.runtime_id,
            description=f"ID of the AgentCore runtime for {runtime_name}",
            export_name=f"AgentCoreRuntime-{safe_runtime_name}-{env_name}-Id"
        )

        if create_ecr_repository:
            CfnOutput(
                self, "RepositoryUri",
                value=self.ecr_repository.repository_uri,
                description=f"ECR repository URI for {runtime_name}",
                export_name=f"AgentCoreRuntime-{safe_runtime_name}-{env_name}-RepositoryUri"
            )

    def grant_invoke(self, grantee: iam.IGrantable) -> iam.Grant:
        """
        Grant permissions to invoke this AgentCore runtime

        Args:
            grantee: The principal to grant permissions to (e.g., Lambda function)

        Returns:
            The Grant object
        """
        return iam.Grant.add_to_principal(
            actions=[
                "bedrock-agentcore:InvokeAgent",
                "bedrock-agentcore:InvokeAgentRuntime",
                "bedrock-agentcore:*"
            ],
            grantee=grantee,
            resource_arns=[self.runtime_arn]
        )
