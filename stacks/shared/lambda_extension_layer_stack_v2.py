"""
Lambda Extension Layer Stack V2 - Improved version that uses pre-built artifacts

This version expects the extensions to be pre-built and doesn't run the build
during CDK synthesis, avoiding unnecessary rebuilds and export conflicts.
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    aws_lambda as lambda_,
)
from constructs import Construct
import os


class LambdaExtensionLayerStackV2(Stack):
    """
    Lambda Extension Layer Stack - Creates Lambda layers from pre-built extensions
    
    This stack expects the Rust extensions to be pre-built using:
        cd lambda/extensions/long-content && make build
    
    This approach avoids building during CDK synthesis and prevents
    unnecessary stack updates due to build artifacts changing.
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.extension_dir = "lambda/extensions/long-content"
        
        # Verify pre-built extensions exist
        self._verify_prebuilt_extensions()
        
        # Create Lambda layers for both architectures
        self._create_x86_layer()
        self._create_arm_layer()
        
        # Create stack exports
        self._create_outputs()
        
        print(f"✅ Created Lambda extension layer stack for {env_name} environment")

    def _verify_prebuilt_extensions(self):
        """Verify that pre-built extension files exist"""
        x86_path = os.path.join(self.extension_dir, "extension-x86.zip")
        arm_path = os.path.join(self.extension_dir, "extension-arm.zip")
        
        if not os.path.exists(x86_path):
            raise Exception(
                f"Pre-built x86 extension not found at {x86_path}\n"
                f"Please build it first: cd {self.extension_dir} && make build"
            )
        
        if not os.path.exists(arm_path):
            raise Exception(
                f"Pre-built ARM extension not found at {arm_path}\n"
                f"Please build it first: cd {self.extension_dir} && make build"
            )
        
        print(f"✅ Found pre-built extensions:")
        print(f"   - x86_64: {x86_path} ({os.path.getsize(x86_path) / 1024 / 1024:.1f} MB)")
        print(f"   - ARM64: {arm_path} ({os.path.getsize(arm_path) / 1024 / 1024:.1f} MB)")

    def _create_x86_layer(self):
        """Create Lambda layer for x86_64 architecture"""
        self.x86_layer = lambda_.LayerVersion(
            self,
            "ProxyExtensionLayerX86",
            code=lambda_.Code.from_asset(
                os.path.join(self.extension_dir, "extension-x86.zip")
            ),
            compatible_architectures=[lambda_.Architecture.X86_64],
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_8,
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_10,
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.PYTHON_3_12,
            ],
            description=f"Lambda Runtime API Proxy extension for x86_64 - {self.env_name}",
            layer_version_name=f"lrap-extension-x86-{self.env_name}",
        )

    def _create_arm_layer(self):
        """Create Lambda layer for ARM64 architecture"""
        self.arm_layer = lambda_.LayerVersion(
            self,
            "ProxyExtensionLayerArm",
            code=lambda_.Code.from_asset(
                os.path.join(self.extension_dir, "extension-arm.zip")
            ),
            compatible_architectures=[lambda_.Architecture.ARM_64],
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_8,
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_10,
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.PYTHON_3_12,
            ],
            description=f"Lambda Runtime API Proxy extension for ARM64 - {self.env_name}",
            layer_version_name=f"lrap-extension-arm-{self.env_name}",
        )

    def _create_outputs(self):
        """Create CloudFormation outputs for the layers"""
        
        # Export x86 layer ARN
        CfnOutput(
            self,
            "ProxyLayerX86ArnExport",
            value=self.x86_layer.layer_version_arn,
            export_name=f"SharedProxyLayerX86ExtensionBuild-{self.env_name}",
            description="ARN of the Lambda Runtime API Proxy layer for x86_64"
        )
        
        # Export ARM layer ARN
        CfnOutput(
            self,
            "ProxyLayerArmArnExport",
            value=self.arm_layer.layer_version_arn,
            export_name=f"SharedProxyLayerArmExtensionBuild-{self.env_name}",
            description="ARN of the Lambda Runtime API Proxy layer for ARM64"
        )