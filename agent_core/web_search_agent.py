#!/usr/bin/env python3
"""
Web Search Agent for Bedrock Agent Core
Uses Strands for multi-agent orchestration and Nova Act for browser automation
"""

import logging
import time
import threading
import glob
import os
import json

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Now import Agent Core components
try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    from bedrock_agentcore.runtime.models import PingStatus
    from bedrock_agentcore.tools.browser_client import BrowserClient, browser_session
except ImportError as e:
    logging.warning(f"Agent Core imports not available: {e}")
    # Fallback for local testing
    class BedrockAgentCoreApp:
        def __init__(self):
            self.tasks = {}
        def entrypoint(self, func):
            return func
        def add_async_task(self, name):
            task_id = f"task_{len(self.tasks)}"
            self.tasks[task_id] = {"name": name, "status": "running"}
            return task_id
        def complete_async_task(self, task_id):
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = "completed"
            return True
        def get_async_task_info(self):
            return {
                "active_count": sum(1 for t in self.tasks.values() if t["status"] == "running"),
                "completed_count": sum(1 for t in self.tasks.values() if t["status"] == "completed")
            }
        def run(self):
            pass

from strands import Agent, tool
from strands.multiagent import GraphBuilder
from strands_tools import file_write, file_read, shell
from strands.models import BedrockModel

# Initialize models
# Use Amazon Nova Pro model for all agents
nova_pro = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0"
)

# Initialize Agent Core app
app = BedrockAgentCoreApp()

print("Starting Web Search Agent...")

# ---------- Tool Definitions ----------

@tool(name="web_search", description="Search for information on web portals and extract structured data")
def web_search_tool(url: str, query: str, extract_data: bool = False):
    """
    Perform web searches and data extraction using browser automation.
    
    Args:
        url: The portal URL to search
        query: The search query or extraction task
        extract_data: Whether to extract structured data from results
    """
    logging.info(f"Starting web search on {url} for query: {query}")
    
    # Add async task for tracking
    task_id = app.add_async_task(f"web_search_{query[:20]}")
    
    try:
        # Start browser session in background thread
        thread = threading.Thread(
            target=_run_browser_task,
            args=(url, query, extract_data, task_id),
            daemon=True
        )
        thread.start()
        
        return {
            "status": "started",
            "task_id": task_id,
            "message": f"Web search started for '{query}' on {url}. Results will be saved when complete."
        }
        
    except Exception as e:
        app.complete_async_task(task_id)
        logging.error(f"Web search error: {e}")
        return {"status": "error", "message": str(e)}


def _run_browser_task(url: str, query: str, extract_data: bool, task_id: str):
    """
    Run browser automation task in background
    """
    try:
        with browser_session("us-west-2") as client:
            logging.info("Browser session started, waiting for initialization...")
            time.sleep(3)  # Wait for browser to be ready
            
            ws_url, headers = client.generate_ws_headers()
            
            # Import Nova Act only when needed
            os.environ["BYPASS_TOOL_CONSENT"] = "true"
            from nova_act import NovaAct
            
            # Construct the prompt based on task type
            if extract_data:
                prompt = f"Navigate to {url} and extract data for: {query}. Return structured information."
            else:
                prompt = f"Search on {url} for: {query}. Provide detailed results with prices, descriptions, and availability."
            
            with NovaAct(
                cdp_endpoint_url=ws_url,
                cdp_headers=headers,
                preview={"playwright_actuation": True},
                nova_act_api_key=os.environ.get("NOVA_ACT_API_KEY", ""),
                starting_page=url,
            ) as nova_act:
                result = nova_act.act(prompt=prompt, max_steps=15)
                
                # Save results to file
                filename = f"/tmp/search_result_{task_id}.json"
                with open(filename, "w") as f:
                    json.dump({
                        "task_id": task_id,
                        "url": url,
                        "query": query,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "session_id": str(result.metadata.session_id),
                        "act_id": str(result.metadata.act_id),
                        "response": str(result.response),
                        "status": "completed"
                    }, f, indent=2)
                
                logging.info(f"Search results saved to {filename}")
                
    except Exception as e:
        logging.error(f"Browser task error: {e}")
        # Save error to file
        filename = f"/tmp/search_result_{task_id}.json"
        with open(filename, "w") as f:
            json.dump({
                "task_id": task_id,
                "url": url,
                "query": query,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
                "status": "failed"
            }, f, indent=2)
    
    finally:
        # Mark task as complete
        app.complete_async_task(task_id)
        logging.info(f"Task {task_id} completed")


@tool(name="get_search_status", description="Get status of web search tasks and list result files")
def get_search_status():
    """
    Get status of running web searches and available results
    """
    # Get task info from Agent Core
    task_info = app.get_async_task_info()
    
    # Find result files
    result_files = glob.glob("/tmp/search_result_*.json")
    
    # Load results
    results = []
    for file_path in result_files:
        try:
            with open(file_path, "r") as f:
                results.append(json.load(f))
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
    
    return {
        "active_tasks": task_info.get("active_count", 0),
        "completed_tasks": task_info.get("completed_count", 0),
        "results_available": len(results),
        "results": results
    }


