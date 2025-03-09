import os
import json
import sys
import socket
import subprocess
import uuid

def lambda_handler(event, context):
    """
    Test Lambda function for the Runtime API Proxy Extension.
    
    This function provides diagnostics about the Lambda environment and shows
    how the extension proxy modifies requests and responses.
    
    Parameters:
    event (dict): The event data passed to the Lambda function
    context (LambdaContext): Runtime information provided by AWS Lambda
    
    Returns:
    dict: A response with diagnostics information and the event payload
    """
    # Generate a unique ID for this invocation
    invocation_id = str(uuid.uuid4())
    
    # Print header with unique ID
    print("-" * 80)
    print(f"LAMBDA RUNTIME API PROXY TEST - ID: {invocation_id}")
    print("-" * 80)
    
    # Log incoming event
    print("\nRECEIVED EVENT:")
    print(json.dumps(event, indent=2))
    
    # Log essential environment variables for debugging
    runtime_api = os.environ.get('AWS_LAMBDA_RUNTIME_API', 'NOT SET')
    exec_wrapper = os.environ.get('AWS_LAMBDA_EXEC_WRAPPER', 'NOT SET')
    agent_context_table = os.environ.get('AGENT_CONTEXT_TABLE', 'NOT SET')
    max_content_size = os.environ.get('MAX_CONTENT_SIZE', 'NOT SET')
    
    print(f"\nKEY ENVIRONMENT VARIABLES:")
    print(f"  AWS_LAMBDA_RUNTIME_API = {runtime_api}")
    print(f"  AWS_LAMBDA_EXEC_WRAPPER = {exec_wrapper}")
    print(f"  AGENT_CONTEXT_TABLE = {agent_context_table}")
    print(f"  MAX_CONTENT_SIZE = {max_content_size}")
    
    # Test connectivity to runtime API
    print("\nCONNECTIVITY TESTS:")
    
    # Test proxy (9009)
    try:
        print("Testing connection to 127.0.0.1:9009 (proxy port)...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', 9009))
        proxy_connection = result == 0
        print(f"  Proxy connection successful: {proxy_connection}")
        s.close()
    except Exception as e:
        print(f"  Error testing proxy connectivity: {e}")
        proxy_connection = False
    
    # Check extension setup
    extension_status = "unknown"
    extension_path = "/opt/extensions/lrap"
    
    if os.path.exists(extension_path):
        extension_status = "installed"
        is_exec = os.access(extension_path, os.X_OK)
        if is_exec:
            extension_status = "executable"
    else:
        extension_status = "missing"
    
    # Check wrapper script
    wrapper_status = "unknown"
    
    if exec_wrapper != 'NOT SET':
        if os.path.exists(exec_wrapper):
            wrapper_status = "installed"
            is_exec = os.access(exec_wrapper, os.X_OK)
            if is_exec:
                wrapper_status = "executable"
                # Read wrapper content
                try:
                    with open(exec_wrapper, 'r') as f:
                        content = f.read().strip()
                        if "AWS_LAMBDA_RUNTIME_API" in content and "127.0.0.1:9009" in content:
                            wrapper_status = "configured correctly"
                except:
                    pass
        else:
            wrapper_status = "missing"
    else:
        wrapper_status = "not configured"
    
    # Include extended diagnostics if requested
    if event.get('diagnostics') == 'full':
        print("\nRUNNING FULL DIAGNOSTICS...")
        
        # List all environment variables
        print("\nALL ENVIRONMENT VARIABLES:")
        for key, value in sorted(os.environ.items()):
            print(f"  {key} = {value}")
        
        # List extensions directory
        print("\nEXTENSIONS DIRECTORY:")
        if os.path.exists('/opt/extensions'):
            for item in os.listdir('/opt/extensions'):
                path = os.path.join('/opt/extensions', item)
                if os.path.isfile(path):
                    is_exec = os.access(path, os.X_OK)
                    print(f"  {path} - Executable: {is_exec}")
                elif os.path.isdir(path):
                    print(f"  {path}/ (directory)")
        
        # Running processes
        print("\nRUNNING PROCESSES:")
        try:
            ps_output = subprocess.check_output(["ps", "-ef"], text=True)
            print(ps_output)
        except Exception as e:
            print(f"  Error getting process list: {e}")
    
    # Check if our event contains a content field with a DynamoDB reference that was transformed
    if 'content' in event and isinstance(event['content'], str):
        if not event['content'].startswith('@content:dynamodb:table:'):
            print(f"\n✅ INPUT TRANSFORM DETECTED! Content field was successfully retrieved")
    
    # Check for nested content with reference
    if 'nested' in event and 'content' in event['nested'] and isinstance(event['nested']['content'], str):
        if not event['nested']['content'].startswith('@content:dynamodb:table:'):
            print(f"\n✅ NESTED INPUT TRANSFORM DETECTED! Nested content field was successfully retrieved")
    
    # Check if we received any content references in array items
    if 'array_of_contents' in event:
        for i, item in enumerate(event.get('array_of_contents', [])):
            if 'content' in item and isinstance(item['content'], str):
                if not item['content'].startswith('@content:dynamodb:table:'):
                    print(f"\n✅ ARRAY INPUT TRANSFORM DETECTED! Array item {i} was successfully retrieved")
    
    # Generate test content of various sizes for testing the DynamoDB threshold
    small_content = "This is a small content field that should NOT be stored in DynamoDB"
    
    # Create content that's exactly at the threshold 
    threshold = int(max_content_size) if max_content_size != 'NOT SET' else 5000
    threshold_content = "T" * threshold
    print(f"\nCreated threshold content of exactly {len(threshold_content)} characters")
    
    # Create content that's just above the threshold
    large_content = "L" * (threshold + 100) 
    print(f"Created large content of {len(large_content)} characters (above threshold)")
    
    # Create very large content
    very_large_content = "V" * (threshold * 2)
    print(f"Created very large content of {len(very_large_content)} characters (2x threshold)")
    
    # Prepare a response that can be modified by the proxy
    response = {
        'statusCode': 200,
        'body': {
            'message': f'Test completed with ID: {invocation_id}',
            'timestamp': str(context.aws_request_id),
            'diagnostics': {
                'proxy_connection': proxy_connection,
                'extension_status': extension_status,
                'wrapper_status': wrapper_status,
                'runtime_api': runtime_api,
                'agent_context_table': agent_context_table,
                'max_content_size': max_content_size
            },
            'event': event,
            # Add content fields of different sizes to test DynamoDB threshold
            'small_content': {
                'content': small_content
            },
            'threshold_content': {
                'content': threshold_content
            },
            'large_content': {
                'content': large_content
            },
            'very_large_content': {
                'content': very_large_content
            },
            # Add nested content fields
            'nested': {
                'normal': 'This is a regular field (not transformed)',
                'content': very_large_content[:1000] + '...'
            },
            # Add content fields in an array
            'array_of_contents': [
                {'content': small_content},
                {'content': large_content[:500] + '...'}
            ]
        }
    }
    
    # For API Gateway compatibility
    return {
        'statusCode': 200,
        'body': json.dumps(response['body'])
    }