"""
Lambda handler for Agent Core Browser Tool
Handles streaming responses and long-running browser automation tasks
"""

import json
import boto3
import logging
import os
import uuid
from typing import Dict, Any, Generator
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def process_event_stream(stream_response: Generator) -> Dict[str, Any]:
    """
    Process the EventStream response from Agent Core
    Collects chunks, traces, and handles completion
    """
    full_response = ""
    traces = []
    metadata = {}
    chunk_count = 0
    
    try:
        for event in stream_response:
            chunk_count += 1
            logger.info(f"Processing event {chunk_count}: Event keys: {event.keys() if hasattr(event, 'keys') else 'N/A'}")
            
            # Log the full event structure for debugging
            if chunk_count <= 3:  # Log first 3 events in detail
                logger.info(f"Event {chunk_count} full structure: {json.dumps(event, default=str)[:500]}")
            
            if 'chunk' in event:
                # Handle data chunks
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    full_response += chunk_text
                    logger.info(f"Received chunk {chunk_count}: {chunk_text[:200]}...")
                elif 'text' in chunk:
                    chunk_text = chunk['text']
                    full_response += chunk_text
                    logger.info(f"Received text chunk {chunk_count}: {chunk_text[:200]}...")
                    
            elif 'message' in event:
                # Handle message events
                message = event['message']
                if isinstance(message, str):
                    full_response += message
                else:
                    full_response += json.dumps(message)
                logger.info(f"Received message: {str(message)[:200]}...")
                
            elif 'output' in event:
                # Handle output events
                output = event['output']
                if isinstance(output, str):
                    full_response += output
                else:
                    full_response += json.dumps(output)
                logger.info(f"Received output: {str(output)[:200]}...")
                
            elif 'trace' in event:
                # Handle trace information for debugging
                trace = event['trace']
                traces.append(trace)
                logger.debug(f"Trace: {json.dumps(trace)[:200]}")
                
            elif 'metadata' in event:
                # Handle metadata
                metadata.update(event['metadata'])
                logger.info(f"Metadata: {json.dumps(metadata)}")
                
            elif 'ping' in event:
                # Handle ping/keepalive events
                logger.debug(f"Ping received: {event['ping']}")
                
            elif 'exception' in event:
                # Handle exceptions
                error_msg = f"Stream exception: {event['exception']}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'response': full_response or error_msg
                }
            else:
                # Handle unknown event types
                logger.info(f"Unknown event type in chunk {chunk_count}: {json.dumps(event, default=str)[:200]}")
                
    except Exception as e:
        logger.error(f"Error processing event stream: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'response': full_response or f"Stream processing error: {str(e)}"
        }
    
    logger.info(f"Processed {chunk_count} chunks, total response length: {len(full_response)}")
    
    return {
        'success': True,
        'response': full_response,
        'traces': traces,
        'metadata': metadata,
        'chunk_count': chunk_count
    }


