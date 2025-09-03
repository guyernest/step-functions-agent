from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    Fn,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy,
    custom_resources as cr
)
from constructs import Construct
from .naming_conventions import NamingConventions
import json


class SharedInfrastructureStack(Stack):
    """
    Shared Infrastructure Stack - Core infrastructure components
    
    This stack creates and manages shared infrastructure components that are
    used across multiple stacks:
    - DynamoDB Tool Registry
    - Common IAM policies and roles
    - Shared monitoring and logging resources
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create DynamoDB tool registry
        self._create_tool_registry()
        
        # Create consolidated tool secrets infrastructure
        self._create_tool_secrets_infrastructure()
        
        # Create shared Custom Resource provider for DynamoDB operations
        self._create_shared_custom_resource_provider()
        
        # Create stack exports
        self._create_stack_exports()

    def _create_tool_registry(self):
        """Create DynamoDB table for tool registry"""
        table_name = NamingConventions.tool_registry_table_name(self.env_name)
        
        self.tool_registry_table = dynamodb.Table(
            self,
            "ToolRegistry",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="tool_name",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # TODO: Change for production
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        # Global Secondary Index: Tools by Language
        self.tool_registry_table.add_global_secondary_index(
            index_name="ToolsByLanguage",
            partition_key=dynamodb.Attribute(
                name="language",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="tool_name",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Global Secondary Index: Tools by Status
        self.tool_registry_table.add_global_secondary_index(
            index_name="ToolsByStatus",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Global Secondary Index: Tools by Author
        self.tool_registry_table.add_global_secondary_index(
            index_name="ToolsByAuthor",
            partition_key=dynamodb.Attribute(
                name="author",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )


    def _create_tool_secrets_infrastructure(self):
        """Create consolidated tool secrets infrastructure"""
        
        # Create the consolidated secret with empty initial structure
        self.tool_secrets = secretsmanager.Secret(
            self,
            "ConsolidatedToolSecrets",
            secret_name=f"/ai-agent/tool-secrets/{self.env_name}",
            description=f"Consolidated secrets for all tools in {self.env_name} environment",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{}',
                generate_string_key='placeholder'
            )
        )
        
        # Create DynamoDB table for tool secrets registry
        self.tool_secrets_table = dynamodb.Table(
            self,
            "ToolSecretsRegistry",
            table_name=f"ToolSecrets-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="tool_name",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            )
        )
        
        # Create Lambda execution role for secret structure manager
        secret_manager_role = iam.Role(
            self,
            "SecretStructureManagerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant permissions to manage the consolidated secret
        secret_manager_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:UpdateSecret"
                ],
                resources=[self.tool_secrets.secret_arn]
            )
        )
        
        # Grant permissions to read/write the registry table
        self.tool_secrets_table.grant_read_write_data(secret_manager_role)
        
        # Create Lambda function for managing secret structure
        self.secret_structure_manager = _lambda_python.PythonFunction(
            self,
            "SecretStructureManager",
            function_name=f"tool-secrets-manager-{self.env_name}",
            description="Manages the structure of consolidated tool secrets",
            entry="lambda/shared/secret-structure-manager",
            index="index.py",
            handler="handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            timeout=Duration.seconds(60),
            memory_size=256,
            architecture=_lambda.Architecture.ARM_64,
            role=secret_manager_role,
            environment={
                "CONSOLIDATED_SECRET_NAME": self.tool_secrets.secret_name,
                "TOOL_SECRETS_TABLE_NAME": self.tool_secrets_table.table_name,
                "ENVIRONMENT": self.env_name
            }
        )

    def _create_shared_custom_resource_provider(self):
        """Create a shared Custom Resource provider for DynamoDB operations"""
        
        # Create a Lambda role for the shared Custom Resource handler
        shared_cr_role = iam.Role(
            self,
            "SharedCustomResourceRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant DynamoDB permissions to the role
        shared_cr_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:BatchWriteItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    self.tool_registry_table.table_arn,
                    self.tool_secrets_table.table_arn,
                    f"{self.tool_registry_table.table_arn}/index/*",
                    f"{self.tool_secrets_table.table_arn}/index/*"
                ]
            )
        )
        
        # Create the Lambda function for handling Custom Resource requests
        self.shared_cr_lambda = _lambda.Function(
            self,
            "SharedCustomResourceLambda",
            function_name=f"shared-custom-resource-{self.env_name}",
            description="Shared Custom Resource handler for DynamoDB operations across all tool stacks",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import urllib3

http = urllib3.PoolManager()
dynamodb = boto3.client('dynamodb')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    response_status = "SUCCESS"
    response_data = {}
    physical_resource_id = event.get('PhysicalResourceId', context.log_stream_name)
    
    try:
        request_type = event['RequestType']
        properties = event['ResourceProperties']
        
        # Extract DynamoDB operation details
        service = properties.get('Service', 'dynamodb')
        action = properties.get('Action')
        parameters = json.loads(properties.get('Parameters', '{}'))
        
        print(f"Service: {service}, Action: {action}")
        print(f"Parameters: {json.dumps(parameters)}")
        
        if service != 'dynamodb':
            raise ValueError(f"Unsupported service: {service}")
        
        # Execute the DynamoDB operation
        if request_type in ['Create', 'Update']:
            if action == 'batchWriteItem':
                print(f"Executing batchWriteItem with {len(parameters.get('RequestItems', {}))} tables")
                response = dynamodb.batch_write_item(**parameters)
                unprocessed = response.get('UnprocessedItems', {})
                if unprocessed:
                    print(f"Warning: Unprocessed items: {json.dumps(unprocessed)}")
                response_data = {'UnprocessedItems': unprocessed}
                print(f"BatchWriteItem response: {json.dumps(response)}")
            elif action == 'putItem':
                print(f"Executing putItem")
                response = dynamodb.put_item(**parameters)
                response_data = {'Item': 'Created'}
                print(f"PutItem response: {json.dumps(response)}")
            elif action == 'deleteItem':
                print(f"Executing deleteItem")
                response = dynamodb.delete_item(**parameters)
                response_data = {'Item': 'Deleted'}
            else:
                raise ValueError(f"Unsupported action: {action}")
        elif request_type == 'Delete':
            # Handle delete operations
            delete_params = json.loads(properties.get('DeleteParameters', '{}'))
            if delete_params:
                print(f"Executing delete with action: {action}")
                if action == 'batchWriteItem':
                    response = dynamodb.batch_write_item(**delete_params)
                elif action == 'deleteItem':
                    response = dynamodb.delete_item(**delete_params)
                print(f"Delete response: {json.dumps(response)}")
            response_data = {'Deleted': True}
            
    except Exception as e:
        print(f"Error executing DynamoDB operation: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        response_status = "FAILED"
        response_data = {'Error': str(e)}
    
    # Send response back to CloudFormation
    response_url = event['ResponseURL']
    response_body = {
        'Status': response_status,
        'Reason': f"See CloudWatch Log Stream: {context.log_stream_name}",
        'PhysicalResourceId': physical_resource_id,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': response_data
    }
    
    json_response_body = json.dumps(response_body)
    headers = {'content-type': '', 'content-length': str(len(json_response_body))}
    
    try:
        response = http.request('PUT', response_url, headers=headers, body=json_response_body)
        print(f"CloudFormation response status: {response.status}")
    except Exception as e:
        print(f"Failed to send response to CloudFormation: {str(e)}")
    
    return response_data
            """),
            timeout=Duration.seconds(60),
            role=shared_cr_role
        )
        
        # Create a provider that wraps the Lambda function
        self.shared_cr_provider = cr.Provider(
            self,
            "SharedDynamoDBProvider",
            on_event_handler=self.shared_cr_lambda
        )

    def _create_stack_exports(self):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export tool registry table name
        CfnOutput(
            self,
            "ToolRegistryTableName",
            value=self.tool_registry_table.table_name,
            export_name=NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name),
            description="Name of the tool registry DynamoDB table"
        )

        # Export tool registry table ARN
        CfnOutput(
            self,
            "ToolRegistryTableArn",
            value=self.tool_registry_table.table_arn,
            export_name=NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name),
            description="ARN of the tool registry DynamoDB table"
        )

        # Export tool registry table stream ARN
        CfnOutput(
            self,
            "ToolRegistryTableStreamArn",
            value=self.tool_registry_table.table_stream_arn,
            export_name=NamingConventions.stack_export_name("TableStreamArn", "ToolRegistry", self.env_name),
            description="Stream ARN of the tool registry DynamoDB table"
        )
        
        # Export consolidated tool secrets ARN
        CfnOutput(
            self,
            "ConsolidatedToolSecretsArn",
            value=self.tool_secrets.secret_arn,
            export_name=f"ConsolidatedToolSecretsArn-{self.env_name}",
            description="ARN of the consolidated tool secrets"
        )
        
        # Export tool secrets table name
        CfnOutput(
            self,
            "ToolSecretsTableName",
            value=self.tool_secrets_table.table_name,
            export_name=f"ToolSecretsTableName-{self.env_name}",
            description="Name of the tool secrets registry table"
        )
        
        # Export secret structure manager Lambda ARN
        CfnOutput(
            self,
            "SecretStructureManagerArn",
            value=self.secret_structure_manager.function_arn,
            export_name=f"SecretStructureManagerArn-{self.env_name}",
            description="ARN of the secret structure manager Lambda"
        )
        
        # Export shared Custom Resource provider service token
        CfnOutput(
            self,
            "SharedCustomResourceProviderToken",
            value=self.shared_cr_provider.service_token,
            export_name=f"SharedCustomResourceProviderToken-{self.env_name}",
            description="Service token for the shared Custom Resource provider"
        )

    def get_tool_registry_table(self) -> dynamodb.Table:
        """Get the tool registry table for use in other stacks"""
        return self.tool_registry_table