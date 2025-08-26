#!/usr/bin/env python3
"""
Shopping Assistant Agent for Bedrock Agent Core
Based on the asynchronous shopping assistant example
"""

from bedrock_agentcore.runtime.models import PingStatus
from bedrock_agentcore.tools.browser_client import BrowserClient, browser_session
import logging
import random
import time
import threading
import os
import glob
import json

# Configure logging
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

from strands import Agent, tool
from strands.multiagent import GraphBuilder
from strands_tools import file_write, file_read, shell
from strands.models import BedrockModel

# Use Amazon Nova Pro model
nova_pro = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0"
)

# Set bypass tool consent
os.environ["BYPASS_TOOL_CONSENT"] = "true"

print("Starting Shopping Assistant...")

# Import Agent Core
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Try to get NOVA_ACT_API_KEY from environment or parameter store
def get_nova_act_api_key():
    """Get Nova Act API key from environment or AWS Parameter Store"""
    # First try environment variable
    api_key = os.environ.get("NOVA_ACT_API_KEY")
    if api_key:
        return api_key
    
    # Try AWS Parameter Store
    try:
        import boto3
        ssm = boto3.client('ssm', region_name='us-west-2')
        response = ssm.get_parameter(
            Name='/agentcore/nova-act-api-key',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        logging.warning(f"Could not retrieve Nova Act API key: {e}")
        # Return a placeholder - in production this would be required
        return "placeholder-api-key"

# Set the API key if available
nova_act_key = get_nova_act_api_key()
if nova_act_key and nova_act_key != "placeholder-api-key":
    os.environ["NOVA_ACT_API_KEY"] = nova_act_key
    print(f"Nova Act API key configured")
else:
    print("Warning: Nova Act API key not found - browser automation will use mock mode")

@tool(name="background_shopping", description="Based on the incoming shopping request, this agent-as-a-tool starts a background shopping task and writes a result file when done. The live shopping session can be seen on the Bedrock Agentcore console")
def call_browser_tool(request: str):
    """Call the browser tool with a web task to perform. You can provide a simple high level task, which is
    completed asynchronously by a sub agent. Prompt the browser agent via the task description that the response
    should be detailed. At the end of the web browser task, the sub agent will write a
    local file in the format 'result_<session_id>.txt' that you can read results from. Note that browser tool
    can take a while to finish. Notify the user that the browser agent is researching the question, and return
    control to the user so they can ask follow up questions. Special case: when the user asks for a comparison between products,
    you can call multiple browser sessions in parallel, or back to back; they can progress simultaneously."""

    logging.debug(f"In call_browser_tool, request = {request}")
    # Sanity check
    logging.debug(app.get_async_task_info())

    try:
        print("Starting background thread ...")
        thread = threading.Thread(
            target=_run_browser_task,
            args=(request + " Make sure to include the price, availability, and key product details in your response. Be efficient - if you can see the price on the search results page, no need to click into product details.",),
            daemon=True,
        )
        thread.start()
        print("Started")

    except Exception as e:
        print(f"Browser tool error: {e}")
    
    return {"messages": [{"role": "tool", "content": "running browser search"}]}


def _run_browser_task(request: str):
    """Run the browser task in background"""
    try:
        with browser_session("us-west-2") as client:
            print("Browser session started... waiting for it to be ready.")
            time.sleep(5)  # Wait for the browser session to be ready
            ws_url, headers = client.generate_ws_headers()

            # Generate a random number for port to avoid conflicts
            port = random.randint(8000, 9000)
            starting_url = "https://www.amazon.com"

            task_id = app.add_async_task("using_browser_tool")
            print(f"Task ID: {task_id}")

            print("Starting Nova act ...")

            try:
                # Import Nova Act when needed
                from nova_act import NovaAct
                
                with NovaAct(
                    cdp_endpoint_url=ws_url,
                    cdp_headers=headers,
                    preview={"playwright_actuation": True},
                    nova_act_api_key=os.environ.get("NOVA_ACT_API_KEY", ""),
                    starting_page=starting_url,
                ) as nova_act:
                    # Give Nova Act clear instructions for price extraction
                    enhanced_prompt = f"{request}\n\nPlease extract and return: 1) Product name, 2) Current price, 3) Availability status, 4) Any discounts or deals, 5) Customer rating if visible"
                    result = nova_act.act(prompt=enhanced_prompt, max_steps=20)

                    print(result)
                    print("Writing response locally...")
                    print(result.response)

                    # Prepare the result data
                    result_data = {
                        "session_id": str(result.metadata.session_id),
                        "act_id": str(result.metadata.act_id),
                        "prompt": str(result.metadata.prompt),
                        "response": str(result.response)
                    }
                    
                    # Still write to file for agent access
                    filename = f"/tmp/result_{result.metadata.session_id}.txt"
                    print(f"Writing to: {filename}")
                    with open(filename, "w") as f:
                        f.write(f"Session ID: {result_data['session_id']}\n")
                        f.write(f"Act ID: {result_data['act_id']}\n")
                        f.write(f"Prompt: {result_data['prompt']}\n")
                        f.write(f"Response: {result_data['response']}\n")

                    success = app.complete_async_task(task_id)
                    print(f"[Processor {task_id}] Task completion: {'SUCCESS' if success else 'FAILED'}")
                    
                    # Return both the status and the actual results
                    return {
                        'status': success,
                        'location': filename,
                        'results': result_data
                    }
                    
            except ImportError:
                logging.error("Nova Act not installed. Using mock response.")
                # Mock response for testing without nova_act
                mock_data = {
                    "session_id": f"mock_{task_id}",
                    "act_id": f"mock_act_{task_id}",
                    "prompt": request,
                    "response": f"Mock search results for: {request}\nNote: Nova Act not available, using mock response"
                }
                
                filename = f"/tmp/result_mock_{task_id}.txt"
                with open(filename, "w") as f:
                    f.write(f"Mock Session ID: {mock_data['session_id']}\n")
                    f.write(f"Prompt: {mock_data['prompt']}\n")
                    f.write(f"Response: {mock_data['response']}\n")
                
                app.complete_async_task(task_id)
                return {
                    'status': True,
                    'location': filename,
                    'results': mock_data
                }
                
    except Exception as e:
        # Convert exception to string immediately to avoid serialization issues
        error_msg = str(e)
        logging.error(f"Browser task error: {error_msg}")
        if 'task_id' in locals():
            app.complete_async_task(task_id)
        return {
            'status': False,
            'error': error_msg,
            'location': 'please check logs',
            'results': {
                'session_id': 'error',
                'prompt': request,
                'response': f"Error occurred: {error_msg}"
            }
        }


@tool
def get_tasks_info():
    """Get status of running web search tasks and list any result files and Nova Act log files"""
    # Get task info
    task_info = app.get_async_task_info()
    logging.debug(task_info)
    
    # Get result files from /tmp
    result_files = glob.glob("/tmp/result_*.txt")
    logging.debug(result_files)
    
    # Get Nova Act log files from /tmp
    nova_act_logs = []
    
    # Look for Nova Act log directories in /tmp
    tmp_dirs = glob.glob("/tmp/tmp*_nova_act_logs")
    for tmp_dir in tmp_dirs:
        if os.path.isdir(tmp_dir):
            # Look for session directories
            session_dirs = glob.glob(f"{tmp_dir}/*")
            for session_dir in session_dirs:
                if os.path.isdir(session_dir):
                    # Find HTML log files
                    log_files = glob.glob(f"{session_dir}/act_*.html")
                    nova_act_logs.extend(log_files)
    
    tasks_result = {
        "message": "Current task information", 
        "task_info": task_info,
        "result_files": result_files,
        "nova_act_logs": nova_act_logs
    }

    logging.debug(f"Nova Act logs found: {nova_act_logs}")
    return tasks_result


# Define agents
reporting_agent = Agent(
    name="reporting_assistant", 
    system_prompt="""You are a report generation agent. Once the shopping session is completed, you can read
     one or more results_<sessionid>.txt files and respond to the user with the content you see.
     
     If no result files are available but Nova Act log files are found, you can read those HTML log files
     to extract information about the shopping session and provide a summary to the user. These log files
     are typically located at paths like /tmp/tmp*_nova_act_logs/*/act_*.html and contain detailed
     information about the browser session. These log files are very large, so do not try to read the 
     entire file all at once.""",
    tools=[file_read, get_tasks_info, shell, file_write],
    model=nova_pro
)

fronting_agent = Agent(
    name="fronting_assistant", 
    system_prompt="""You are a shopping assistant for amazon.com. You receive a request from the user, and answer immediately
     if it is a generic question, or route to a background shopping agent. If you decide to go on with background 
     shopping you must return `shop_background.start` in your text response. You may also read any reports or results
     generated by other agents; this will be in the format `/tmp/result_<session_id>`. 
     You also have a tool to check the status of running tasks. 
     
     DO NOT use the reporting agent tool right after creating a browser session. Ask the user to wait for results.""",
    tools=[get_tasks_info, file_read],
    model=nova_pro
)

shopping_agent = Agent(
    name="shopping_assistant", 
    system_prompt="""You are a background shopping assistant. You receive a request from the user, and
     asynchronously search amazon.com and report back to the customer. Once you start a shopping session, 
     recognize that this will take a long time to complete. After starting one or more sessions in parallel,
     return immediately to the user with an appropriate message. 
     
     NOTE 1: If a shopping session is running/active, do not start another one unless you need to, or if it is a different shopping request
     from earlier. 
    
     NOTE 2: In case the user asks for a comparison between two (or more) products, start 2 (or more) browser sessions in parallel. 
    
     NOTE 3: Do not take a long time to research this; use a maximum of 5 steps to complete the search (where one step is a click, scroll etc);
     do whatever minimum research required to directly answer the user question. 

     NOTE 4: DO NOT ask follow up questions, start analyzing the task immediately using the web search tool.
    
    Lastly, if the user asks for the status of the search or for a report, use the appropriate tools to assist.""",
    tools=[call_browser_tool],
    model=nova_pro
)


def only_if_shopping_needed(state):
    """Only pass through if shopping is required."""
    logging.debug("---------------------------------------------------------")
    logging.debug(state)
    logging.debug(f"task: {state.task}")

    start_node = state.results.get("start")
    if not start_node:
        return False

    # Check if research result contains success indicator
    result_text = str(start_node.result)
    logging.debug("-------!!!-------")
    logging.debug(result_text.lower())
    condition = "shop_background.start" in result_text.lower()
    if condition:
        logging.debug(f"starting shopping task since condition is {condition}")
        print(f"starting shopping task since condition is {condition}")
    else:
        logging.debug(f"not starting shopping task since condition is {condition}")
    logging.debug("-------!!!-------")
    return condition


def only_if_background_task_is_done(state):
    """Check if background tasks are done and results are available"""
    tasks = get_tasks_info()
    # Return True if there are no active tasks AND either result files or Nova Act logs are available
    return tasks['task_info'].get('active_count', 0) == 0 and (
        tasks.get('result_files', []) != [] or 
        tasks.get('nova_act_logs', []) != []
    )


# Build the graph
builder = GraphBuilder()

builder.add_node(fronting_agent, "start")
builder.add_node(shopping_agent, "shop")
builder.add_node(reporting_agent, "report")

builder.add_edge("start", "shop", condition=only_if_shopping_needed)
builder.add_edge("start", "report", condition=only_if_background_task_is_done)
builder.set_entry_point("start")

graph = builder.build()


@app.entrypoint
def handler(payload, context):
    """Main entrypoint for the shopping assistant"""
    logging.info(f"Handler invoked with payload: {json.dumps(payload) if payload else 'None'}")
    
    try:
        if "test" in payload:
            # Directly test browser task
            test_request = payload.get("test")
            if isinstance(test_request, bool):
                test_request = "Search for Echo Dot prices on Amazon"
            # Validate the request
            if not test_request or not isinstance(test_request, str):
                return {
                    "status": False,
                    "error": "Invalid test request - must be a non-empty string",
                    "results": {"response": "Please provide a valid search query"}
                }
            result = _run_browser_task(request=test_request)
            return result
    except Exception as e:
        # Catch any exceptions and return a proper error response
        error_msg = str(e)
        logging.error(f"Handler error: {error_msg}")
        return {
            "status": False,
            "error": error_msg,
            "results": {"response": f"Error processing request: {error_msg}"}
        }
    
    elif "prompt" in payload:
        # Run the full agent graph
        result = graph(payload.get("prompt"))
        # Extract the assistant's message
        if result and result.results and 'start' in result.results:
            message = result.results['start'].result.message
            # Handle different message formats
            if isinstance(message, dict):
                if 'content' in message:
                    content = message['content']
                    if isinstance(content, list) and len(content) > 0:
                        if isinstance(content[0], dict) and 'text' in content[0]:
                            return {"result": content[0]['text']}
                    return {"result": str(content)}
                return {"result": str(message)}
            return {"result": str(message)}
        return {"result": "Processing your request..."}
    else:
        return {"result": "You must provide a `prompt` or `test` key to proceed. ✋"}


# Only run if executed directly (for local testing)
if __name__ == "__main__":
    app.run()