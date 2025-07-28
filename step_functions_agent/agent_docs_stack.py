# This stack deploys the documentation of the AI agents framework to S3.

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
)
from aws_cdk.aws_s3_deployment import Source, BucketDeployment

from constructs import Construct

class AgentDocsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # Createt the bucket that will host the documentation static pages
        docs_bucket = s3.Bucket(self, "AgentDocsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            )
        )

                # Add bucket policy to allow public access to all files
        docs_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[docs_bucket.arn_for_objects("*")],
                principals=[iam.AnyPrincipal()]
            )
        )

        # Deploy website files from a local directory
        deployment = BucketDeployment(self, "DeployWebsiteContent", 
            sources=[Source.asset("docs/build/")],
            destination_bucket=docs_bucket,
            memory_limit=2048  # Increase memory for faster uploads (default is 128MB)
        )