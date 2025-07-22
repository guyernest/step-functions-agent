from aws_cdk import Stack, Fn
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.tool_definitions import AllTools
from ..shared.base_agent_construct import BaseAgentConstruct


class ImageAnalysisAgentStack(BaseAgentStack):
    """
    Image Analysis Agent Stack - Uses BaseAgentStack for simplified deployment
    
    This stack demonstrates the clean new architecture using the base stack:
    - Minimal code (~20 lines vs ~340 lines)
    - Uses BaseAgentStack for common patterns
    - Configurable tool list per agent
    - Uses Gemini LLM for multimodal image analysis tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        
        # Import Gemini LLM ARN from shared stack (multimodal capabilities)
        gemini_lambda_arn = Fn.import_value(f"SharedGeminiLambdaArn-{env_name}")
        
        # Import Image Analysis Lambda ARN
        image_analysis_lambda_arn = Fn.import_value(f"ImageAnalysisLambdaArn-{env_name}")
        
        # Define tool configurations
        tool_configs = [
            {
                "tool_name": "analyze_images",
                "lambda_arn": image_analysis_lambda_arn,
                "requires_approval": False
            }
        ]
        
        # Validate tool names exist in centralized definitions
        tool_names = [config["tool_name"] for config in tool_configs]
        invalid_tools = AllTools.validate_tool_names(tool_names)
        if invalid_tools:
            raise ValueError(f"Image Analysis Agent uses invalid tools: {invalid_tools}. Available tools: {AllTools.get_all_tool_names()}")
        
        # Call BaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="image-analysis-agent",
            llm_arn=gemini_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt="You are an expert computer vision assistant with advanced image analysis capabilities. You can analyze images, extract text (OCR), identify objects, describe scenes, and answer questions about visual content. Use the analyze_images tool to process images and provide detailed, accurate descriptions and insights. You excel at understanding visual context and can help with tasks like document analysis, object detection, scene understanding, and visual question answering.",
            **kwargs
        )
        
        # Store env_name for registration
        self.env_name = env_name
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this agent in the Agent Registry using BaseAgentConstruct"""
        
        # Define Image Analysis agent specification
        agent_spec = {
            "agent_name": "image-analysis-agent",
            "version": "v1.0",
            "status": "active",
            "system_prompt": """You are an expert computer vision assistant with state-of-the-art multimodal AI capabilities.

Your primary responsibilities:
- Analyze images with detailed descriptions and insights
- Extract text from images using advanced OCR capabilities
- Identify objects, people, animals, and scenes in images
- Answer specific questions about image content
- Provide detailed visual analysis for accessibility purposes
- Analyze documents, charts, graphs, and diagrams
- Detect and describe visual elements, colors, composition
- Compare and contrast multiple images when provided

Your capabilities include:
- Object detection and classification
- Optical Character Recognition (OCR)
- Scene understanding and description
- Visual question answering
- Document analysis and data extraction
- Image quality assessment
- Accessibility descriptions for visually impaired users

Always provide accurate, detailed, and helpful analysis. Be specific about what you observe and explain your reasoning when making interpretations about image content.""",
            "description": "AI-powered image analysis and computer vision agent with multimodal capabilities",
            "llm_provider": "gemini",
            "llm_model": "gemini-1.5-pro",
            "tools": [
                {"tool_name": "analyze_images", "enabled": True, "version": "latest"}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/image-analysis-agent-{self.env_name}",
                "metrics_namespace": "AIAgents/ImageAnalysis",
                "trace_enabled": True,
                "log_level": "INFO"
            },
            "parameters": {
                "max_iterations": 3,
                "temperature": 0.1,
                "timeout_seconds": 300,
                "max_tokens": 4096
            },
            "metadata": {
                "created_by": "system",
                "tags": ["image", "vision", "multimodal", "ocr", "production"],
                "deployment_env": self.env_name
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "ImageAnalysisAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )