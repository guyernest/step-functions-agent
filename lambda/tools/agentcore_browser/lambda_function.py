"""
Lambda handler for Agent Core Browser Tool
Routes to different Agent Core agents based on tool name
Handles streaming responses and long-running browser automation tasks
"""

import json
import boto3
from botocore.exceptions import ClientError
import os
import uuid
from typing import Dict, Any, Generator, Optional
import time
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities import parameters
from agent_config import get_agent_config, get_agent_arn, get_transformer, generate_presigned_urls

# Initialize AWS Lambda Powertools
logger = Logger(service="agentcore-browser")
tracer = Tracer()


def get_tool_credentials(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve credentials from the consolidated tool secrets for a specific tool.

    Uses AWS Lambda Powertools Parameters utility to fetch secrets:
    - Consolidated secret: /ai-agent/tool-secrets/{env_name}
    - Tool-specific section within the consolidated secret

    Args:
        tool_name: Name of the tool (e.g., 'browser_broadband')

    Returns:
        Dictionary with credentials or None if not configured

    Expected secret structure in consolidated secret:
    {
        "browser_broadband": {
            "username": "user@example.com",
            "password": "encrypted_password",
            "api_key": "optional_api_key"
        },
        "browser_shopping": {...},
        ...
    }
    """
    try:
        # Get environment name for secret path
        env_name = os.environ.get('ENVIRONMENT', os.environ.get('ENV_NAME', 'prod'))
        secret_name = os.environ.get('CONSOLIDATED_SECRET_NAME', f'/ai-agent/tool-secrets/{env_name}')

        # Use Powertools Parameters to get secret with caching
        consolidated_secret = parameters.get_secret(secret_name, transform='json')

        # Extract tool-specific credentials
        tool_secrets = consolidated_secret.get(tool_name, {})

        if tool_secrets:
            logger.info(f"Successfully retrieved credentials for {tool_name} (fields: {list(tool_secrets.keys())})")
            return tool_secrets
        else:
            # No credentials configured for this tool - this is OK
            logger.info(f"No credentials configured for {tool_name} in consolidated secret")
            return None

    except Exception as e:
        logger.error(f"Error retrieving credentials for {tool_name}: {e}")
        # Don't fail the request if credentials can't be retrieved
        # Let the agent handle missing credentials
        return None


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


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    """
    Lambda handler that routes to different Agent Core agents based on tool name
    Handles streaming responses for long-running browser automation tasks

    Expected input format from tool registry:
    {
        "id": "toolu_xxx",
        "name": "browser_broadband",  # or browser_shopping, browser_search
        "input": {
            # Tool-specific input fields
        }
    }
    """
    logger.info("Received tool invocation", extra={"event": event})
    
    # Get environment variables
    aws_region = os.environ.get('AWS_REGION')
    aws_account_id = os.environ.get('AWS_ACCOUNT_ID', '672915487120')
    
    
    try:
        # Extract tool use information
        tool_use_id = event.get('id', f'tool_{context.aws_request_id}')
        tool_name = event.get('name', 'browser_search')
        tool_input = event.get('input', {})
        
        logger.info(f"Tool name: {tool_name}")
        logger.info(f"Tool input: {json.dumps(tool_input)}")
        
        # Get agent configuration for this tool
        agent_config = get_agent_config(tool_name)
        if not agent_config:
            logger.error(f"Unknown tool name: {tool_name}")
            return {
                'type': 'tool_result',
                'name': tool_name,
                'tool_use_id': tool_use_id,
                'content': f'Error: Unknown tool name "{tool_name}". Supported tools: browser_broadband, browser_shopping, browser_search'
            }
        
        # Get the agent ARN for this tool
        agent_runtime_arn = get_agent_arn(tool_name, aws_region, aws_account_id)
        logger.info(f"Using Agent Runtime ARN: {agent_runtime_arn}")
        
        # Transform input using tool-specific transformer
        transform_input_func = get_transformer(agent_config['transform_input'])
        if not transform_input_func:
            logger.error(f"No input transformer found for {tool_name}")
            return {
                'type': 'tool_result',
                'name': tool_name,
                'tool_use_id': tool_use_id,
                'content': f'Error: Configuration error for tool {tool_name}'
            }
        
        # Transform the input to agent-specific format
        try:
            agent_payload = transform_input_func(tool_input)
            logger.info(f"Transformed payload: {json.dumps(agent_payload)}")
        except ValueError as e:
            logger.error(f"Input validation error: {str(e)}")
            return {
                'type': 'tool_result',
                'name': tool_name,
                'tool_use_id': tool_use_id,
                'content': f'Error: {str(e)}'
            }

        # Retrieve and inject credentials from consolidated tool secrets
        credentials = get_tool_credentials(tool_name)
        if credentials:
            # Inject credentials into the payload
            if 'input' not in agent_payload:
                agent_payload['input'] = {}
            agent_payload['input']['credentials'] = credentials
            logger.info(f"Injected credentials for {tool_name} (fields: {list(credentials.keys())})")
        else:
            logger.info(f"No credentials configured for {tool_name}")
        
        # Initialize Agent Core client
        from botocore.config import Config
        
        # Configure extended timeouts for browser automation
        # Lambda has 10 minute timeout, so we can wait up to 9 minutes
        config = Config(
            region_name=aws_region,
            read_timeout=540,  # 9 minutes for browser automation
            connect_timeout=30,
            retries={'max_attempts': 0}
        )
        
        agent_core_client = boto3.client('bedrock-agentcore', config=config)
        logger.info("Using bedrock-agentcore client")
        
        # Create session ID for this interaction (must be at least 33 characters)
        session_id = f'agentcore-session-{uuid.uuid4().hex}'
        logger.info(f"Using session ID: {session_id} (length: {len(session_id)})")
        
        # Prepare the payload for Agent Core
        payload = json.dumps(agent_payload).encode()
        logger.info(f"Sending payload to Agent Core: {agent_payload}")
        
        # Invoke Agent Core runtime - this returns a streaming response
        logger.info(f"Invoking Agent Core for {tool_name}")
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
            parsed_response = response_text
            if response_text.startswith('{') or response_text.startswith('['):
                try:
                    response_json = json.loads(response_text)
                    logger.info(f"Parsed JSON response: {json.dumps(response_json)[:500]}")
                    
                    # Extract result from known response formats
                    if 'result' in response_json:
                        parsed_response = response_json['result']
                        logger.info(f"Extracted 'result' field: {str(parsed_response)[:500]}")
                    elif 'message' in response_json:
                        parsed_response = response_json['message']
                    elif 'output' in response_json:
                        parsed_response = response_json['output']
                    elif 'content' in response_json:
                        parsed_response = response_json['content']
                    else:
                        parsed_response = response_json
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON: {e}")
                    # Keep as plain text
            
            # Transform output using tool-specific transformer
            transform_output_func = get_transformer(agent_config['transform_output'])
            if transform_output_func:
                try:
                    final_content = transform_output_func(parsed_response)
                    logger.info(f"Transformed output: {final_content[:500]}")
                except Exception as e:
                    logger.warning(f"Output transformation failed: {str(e)}")
                    final_content = str(parsed_response)
            else:
                final_content = str(parsed_response) if parsed_response else 'Agent Core task completed'
            
            # Log trace information if available
            if agent_response_data.get('traces'):
                logger.info(f"Agent traces: {json.dumps(agent_response_data['traces'][:3])}")  # Log first 3 traces
            
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