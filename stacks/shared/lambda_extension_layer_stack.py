from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as lambda_,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
import os
import subprocess
import sys


class LambdaExtensionLayerStack(Stack):
    """
    Lambda Extension Layer Stack
    
    Builds the Lambda Runtime API Proxy extension using the existing Makefile
    and creates Lambda layers for both x86_64 and ARM64 architectures.
    
    This stack:
    - Uses the Makefile to build the Rust extension
    - Creates Lambda layers from the built zip files
    - Provides CloudFormation exports for layer ARNs
    
    Prerequisites:
    - cargo-lambda must be installed locally
    - Rust toolchain must be installed
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.extension_dir = "lambda/extensions/long-content"
        
        # Build the extensions using Makefile
        self._build_extensions()
        
        # Create Lambda layers for both architectures
        self._create_x86_layer()
        self._create_arm_layer()
        
        # Create stack exports
        self._create_outputs()
        
        print(f"✅ Created Lambda extension layer stack for {env_name} environment")

    def _build_extensions(self):
        """Build the extensions using the Makefile"""
        
        print("🔨 Building Lambda extensions using Makefile...")
        
        # Save current directory
        original_cwd = os.getcwd()
        
        try:
            # Change to extension directory
            os.chdir(self.extension_dir)
            
            # Run make clean to ensure fresh build
            print("  Cleaning previous builds...")
            result = subprocess.run(["make", "clean"], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Warning: make clean failed: {result.stderr}")
            
            # Run make build to build both architectures
            print("  Building extensions for x86_64 and ARM64...")
            result = subprocess.run(["make", "build"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Extension build failed: {result.stderr}")
            
            print("  Build completed successfully!")
            
            # Verify the zip files exist
            if not os.path.exists("extension-x86.zip"):
                raise Exception("extension-x86.zip not found after build")
            if not os.path.exists("extension-arm.zip"):
                raise Exception("extension-arm.zip not found after build")
                
        finally:
            # Change back to original directory
            os.chdir(original_cwd)

    def _create_x86_layer(self):
        """Create Lambda layer for x86_64 architecture"""
        
        # Path to the built extension zip
        x86_zip_path = os.path.join(self.extension_dir, "extension-x86.zip")
        
        self.proxy_layer_x86 = lambda_.LayerVersion(
            self,
            "ProxyExtensionLayerX86",
            layer_version_name=f"lambda-runtime-api-proxy-x86-{self.env_name}",
            description="Lambda Runtime API Proxy Extension for x86_64",
            code=lambda_.Code.from_asset(x86_zip_path),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_10,
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.NODEJS_18_X,
                lambda_.Runtime.JAVA_11,
                lambda_.Runtime.JAVA_17,
                lambda_.Runtime.PROVIDED_AL2,
                lambda_.Runtime.PROVIDED_AL2023
            ],
            compatible_architectures=[lambda_.Architecture.X86_64]
        )
        
        print(f"🔧 Created Lambda extension layer for x86_64 architecture")

    def _create_arm_layer(self):
        """Create Lambda layer for ARM64 architecture"""
        
        # Path to the built extension zip
        arm_zip_path = os.path.join(self.extension_dir, "extension-arm.zip")
        
        self.proxy_layer_arm = lambda_.LayerVersion(
            self,
            "ProxyExtensionLayerARM",
            layer_version_name=f"lambda-runtime-api-proxy-arm-{self.env_name}",
            description="Lambda Runtime API Proxy Extension for ARM64",
            code=lambda_.Code.from_asset(arm_zip_path),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_10,
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.NODEJS_18_X,
                lambda_.Runtime.JAVA_11,
                lambda_.Runtime.JAVA_17,
                lambda_.Runtime.PROVIDED_AL2,
                lambda_.Runtime.PROVIDED_AL2023
            ],
            compatible_architectures=[lambda_.Architecture.ARM_64]
        )
        
        print(f"🔧 Created Lambda extension layer for ARM64 architecture")

    def _create_outputs(self):
        """Create CloudFormation outputs for other stacks to use"""
        
        # Export layer ARNs
        CfnOutput(
            self,
            "ProxyLayerX86Arn",
            value=self.proxy_layer_x86.layer_version_arn,
            export_name=NamingConventions.stack_export_name("ProxyLayerX86", "ExtensionBuild", self.env_name),
            description="Lambda Runtime API Proxy layer ARN for x86_64"
        )
        
        CfnOutput(
            self,
            "ProxyLayerArmArn", 
            value=self.proxy_layer_arm.layer_version_arn,
            export_name=NamingConventions.stack_export_name("ProxyLayerArm", "ExtensionBuild", self.env_name),
            description="Lambda Runtime API Proxy layer ARN for ARM64"
        )