def handler(event, context):
    """
    Lambda handler that processes tool registry format and invokes Agent Core
    Handles streaming responses for long-running browser automation tasks
    
    Expected input format from tool registry:
    {
        "id": "toolu_xxx",
        "name": "browser_search",
        "input": {
            "query": "search query",
            "url": "https://www.amazon.com",
            "test_mode": false
        }
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get environment variables
    aws_region = os.environ.get('AWS_REGION')
    agent_runtime_arn = os.environ.get('AGENT_RUNTIME_ARN')
    
    logger.info(f"AWS Region: {aws_region}")
    logger.info(f"Agent Runtime ARN: {agent_runtime_arn}")
    
    try:
        # Extract tool use information
        tool_use_id = event.get('id', f'tool_{context.aws_request_id}')
        tool_name = event.get('name', 'browser_search')
        tool_input = event.get('input', {})
        
        # Build prompt for Agent Core based on tool input
        # Handle common typos and variations
        query = (
            tool_input.get('query') or 
            tool_input.get('prompt') or 
            tool_input.get('promot') or  # Handle typo
            tool_input.get('question') or 
            tool_input.get('search') or 
            ''
        )
        url = tool_input.get('url', 'https://www.amazon.com')
        action = tool_input.get('action', 'search')
        
        # Validate we have a query
        if not query:
            logger.warning("No query provided in input")
            return {
                'type': 'tool_result',
                'name': tool_name,
                'tool_use_id': tool_use_id,
                'content': 'Error: No search query provided. Please provide a "query" field in the input.'
            }
        
        if action == 'search':
            prompt = f"Search for {query} on {url}"
        elif action == 'extract':
            selectors = tool_input.get('selectors', {})
            prompt = f"Extract data from {url} using selectors: {json.dumps(selectors)}"
        elif action == 'authenticate':
            prompt = f"Authenticate on {url}"
        else:
            prompt = query or f"Browse {url}"
        
        # Initialize Agent Core client
        agent_core_client = boto3.client('bedrock-agentcore', region_name=aws_region)
        logger.info("Using bedrock-agentcore client")
        
        # Create session ID for this interaction (must be at least 33 characters)
        session_id = f'agentcore-session-{uuid.uuid4().hex}'
        logger.info(f"Using session ID: {session_id} (length: {len(session_id)})")
        
        # Prepare the payload for Agent Core
        # Default to test mode for immediate execution (avoids background task)
        use_test_mode = tool_input.get('test_mode', True)  # Default to True
        
        if use_test_mode:
            payload_dict = {
                "test": prompt
            }
            logger.info("Using test mode for direct browser execution")
        else:
            payload_dict = {
                "prompt": prompt
            }
            logger.info("Using standard mode (may start background task)")
        
        payload = json.dumps(payload_dict).encode()
        logger.info(f"Sending payload to Agent Core: {payload_dict}")
        
        # Invoke Agent Core runtime - this returns a streaming response
        logger.info(f"Invoking Agent Core with prompt: {prompt}")
        start_time = time.time()
        
        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=agent_runtime_arn,
            runtimeSessionId=session_id,
            payload=payload
        )
        
        logger.info(f"Got response object: {type(response)}, keys: {response.keys()}")
        
        # Log additional response details
        logger.info(f"Response metadata: {response.get('ResponseMetadata', {})}")
        logger.info(f"Status code: {response.get('statusCode')}")
        logger.info(f"Content type: {response.get('contentType')}")
        
        # Process the streaming response
        agent_response_data = None
        
        # Check for 'response' key (the actual streaming response)
        if 'response' in response:
            stream_response = response['response']
            logger.info(f"Got response stream: {type(stream_response)}")
            
            # Check if this is a StreamingBody (most common case)
            if hasattr(stream_response, 'read'):
                # Regular streaming body - read the entire response
                logger.info("Processing StreamingBody response...")
                response_body = stream_response.read()
                if isinstance(response_body, bytes):
                    response_body = response_body.decode('utf-8')
                logger.info(f"Raw response: {response_body[:500]}...")
                agent_response_data = {
                    'success': True,
                    'response': response_body
                }
            # Check if this is an EventStream (iterator of events)
            elif hasattr(stream_response, '__iter__') and not isinstance(stream_response, (str, bytes)):
                logger.info("Processing EventStream response...")
                try:
                    agent_response_data = process_event_stream(stream_response)
                except TypeError as e:
                    # If it fails, try reading as bytes
                    logger.warning(f"EventStream processing failed: {e}, trying as bytes")
                    if hasattr(stream_response, 'read'):
                        response_body = stream_response.read()
                        if isinstance(response_body, bytes):
                            response_body = response_body.decode('utf-8')
                        agent_response_data = {
                            'success': True,
                            'response': response_body
                        }
                    else:
                        agent_response_data = {
                            'success': False,
                            'error': str(e),
                            'response': 'Failed to process stream'
                        }
            else:
                logger.warning(f"Unknown response type: {type(stream_response)}")
                agent_response_data = {
                    'success': False,
                    'response': str(stream_response)
                }
        # Fallback to check for 'payload' key (older format)
        elif 'payload' in response:
            payload_response = response['payload']
            logger.info("Using legacy 'payload' key")
            
            if hasattr(payload_response, '__iter__'):
                logger.info("Processing EventStream response from payload...")
                agent_response_data = process_event_stream(payload_response)
            elif hasattr(payload_response, 'read'):
                logger.info("Processing regular streaming response from payload...")
                response_body = payload_response.read()
                if isinstance(response_body, bytes):
                    response_body = response_body.decode('utf-8')
                agent_response_data = {
                    'success': True,
                    'response': response_body
                }
            else:
                agent_response_data = {
                    'success': False,
                    'response': str(payload_response)
                }
        else:
            logger.warning(f"No 'response' or 'payload' key found. Available keys: {response.keys()}")
            agent_response_data = {
                'success': False,
                'response': 'No streaming response in Agent Core response'
            }
        
        elapsed_time = time.time() - start_time
        logger.info(f"Agent Core processing took {elapsed_time:.2f} seconds")
        
        # Extract the final response text
        if agent_response_data and agent_response_data.get('success'):
            response_text = agent_response_data.get('response', '')
            
            # Clean up the response text (remove extra quotes, etc.)
            response_text = response_text.strip()
            
            # Try to parse as JSON if it looks like JSON
            if response_text.startswith('{') or response_text.startswith('['):
                try:
                    response_json = json.loads(response_text)
                    logger.info(f"Parsed JSON response: {json.dumps(response_json)[:500]}")
                    
                    # Extract result from known response formats
                    if 'result' in response_json:
                        response_text = response_json['result']
                        logger.info(f"Extracted 'result' field: {response_text[:500]}")
                    elif 'message' in response_json:
                        response_text = response_json['message']
                    elif 'output' in response_json:
                        response_text = response_json['output']
                    elif 'content' in response_json:
                        response_text = response_json['content']
                    else:
                        response_text = json.dumps(response_json)
                    
                    # If the result contains task status, handle it specially
                    if isinstance(response_text, str) and 'shop_background.start' in response_text:
                        logger.info("Agent started background shopping task")
                        response_text = "I've started searching for Echo Dot prices on Amazon. This may take a moment as I browse the website to find the current pricing information. Please wait..."
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON: {e}")
                    # Keep as plain text
            
            # Log trace information if available
            if agent_response_data.get('traces'):
                logger.info(f"Agent traces: {json.dumps(agent_response_data['traces'][:3])}")  # Log first 3 traces
            
            final_content = response_text if response_text else 'Agent Core task completed'
        else:
            error_msg = agent_response_data.get('error', 'Unknown error')
            final_content = f"Error: {error_msg}"
            logger.error(f"Agent Core error: {error_msg}")
        
        # Format response in tool registry format
        tool_result = {
            'type': 'tool_result',
            'name': tool_name,
            'tool_use_id': tool_use_id,
            'content': final_content
        }
        
        logger.info(f"Returning tool result: {json.dumps(tool_result)[:500]}...")
        return tool_result
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'type': 'tool_result',
            'name': event.get('name', 'browser_search'),
            'tool_use_id': event.get('id', 'error'),
            'content': f'Error: {str(e)}'
        }