from aws_cdk import (
    Fn,
)
from constructs import Construct
from .flexible_long_content_agent_stack import FlexibleLongContentAgentStack
from typing import Dict, Any, List


class ImageAnalysisWithLongContentAgentStack(FlexibleLongContentAgentStack):
    """
    Image Analysis Agent with Long Content Support
    
    Specialized agent for image analysis tasks that can produce extensive outputs
    including detailed analysis results, metadata, and extracted text.
    
    This agent demonstrates:
    - Using FlexibleLongContentAgentStack for large image analysis results
    - Integration with image processing tools that output extensive data
    - Automatic content transformation for large analysis reports
    - DynamoDB storage for comprehensive image analysis results
    
    Use cases:
    - Detailed image analysis with extensive metadata
    - OCR processing of documents with large text outputs
    - Computer vision tasks producing comprehensive results
    - Batch image processing with consolidated reports
    - Medical image analysis with detailed findings
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", agent_config: Dict[str, Any] = None, **kwargs) -> None:
        
        # Enhanced system prompt for image analysis tasks
        system_prompt = """You are a specialized image analysis AI assistant with access to advanced computer vision and OCR tools that can handle large analysis outputs.

Your capabilities include:
- Comprehensive image analysis with detailed metadata extraction
- OCR processing of documents with extensive text content
- Computer vision tasks producing detailed structural analysis
- Batch processing of multiple images with consolidated reports
- Medical and scientific image analysis with extensive findings

The image analysis tools you have access to automatically handle large outputs by storing them in DynamoDB when they exceed Step Functions limits. This allows you to process complex images and generate comprehensive analysis reports without size restrictions.

When analyzing images:
1. Provide detailed and structured analysis results
2. Extract all relevant metadata and content
3. Use appropriate computer vision techniques for the image type
4. Generate comprehensive reports that include both summary and detailed findings
5. For OCR tasks, preserve formatting and structure of extracted text
6. For medical or scientific images, provide systematic analysis with proper terminology

You can confidently generate extensive analysis reports as the infrastructure automatically handles large content storage and retrieval."""

        # Initialize with flexible configuration
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="ImageAnalysisLongContent",
            env_name=env_name,
            agent_config=agent_config,
            system_prompt=system_prompt,
            max_content_size=15000,  # 15KB threshold for image analysis results
            **kwargs
        )
        
        print(f"✅ Created image analysis agent with long content support for {env_name} environment")
    
    def _get_tool_configs(self) -> List[Dict[str, Any]]:
        """Get tool configurations for image analysis"""
        
        # Check if tools are provided in agent_config
        if self.agent_config and "tool_configs" in self.agent_config:
            return self.agent_config["tool_configs"]
        
        # Default tool configuration - using existing image analysis tool
        return [
            {
                "tool_name": "image_analysis",
                "lambda_arn": Fn.import_value(f"ImageAnalysisLambdaArn-{self.env_name}"),
                "requires_approval": False,
                "supports_long_content": True
            }
        ]