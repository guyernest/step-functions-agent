"""
MCP GraphQL Stack - AppSync API for MCP Registry

This stack creates an AWS AppSync GraphQL API that provides access to the MCP Registry.
It includes resolvers for querying and mutating MCP server records.
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Duration,
    Expiration,
    aws_appsync as appsync,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_logs as logs,
)
from constructs import Construct
import os


class MCPGraphQLStack(Stack):
    """
    Stack for MCP Registry GraphQL API
    Creates AppSync API with Lambda resolvers for MCP server management
    """
    
    def __init__(self, scope: Construct, construct_id: str, 
                 mcp_registry_table_name: str,
                 mcp_registry_table_arn: str,
                 env_name: str = "prod", 
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create Cognito User Pool for authentication (optional)
        self.user_pool = cognito.UserPool(
            self,
            "MCPRegistryUserPool",
            user_pool_name=f"mcp-registry-users-{env_name}",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=False
            ),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=False
                )
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            removal_policy=RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN
        )
        
        # Create AppSync API
        self.graphql_api = appsync.GraphqlApi(
            self,
            "MCPRegistryAPI",
            name=f"MCPRegistryAPI-{env_name}",
            schema=appsync.SchemaFile.from_asset(
                "lambda/graphql/mcp_registry_schema.graphql"
            ),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.API_KEY,
                    api_key_config=appsync.ApiKeyConfig(
                        description=f"API Key for MCP Registry {env_name}",
                        expires=Expiration.after(Duration.days(365))
                    )
                ),
                additional_authorization_modes=[
                    appsync.AuthorizationMode(
                        authorization_type=appsync.AuthorizationType.USER_POOL,
                        user_pool_config=appsync.UserPoolConfig(
                            user_pool=self.user_pool
                        )
                    ),
                    appsync.AuthorizationMode(
                        authorization_type=appsync.AuthorizationType.IAM
                    )
                ]
            ),
            log_config=appsync.LogConfig(
                field_log_level=appsync.FieldLogLevel.ERROR,
                exclude_verbose_content=False,
                retention=logs.RetentionDays.ONE_WEEK
            ),
            xray_enabled=True
        )
        
        # Create Lambda function for resolvers
        self.resolver_lambda = _lambda.Function(
            self,
            "MCPRegistryResolver",
            function_name=f"mcp-registry-resolver-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            handler="mcp_registry_resolver.lambda_handler",
            code=_lambda.Code.from_asset("lambda/graphql"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "TABLE_NAME": mcp_registry_table_name,
                "ENVIRONMENT": env_name,
                "POWERTOOLS_SERVICE_NAME": "mcp-registry-resolver",
                "POWERTOOLS_METRICS_NAMESPACE": "MCPRegistry",
                "LOG_LEVEL": "INFO"
            },
            tracing=_lambda.Tracing.ACTIVE
        )
        
        # Grant permissions to Lambda
        self.resolver_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    mcp_registry_table_arn,
                    f"{mcp_registry_table_arn}/index/*"
                ]
            )
        )
        
        # Grant permissions for Secrets Manager (for API keys)
        self.resolver_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/mcp/servers/*"]
            )
        )
        
        # Create Lambda data source
        lambda_datasource = self.graphql_api.add_lambda_data_source(
            "MCPRegistryLambdaDataSource",
            self.resolver_lambda,
            name=f"MCPRegistryLambdaDS_{env_name}",
            description="Lambda resolver for MCP Registry operations"
        )
        
        # Create resolvers for queries
        queries = [
            "listMCPServersFromRegistry",
            "getMCPServer",
            "listMCPServersByStatus", 
            "listMCPServersByProtocol",
            "testMCPServerConnection"
        ]
        
        for query_name in queries:
            lambda_datasource.create_resolver(
                f"{query_name}Resolver",
                type_name="Query",
                field_name=query_name
            )
        
        # Create resolvers for mutations
        mutations = [
            "registerMCPServer",
            "updateMCPServer",
            "updateMCPServerStatus",
            "approveMCPServer",
            "decommissionMCPServer"
        ]
        
        for mutation_name in mutations:
            lambda_datasource.create_resolver(
                f"{mutation_name}Resolver",
                type_name="Mutation",
                field_name=mutation_name
            )
        
        # Create IAM role for external services to access the API
        self.api_access_role = iam.Role(
            self,
            "MCPRegistryAPIAccessRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description=f"Role for accessing MCP Registry GraphQL API in {env_name}"
        )
        
        self.api_access_role.add_to_policy(
            iam.PolicyStatement(
                actions=["appsync:GraphQL"],
                resources=[f"{self.graphql_api.arn}/*"]
            )
        )
        
        # Outputs
        CfnOutput(
            self,
            "MCPRegistryGraphQLEndpoint",
            value=self.graphql_api.graphql_url,
            export_name=f"MCPRegistryGraphQLEndpoint-{env_name}",
            description="GraphQL endpoint for MCP Registry"
        )
        
        CfnOutput(
            self,
            "MCPRegistryGraphQLApiKey",
            value=self.graphql_api.api_key or "N/A",
            export_name=f"MCPRegistryGraphQLApiKey-{env_name}",
            description="API Key for MCP Registry GraphQL API"
        )
        
        CfnOutput(
            self,
            "MCPRegistryGraphQLApiId",
            value=self.graphql_api.api_id,
            export_name=f"MCPRegistryGraphQLApiId-{env_name}",
            description="AppSync API ID for MCP Registry"
        )
        
        CfnOutput(
            self,
            "MCPRegistryUserPoolId",
            value=self.user_pool.user_pool_id,
            export_name=f"MCPRegistryUserPoolId-{env_name}",
            description="Cognito User Pool ID for MCP Registry"
        )
        
        CfnOutput(
            self,
            "MCPRegistryAPIAccessRoleArn",
            value=self.api_access_role.role_arn,
            export_name=f"MCPRegistryAPIAccessRoleArn-{env_name}",
            description="IAM role ARN for accessing MCP Registry API"
        )