@tool(name="authenticate", description="Authenticate with a web portal")
def authenticate_portal(url: str, username: str, password: str):
    """
    Authenticate with a web portal for accessing protected content
    """
    # This would integrate with Nova Act for authentication
    # For now, return a mock response
    return {
        "status": "authenticated",
        "session_id": f"session_{time.time()}",
        "message": f"Successfully authenticated to {url}"
    }


# ---------- Agent Definitions ----------

search_agent = Agent(
    name="web_search_specialist",
    system_prompt="""You are a web search specialist that helps users find and extract information from web portals.
    
    Your capabilities:
    1. Search various web portals and search engines
    2. Extract structured data from web pages
    3. Handle authentication for protected portals
    4. Provide detailed search results with relevant information
    
    When performing searches:
    - Be thorough but efficient (use max 15 browser steps)
    - Extract the most relevant information
    - Include prices, availability, and descriptions when applicable
    - Save results for later retrieval
    
    Return search results in a clear, structured format.""",
    tools=[web_search_tool, get_search_status, authenticate_portal],
    model=nova_pro
)

reporting_agent = Agent(
    name="report_generator",
    system_prompt="""You are a report generation specialist. You read search results and create clear, 
    concise reports for users.
    
    When generating reports:
    - Summarize key findings
    - Highlight important information (prices, availability, features)
    - Organize data in a logical structure
    - Include relevant details from search results
    - Provide actionable insights when appropriate""",
    tools=[file_read, get_search_status],
    model=nova_pro
)

fronting_agent = Agent(
    name="user_assistant",
    system_prompt="""You are a helpful assistant that coordinates web searches for users.
    
    Your role:
    1. Understand user requests and determine if web search is needed
    2. Route requests to the appropriate specialist agent
    3. Provide updates on search progress
    4. Present results in a user-friendly format
    
    Decision logic:
    - If the user asks for web search, product information, or data extraction: route to search specialist
    - If the user asks for search results or reports: route to report generator
    - For general questions: answer directly
    
    Include 'search.needed' in your response when web search is required.
    Include 'report.needed' in your response when results should be generated.""",
    tools=[get_search_status],
    model=nova_pro
)

# ---------- Graph Builder ----------

def should_search(state):
    """Determine if search is needed based on fronting agent response"""
    front_result = state.results.get("front")
    if front_result:
        result_text = str(front_result.result)
        return "search.needed" in result_text.lower()
    return False


def should_report(state):
    """Determine if report generation is needed"""
    front_result = state.results.get("front")
    if front_result:
        result_text = str(front_result.result)
        return "report.needed" in result_text.lower()
    # Also check if there are completed searches
    status = get_search_status()
    return status["results_available"] > 0


# Build the agent graph
builder = GraphBuilder()

builder.add_node(fronting_agent, "front")
builder.add_node(search_agent, "search")
builder.add_node(reporting_agent, "report")

# Add conditional edges
builder.add_edge("front", "search", condition=should_search)
builder.add_edge("front", "report", condition=should_report)
builder.add_edge("search", "report")  # Always generate report after search

builder.set_entry_point("front")

graph = builder.build()

# ---------- Agent Core Entrypoint ----------

@app.entrypoint
def handler(payload, context):
    """
    Main entrypoint for the Agent Core web search agent
    
    Payload structure:
    {
        "prompt": "User's search query",
        "url": "Optional specific URL to search",
        "mode": "search|extract|authenticate"
    }
    """
    logging.info(f"Received payload: {payload}")
    
    # Handle different request types
    if "test" in payload:
        # Direct test mode
        return {"status": "healthy", "message": "Web Search Agent is running"}
    
    elif "prompt" in payload:
        # Run the multi-agent graph
        prompt = payload.get("prompt")
        url = payload.get("url", "https://www.amazon.com")  # Default to Amazon
        
        # Add URL context to prompt if provided
        if url != "https://www.amazon.com":
            prompt = f"Search on {url}: {prompt}"
        
        try:
            result = graph(prompt)
            
            # Extract the final response
            if "front" in result.results:
                response = result.results["front"].result.message
            elif "report" in result.results:
                response = result.results["report"].result.message
            else:
                response = "Search completed. Please check results."
            
            return {
                "status": "success",
                "response": response,
                "task_info": get_search_status()
            }
            
        except Exception as e:
            logging.error(f"Graph execution error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    else:
        return {
            "status": "error",
            "message": "Please provide a 'prompt' in your request"
        }


# Run the app if executed directly (for local testing)
if __name__ == "__main__":
    app.run()