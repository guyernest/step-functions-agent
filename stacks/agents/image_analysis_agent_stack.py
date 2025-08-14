from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack


class ImageAnalysisAgentStack(ModularBaseAgentStack):
    """
    Image Analysis Agent Stack - Uses BaseAgentStack for simplified deployment
    
    This stack demonstrates the clean new architecture using the base stack:
    - Minimal code (~20 lines vs ~340 lines)
    - Uses BaseAgentStack for common patterns
    - Configurable tool list per agent
    - Uses Gemini LLM for multimodal image analysis tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "Computer vision assistant with advanced image analysis capabilities"
        self.llm_provider = "gemini"
        self.llm_model = "gemini-1.5-flash"
        self.agent_metadata = {
            "tags": ['vision', 'ocr', 'image-analysis', 'multimodal']
        }
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
        
                
        # Call ModularBaseAgentStack constructor
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