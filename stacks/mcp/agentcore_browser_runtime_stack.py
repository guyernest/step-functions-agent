"""
AgentCore Browser Runtime Stack

Deploys the browser automation agents to AWS Bedrock AgentCore runtime:
1. browser_broadband - UK broadband availability checker
2. browser_shopping - E-commerce product search
3. browser_search - General web search and extraction

Each agent is deployed as a containerized AgentCore runtime that the
AgentCoreBrowserToolStack Lambda function can invoke.

Architecture:
- ECR repositories for each agent's Docker image
- IAM roles with AgentCore execution permissions
- CfnRuntime resources for each agent
- Outputs agent ARNs for consumption by Lambda tool
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_s3 as s3,
)
from constructs import Construct
from stacks.shared.agentcore_runtime_construct import AgentCoreRuntimeConstruct
from typing import Dict


class AgentCoreBrowserRuntimeStack(Stack):
    """
    Stack that deploys browser automation agents to AgentCore runtime
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "prod",
        **kwargs
    ) -> None:
        """
        Initialize the AgentCore Browser Runtime Stack

        Args:
            scope: CDK construct scope
            construct_id: Unique stack ID
            env_name: Environment name (prod, dev, etc.)
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name

        # Create CodeBuild project for building container images
        self._create_codebuild_project()

        # Agent configurations
        # Note: Using 'cdk_' prefix to avoid conflicts with existing starter-toolkit deployments
        # Runtime names must match pattern: [a-zA-Z][a-zA-Z0-9_]{0,47} (no hyphens allowed!)
        # These agents need to be built and pushed to ECR before deployment
        # See docs/AGENTCORE_BROWSER_DEPLOYMENT.md for build instructions
        agent_configs = [
            {
                "id": "BroadbandAgent",
                "runtime_name": "cdk_broadband_checker_agent",
                "description": "UK broadband availability checker using BT Wholesale portal and Nova Act browser automation",
                "env_vars": {
                    "AWS_REGION": self.region,
                    "AGENT_TYPE": "broadband",
                    "LOG_LEVEL": "INFO",
                    "IMAGE_VERSION": "v2-with-nova-act"  # Force runtime update
                }
            },
            {
                "id": "ShoppingAgent",
                "runtime_name": "cdk_shopping_agent",
                "description": "E-commerce product search and price comparison on Amazon and eBay using Nova Act browser automation",
                "env_vars": {
                    "AWS_REGION": self.region,
                    "AGENT_TYPE": "shopping",
                    "LOG_LEVEL": "INFO",
                    "IMAGE_VERSION": "v2-with-nova-act"  # Force runtime update
                }
            },
            {
                "id": "SearchAgent",
                "runtime_name": "cdk_web_search_agent",
                "description": "General web search and information extraction using Nova Act browser automation",
                "env_vars": {
                    "AWS_REGION": self.region,
                    "AGENT_TYPE": "search",
                    "LOG_LEVEL": "INFO",
                    "IMAGE_VERSION": "v2-with-nova-act"  # Force runtime update
                }
            }
        ]

        # Deploy each agent runtime
        # Note: ECR repositories are created manually via Makefile
        # to avoid chicken-and-egg problem with image validation
        self.agent_runtimes: Dict[str, AgentCoreRuntimeConstruct] = {}

        for config in agent_configs:
            # Construct container URI from manually-created ECR repository
            repo_name = f"bedrock-agentcore-{config['runtime_name']}"
            container_uri = f"{self.account}.dkr.ecr.{self.region}.amazonaws.com/{repo_name}:latest"

            runtime = AgentCoreRuntimeConstruct(
                self,
                config["id"],
                runtime_name=config["runtime_name"],
                container_uri=container_uri,
                description=config["description"],
                environment_variables=config["env_vars"],
                protocol="HTTP",
                network_mode="PUBLIC",
                create_ecr_repository=False,  # ECR repos created manually
                env_name=env_name
            )

            self.agent_runtimes[config["runtime_name"]] = runtime

        # Create stack outputs with all agent ARNs for Lambda consumption
        self._create_outputs()

    def _create_codebuild_project(self):
        """Create CodeBuild project for building AgentCore browser container images"""

        # CodeBuild IAM role
        codebuild_role = iam.Role(
            self,
            "CodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            description="Role for CodeBuild to build AgentCore browser containers"
        )

        # Grant ECR permissions
        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:PutImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload"
                ],
                resources=["*"]
            )
        )

        # Grant CloudWatch Logs permissions
        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/codebuild/*"]
            )
        )

        # Grant S3 permissions for source artifacts
        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion"
                ],
                resources=[f"arn:aws:s3:::codebuild-{self.account}-{self.region}/agentcore-browser-build/*"]
            )
        )

        # Create CodeBuild project
        # Using inline buildspec to avoid source chicken-and-egg problem
        # Source will be provided via start-build --source-location CLI parameter
        self.codebuild_project = codebuild.Project(
            self,
            "ContainerBuildProject",
            project_name=f"agentcore-browser-build-{self.env_name}",
            description="Build AgentCore browser agent containers with Nova Act",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.LARGE,
                privileged=True  # Required for Docker builds
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": 0.2,
                "phases": {
                    "pre_build": {
                        "commands": [
                            "echo Logging in to Amazon ECR...",
                            "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com",
                            "IMAGE_TAG=latest",
                            "echo Build started on `date`",
                            "echo Building the Docker image for $IMAGE_REPO_NAME"
                        ]
                    },
                    "build": {
                        "commands": [
                            "docker build --platform linux/arm64 -t $IMAGE_REPO_NAME:$IMAGE_TAG .",
                            "docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG",
                            "docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:latest"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "echo Build completed on `date`",
                            "echo Pushing the Docker images...",
                            "docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG",
                            "docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:latest",
                            "echo Successfully pushed $IMAGE_REPO_NAME:latest to ECR"
                        ]
                    }
                }
            }),
            role=codebuild_role,
            timeout=Duration.minutes(60)  # Container builds can take time
        )

        # Output CodeBuild project name
        CfnOutput(
            self,
            "CodeBuildProjectName",
            value=self.codebuild_project.project_name,
            description="CodeBuild project for building AgentCore browser containers",
            export_name=f"AgentCoreBrowser-CodeBuildProject-{self.env_name}"
        )

    def _create_outputs(self):
        """Create stack outputs for agent ARNs"""

        # Individual agent ARNs (replace underscores with hyphens in export names)
        for name, runtime in self.agent_runtimes.items():
            safe_name = name.replace('_', '-')
            CfnOutput(
                self,
                f"{name.title().replace('_', '')}Arn",
                value=runtime.runtime_arn,
                description=f"AgentCore runtime ARN for {name}",
                export_name=f"AgentCoreBrowser-{safe_name}-{self.env_name}-Arn"
            )

        # Combined output as JSON for easy Lambda consumption
        import json
        agent_arns_map = {
            "browser_broadband": self.agent_runtimes["cdk_broadband_checker_agent"].runtime_arn,
            "browser_shopping": self.agent_runtimes["cdk_shopping_agent"].runtime_arn,
            "browser_search": self.agent_runtimes["cdk_web_search_agent"].runtime_arn
        }

        CfnOutput(
            self,
            "AgentArnsJson",
            value=json.dumps(agent_arns_map),
            description="JSON map of tool names to agent ARNs",
            export_name=f"AgentCoreBrowser-AgentArns-{self.env_name}"
        )

        # ECR repository URIs for build/push operations
        CfnOutput(
            self,
            "BroadbandRepositoryUri",
            value=self.agent_runtimes["cdk_broadband_checker_agent"].container_uri.rsplit(':', 1)[0],
            description="ECR repository for broadband agent container"
        )

        CfnOutput(
            self,
            "ShoppingRepositoryUri",
            value=self.agent_runtimes["cdk_shopping_agent"].container_uri.rsplit(':', 1)[0],
            description="ECR repository for shopping agent container"
        )

        CfnOutput(
            self,
            "SearchRepositoryUri",
            value=self.agent_runtimes["cdk_web_search_agent"].container_uri.rsplit(':', 1)[0],
            description="ECR repository for search agent container"
        )

    def get_agent_runtime(self, runtime_name: str) -> AgentCoreRuntimeConstruct:
        """
        Get a specific agent runtime by name

        Args:
            runtime_name: Name of the runtime (e.g., 'broadband_checker_agent')

        Returns:
            The AgentCoreRuntimeConstruct

        Raises:
            KeyError: If runtime name not found
        """
        return self.agent_runtimes[runtime_name]
