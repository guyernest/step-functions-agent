"""
AgentCore S3 Permissions Stack

Adds S3 permissions to AgentCore runtime execution roles for Nova Act recordings.
This stack grants permissions to existing roles created by the agentcore CLI.
"""

from aws_cdk import (
    Stack,
    aws_iam as iam,
)
from constructs import Construct


class AgentCoreS3PermissionsStack(Stack):
    """
    Stack that adds S3 permissions to AgentCore runtime execution roles
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "prod",
        agent_runtime_role_name: str = None,
        recordings_bucket_name: str = None,
        **kwargs
    ) -> None:
        """
        Initialize the S3 permissions stack

        Args:
            scope: CDK construct scope
            construct_id: Unique stack ID
            env_name: Environment name (prod, dev, etc.)
            agent_runtime_role_name: Name of the AgentCore runtime execution role
            recordings_bucket_name: Name of the S3 bucket for Nova Act recordings
        """
        super().__init__(scope, construct_id, **kwargs)

        if not agent_runtime_role_name:
            raise ValueError("agent_runtime_role_name is required")

        if not recordings_bucket_name:
            raise ValueError("recordings_bucket_name is required")

        # Import the existing AgentCore runtime role
        agent_role = iam.Role.from_role_name(
            self, "AgentCoreRuntimeRole",
            role_name=agent_runtime_role_name
        )

        # Add S3 permissions for Nova Act recordings
        iam.Policy(
            self, "NovaActS3RecordingsPolicy",
            policy_name=f"NovaActS3Recordings-{env_name}",
            roles=[agent_role],
            statements=[
                iam.PolicyStatement(
                    sid="NovaActS3RecordingsAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:HeadBucket",
                        "s3:ListBucket",
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:DeleteObject"
                    ],
                    resources=[
                        f"arn:aws:s3:::{recordings_bucket_name}",
                        f"arn:aws:s3:::{recordings_bucket_name}/*"
                    ]
                )
            ]
        )
