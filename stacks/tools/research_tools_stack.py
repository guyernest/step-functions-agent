from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    SecretValue
)

try:
    from aws_cdk import aws_lambda_go_alpha as lambda_go
except ImportError:
    # Fallback to regular Lambda if Go alpha is not available
    lambda_go = None

try:
    from aws_cdk import aws_lambda_python_alpha as _lambda_python
except ImportError:
    # Fallback to regular Lambda if Python alpha is not available
    _lambda_python = None
from constructs import Construct
from .base_tool_construct import MultiToolConstruct
import os
import json


class ResearchToolsStack(Stack):
    """
    Research Tools Stack - Deploys both Go and Python research tools
    
    This stack demonstrates multi-language tool deployment:
    - Go tool for web research (Perplexity API)
    - Python tools for financial data (yfinance)
    - Automatic DynamoDB registry registration
    - Tool-specific secrets management
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create tool-specific secrets
        self._create_web_research_secret()
        
        # Deploy Go research tool
        self._create_go_research_tool()
        
        # Deploy Python financial tools
        self._create_python_financial_tools()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_web_research_secret(self):
        """Create secret for web research tool (Perplexity API)"""
        
        # Try to load from .env.web-research file
        env_file_path = ".env.web-research"
        secret_value = {"PPLX_API_KEY": "REPLACE_WITH_ACTUAL_API_KEY"}
        
        if os.path.exists(env_file_path):
            try:
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            secret_value[key.strip()] = value.strip()
            except Exception as e:
                print(f"Warning: Could not read {env_file_path}: {e}")
        
        # Check if we have actual API key (not placeholder)
        if secret_value.get("PPLX_API_KEY") and secret_value["PPLX_API_KEY"] != "your_perplexity_api_key_here":
            # Create secret with actual value
            secret_object_value = {
                key: SecretValue.unsafe_plain_text(value)
                for key, value in secret_value.items()
            }
            
            self.web_research_secret = secretsmanager.Secret(
                self, 
                "WebResearchSecrets",
                secret_name=f"/ai-agent/tools/web-research/{self.env_name}",
                description=f"Web research tool secrets (Perplexity API) for {self.env_name} environment",
                secret_object_value=secret_object_value,
                removal_policy=RemovalPolicy.DESTROY
            )
        else:
            # Use template with placeholder
            self.web_research_secret = secretsmanager.Secret(
                self, 
                "WebResearchSecrets",
                secret_name=f"/ai-agent/tools/web-research/{self.env_name}",
                description=f"Web research tool secrets (Perplexity API) for {self.env_name} environment - UPDATE WITH ACTUAL API KEY",
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    secret_string_template=json.dumps(secret_value),
                    generate_string_key="placeholder",
                    exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\^"
                ),
                removal_policy=RemovalPolicy.DESTROY
            )

    def _create_go_research_tool(self):
        """Create Go Lambda function for web research"""
        
        # Create execution role for Go Lambda
        go_lambda_role = iam.Role(
            self,
            "GoResearchLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to research tool secrets
        go_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[self.web_research_secret.secret_arn]
            )
        )
        
        # Create Go Lambda function
        if lambda_go is not None:
            self.go_research_lambda = lambda_go.GoFunction(
                self,
                "WebResearchLambda",
                function_name=f"tool-web-research-{self.env_name}",
                description="Web research tool using Go and Perplexity API",
                entry="lambda/tools/web-research/",
                runtime=_lambda.Runtime.PROVIDED_AL2023,
                architecture=_lambda.Architecture.ARM_64,
                timeout=Duration.seconds(120),
                role=go_lambda_role
            )
            
            # Apply removal policy separately
            self.go_research_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        else:
            # Fallback to regular Lambda with Go runtime
            self.go_research_lambda = _lambda.Function(
                self,
                "WebResearchLambda",
                function_name=f"tool-web-research-{self.env_name}",
                description="Web research tool using Go and Perplexity API",
                runtime=_lambda.Runtime.PROVIDED_AL2023,
                architecture=_lambda.Architecture.ARM_64,
                code=_lambda.Code.from_asset("lambda/tools/web-research/"),
                handler="main",
                timeout=Duration.seconds(120),
                role=go_lambda_role
            )
            
            # Apply removal policy separately
            self.go_research_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        # Export Lambda ARN
        CfnOutput(
            self,
            "WebResearchLambdaArn",
            value=self.go_research_lambda.function_arn,
            export_name=f"WebResearchLambdaArn-{self.env_name}"
        )
        
        # Output secret ARN for reference
        CfnOutput(
            self,
            "WebResearchSecretArn",
            value=self.web_research_secret.secret_arn,
            description="ARN of the web research secret - update with actual Perplexity API key"
        )

    def _create_python_financial_tools(self):
        """Create Python Lambda function for financial tools"""
        
        # Create execution role for Python Lambda
        python_lambda_role = iam.Role(
            self,
            "PythonFinancialLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Create Python Lambda function with automatic dependency management
        if _lambda_python is not None:
            self.python_financial_lambda = _lambda_python.PythonFunction(
                self,
                "FinancialToolsLambda",
                function_name=f"tool-financial-data-{self.env_name}",
                description="Financial research tools using Python and yfinance",
                entry="lambda/tools/yfinance",
                index="index.py",
                handler="lambda_handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                timeout=Duration.seconds(120),
                role=python_lambda_role
            )
        else:
            # Fallback to regular Lambda (will need manual dependency management)
            self.python_financial_lambda = _lambda.Function(
                self,
                "FinancialToolsLambda",
                function_name=f"tool-financial-data-{self.env_name}",
                description="Financial research tools using Python and yfinance",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                code=_lambda.Code.from_asset("lambda/tools/yfinance"),
                handler="index.lambda_handler",
                timeout=Duration.seconds(120),
                role=python_lambda_role
            )
        
        # Apply removal policy separately
        self.python_financial_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        # Export Lambda ARN
        CfnOutput(
            self,
            "FinancialToolsLambdaArn",
            value=self.python_financial_lambda.function_arn,
            export_name=f"FinancialToolsLambdaArn-{self.env_name}"
        )

    def _register_tools_using_base_construct(self):
        """Register all research tools using the BaseToolConstruct pattern"""
        
        # Define Go research tool specifications
        go_research_tools = [
            {
                "tool_name": "research_company",
                "description": "Perform comprehensive web research on a company using AI-powered search",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "The name of the company to research"
                        },
                        "topics": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "Specific research topics (e.g., 'recent financial performance', 'market position')"
                            },
                            "description": "Optional list of specific topics to research. If not provided, will research general topics."
                        }
                    },
                    "required": ["company"]
                },
                "language": "go",
                "tags": ["research", "web", "company", "perplexity", "ai"],
                "author": "research-team@company.com"
            }
        ]
        
        # Define Python financial tool specifications
        python_financial_tools = [
            {
                "tool_name": "list_industries",
                "description": "List all industries within a specific sector for market analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector_key": {
                            "type": "string",
                            "description": "The sector key. Valid sectors: real-estate, healthcare, financial-services, technology, consumer-cyclical, consumer-defensive, basic-materials, industrials, energy, utilities, communication-services"
                        }
                    },
                    "required": ["sector_key"]
                },
                "language": "python",
                "tags": ["finance", "sectors", "industries", "yfinance"],
                "author": "research-team@company.com"
            },
            {
                "tool_name": "top_industry_companies",
                "description": "Get top companies within a specific industry for competitive analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry_key": {
                            "type": "string",
                            "description": "The industry key to get top companies for"
                        }
                    },
                    "required": ["industry_key"]
                },
                "language": "python",
                "tags": ["finance", "companies", "industry", "rankings"],
                "author": "research-team@company.com"
            },
            {
                "tool_name": "top_sector_companies",
                "description": "Get top companies within a specific sector for market analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector_key": {
                            "type": "string",
                            "description": "The sector key to get top companies for"
                        }
                    },
                    "required": ["sector_key"]
                },
                "language": "python",
                "tags": ["finance", "companies", "sector", "rankings"],
                "author": "research-team@company.com"
            }
        ]
        
        # Use MultiToolConstruct to register both tool groups
        MultiToolConstruct(
            self,
            "ResearchToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": go_research_tools,
                    "lambda_function": self.go_research_lambda
                },
                {
                    "tool_specs": python_financial_tools,
                    "lambda_function": self.python_financial_lambda
                }
            ],
            env_name=self.env_name
        )