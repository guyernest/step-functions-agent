#!/usr/bin/env python3
"""
Simplified Web Search Agent for Bedrock Agent Core
A minimal working implementation to test the runtime
"""

import logging
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import Agent Core runtime
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Initialize the app
app = BedrockAgentCoreApp()

logger.info("Initializing Simple Web Search Agent...")

@app.entrypoint
def handler(payload, context):
    """
    Main entrypoint for the Agent Core web search agent
    
    This is a simplified version that handles basic requests
    """
    logger.info(f"Handler invoked with payload: {json.dumps(payload)}")
    logger.info(f"Context: {context}")
    
    try:
        # Handle different request types
        if not payload:
            return {
                "status": "error",
                "message": "No payload provided"
            }
        
        # Handle test/health check
        if payload.get("test") or payload.get("ping"):
            logger.info("Handling test/ping request")
            return {
                "status": "healthy",
                "message": "Simple Web Search Agent is running",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Handle prompt-based requests
        if "prompt" in payload:
            prompt = payload.get("prompt", "")
            logger.info(f"Processing prompt: {prompt}")
            
            # For now, return a simple response
            # In production, this would invoke the multi-agent graph
            response = f"I received your request: '{prompt}'. Web search functionality is being initialized."
            
            return {
                "status": "success",
                "response": response,
                "prompt": prompt,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Handle direct commands
        if "command" in payload:
            command = payload.get("command")
            logger.info(f"Processing command: {command}")
            
            if command == "status":
                return {
                    "status": "ready",
                    "agent": "simple-web-search",
                    "version": "1.0.0",
                    "capabilities": ["search", "extract", "report"]
                }
            elif command == "help":
                return {
                    "status": "success",
                    "commands": ["status", "help"],
                    "usage": "Send a 'prompt' key with your search query"
                }
        
        # Default response for unknown requests
        return {
            "status": "error",
            "message": "Please provide a 'prompt' key with your search query, or 'test' for health check",
            "received_keys": list(payload.keys()) if payload else []
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Internal error: {str(e)}"
        }

# Only run the app if this is the main module
if __name__ == "__main__":
    logger.info("Starting Agent Core app...")
    app.run()