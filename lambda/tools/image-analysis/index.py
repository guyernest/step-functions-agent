import json
import boto3
from typing import List, Dict, Any
from google import genai
from google.genai import types
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters

# Initialize logger
logger = Logger(service="Image Analysis Service")

# Initialize AWS clients
s3_client = boto3.client('s3')

class ImageAnalyzer:
    def __init__(self):
        # Initialize Gemini client with API key from AWS Secrets Manager
        api_key = parameters.get_secret("/ai-agent/api-keys")
        self.gemini_client = genai.Client(api_key=json.loads(api_key)["GEMINI_API_KEY"])
        
    def get_image_from_s3(self, bucket: str, key: str) -> types.Part:
        """
        Retrieve an image from S3 and convert it to Gemini's Part format
        """
        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            image_content = response['Body'].read()
            # Determine content type from the key's extension
            content_type = f"image/{key.split('.')[-1].lower()}"
            return types.Part.from_bytes(image_content, content_type)
        except ClientError as e:
            logger.error(f"Error retrieving image from S3: {str(e)}")
            raise

    def analyze_images(self, image_locations: List[Dict[str, str]], query: str) -> str:
        """
        Analyze multiple images using Gemini model
        """
        try:
            # Convert all S3 images to Gemini Parts
            image_parts = []
            for loc in image_locations:
                image_part = self.get_image_from_s3(loc['bucket'], loc['key'])
                image_parts.append(image_part)

            # Generate content using Gemini
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[query, *image_parts]
            )
            
            return response.text

        except Exception as e:
            logger.error(f"Error analyzing images: {str(e)}")
            raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for image analysis
    """
    try:
        logger.info("Received event", extra={"event": event})
        
        tool_use = event
        tool_name = tool_use.get("name")
        
        if tool_name != "analyze_images":
            return {
                "type": "tool_result",
                "tool_use_id": tool_use["id"],
                "content": json.dumps({"error": f"Unknown tool: {tool_name}"})
            }

        # Extract input parameters
        input_data = tool_use.get("input", {})
        image_locations = input_data.get("image_locations", [])
        query = input_data.get("query", "What do you see in these images?")

        # Validate input
        if not image_locations:
            return {
                "type": "tool_result",
                "tool_use_id": tool_use["id"],
                "content": json.dumps({"error": "No image locations provided"})
            }

        # Initialize analyzer and process images
        analyzer = ImageAnalyzer()
        result = analyzer.analyze_images(image_locations, query)

        return {
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            "content": json.dumps({"analysis": result})
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            "content": json.dumps({"error": str(e)})
        }

if __name__ == "__main__":
    # Test event
    test_event = {
        "name": "analyze_images",
        "id": "analyze_images_unique_id",
        "input": {
            "image_locations": [
                {
                    "bucket": "ai-agent-test-bucket-672915487120-us-west-2", 
                    "key": "uploads/tehini_image.jpg"
                },
            ],
            "query": "What products are shown in these images and what are their ingredients?"
        },
        "type": "tool_use"
    }
    
    # Test the handler
    response = lambda_handler(test_event, None)
    print(json.dumps(response, indent=2))