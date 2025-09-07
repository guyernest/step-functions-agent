"""
Agent Core Browser Tool Configuration
Maps tool names to Agent Core agent IDs and provides transformation functions
"""

from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger()

# Agent Core runtime configurations
AGENT_CONFIGS = {
    'browser_broadband': {
        'agent_id': 'broadband_checker_agent-KcXxkNFCkG',
        'agent_arn_suffix': 'runtime/broadband_checker_agent-KcXxkNFCkG',
        'description': 'UK broadband availability checker',
        'capabilities': ['broadband', 'telecom', 'uk-addresses', 'bt-wholesale'],
        'transform_input': 'transform_broadband_input',
        'transform_output': 'transform_broadband_output'
    },
    'browser_shopping': {
        'agent_id': 'shopping_agent-aw6O6r7uk5',
        'agent_arn_suffix': 'runtime/shopping_agent-aw6O6r7uk5',
        'description': 'E-commerce product search and price comparison',
        'capabilities': ['shopping', 'prices', 'products', 'amazon', 'ebay'],
        'transform_input': 'transform_shopping_input',
        'transform_output': 'transform_shopping_output'
    },
    'browser_search': {
        'agent_id': 'web_search_agent-3dH6uJ84DT',
        'agent_arn_suffix': 'runtime/web_search_agent-3dH6uJ84DT',
        'description': 'General web search and information extraction',
        'capabilities': ['search', 'extraction', 'web-scraping', 'research'],
        'transform_input': 'transform_search_input',
        'transform_output': 'transform_search_output'
    }
}


def get_agent_config(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get agent configuration for a given tool name
    
    Args:
        tool_name: Name of the tool (e.g., 'browser_broadband')
        
    Returns:
        Agent configuration dict or None if not found
    """
    return AGENT_CONFIGS.get(tool_name)


def get_agent_arn(tool_name: str, region: str = 'us-west-2', account_id: str = '672915487120') -> Optional[str]:
    """
    Build the full Agent Core runtime ARN for a tool
    
    Args:
        tool_name: Name of the tool
        region: AWS region
        account_id: AWS account ID
        
    Returns:
        Full ARN or None if tool not found
    """
    config = get_agent_config(tool_name)
    if not config:
        return None
    
    return f"arn:aws:bedrock-agentcore:{region}:{account_id}:{config['agent_arn_suffix']}"


def transform_broadband_input(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform browser_broadband input to Agent Core format
    
    Expected input:
    {
        "address": {
            "building_number": "13",
            "street": "Albion Drive",
            "town": "London",
            "postcode": "E8 4LX"
        }
    }
    
    Agent Core payload:
    {
        "test": true,  # Use test mode to wait for completion
        "address": {
            "building_number": "13",
            "street": "Albion Drive",
            "town": "London",
            "postcode": "E8 4LX"
        }
    }
    """
    # Pass through the address structure as-is
    # The broadband_checker_agent expects this exact format
    address = tool_input.get('address', {})
    
    # Validate required field
    if not address.get('postcode'):
        raise ValueError("Postcode is required for broadband checks")
    
    # Use test mode to ensure Lambda waits for completion
    # The agent's test handler will process the address and return results
    return {
        "test": True,
        "address": address,
        "max_steps": 10  # Allow more steps for complex addresses
    }


def transform_shopping_input(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform browser_shopping input to Agent Core format
    
    Expected input:
    {
        "query": "gaming laptops",
        "site": "amazon",
        "max_results": 10
    }
    
    Agent Core payload:
    {
        "prompt": "Search for gaming laptops on amazon",
        "test_mode": true
    }
    """
    query = tool_input.get('query', '')
    site = tool_input.get('site', 'amazon')
    max_results = tool_input.get('max_results', 10)
    
    if not query:
        raise ValueError("Query is required for shopping searches")
    
    # Build the prompt based on site selection
    if site == 'all':
        prompt = f"Search for {query} on multiple shopping sites and compare prices"
    else:
        prompt = f"Search for {query} on {site}"
    
    if max_results:
        prompt += f" (show up to {max_results} results)"
    
    return {
        "test": prompt  # Use test mode for immediate execution
    }


def transform_search_input(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform browser_search input to Agent Core format
    
    Expected input:
    {
        "query": "AI research papers",
        "url": "https://arxiv.org",
        "extract_fields": ["title", "authors", "date"]
    }
    
    Agent Core payload:
    {
        "prompt": "Search for AI research papers on https://arxiv.org and extract title, authors, date"
    }
    """
    query = tool_input.get('query', '')
    url = tool_input.get('url', '')
    extract_fields = tool_input.get('extract_fields', [])
    
    if not query:
        raise ValueError("Query is required for web searches")
    
    # Build the prompt
    if url:
        prompt = f"Search for {query} on {url}"
    else:
        prompt = f"Search the web for {query}"
    
    if extract_fields:
        fields_str = ", ".join(extract_fields)
        prompt += f" and extract the following information: {fields_str}"
    
    return {
        "prompt": prompt
    }


def generate_presigned_urls(s3_prefix: str, bucket_name: str = "nova-act-browser-results-prod-672915487120") -> list:
    """
    Generate presigned URLs for HTML recordings in S3
    
    Args:
        s3_prefix: S3 prefix path (e.g., "broadband-checker/broadband_check_E8 4LX_1757219331105/")
        bucket_name: S3 bucket name
        
    Returns:
        List of presigned URLs for HTML files
    """
    import boto3
    from botocore.exceptions import ClientError
    
    s3_client = boto3.client('s3', region_name='us-west-2')
    presigned_urls = []
    
    try:
        # List objects in the prefix
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=s3_prefix
        )
        
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                # Filter for HTML files
                if key.endswith('.html'):
                    try:
                        # Generate presigned URL valid for 1 hour
                        url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': bucket_name, 'Key': key},
                            ExpiresIn=3600
                        )
                        presigned_urls.append({
                            'filename': key.split('/')[-1],
                            'url': url
                        })
                        logger.info(f"Generated presigned URL for {key}")
                    except ClientError as e:
                        logger.error(f"Error generating presigned URL for {key}: {e}")
                        
    except ClientError as e:
        logger.error(f"Error listing S3 objects: {e}")
        
    return presigned_urls


def transform_broadband_output(agent_response: Any) -> str:
    """
    Transform broadband checker agent response to standard format
    
    Agent response might include:
    - Task status
    - Exchange and cabinet information
    - Speed data
    - Recording paths
    """
    logger.info(f"Transforming broadband output: {type(agent_response)}: {str(agent_response)[:500]}")
    
    # Log full response for debugging
    if isinstance(agent_response, dict):
        import json
        logger.info(f"Full agent response: {json.dumps(agent_response, default=str)}")
    
    if isinstance(agent_response, dict):
        # Check if this is a task status response
        if 'status' in agent_response:
            if agent_response['status'] == 'started':
                return f"Broadband check started for {agent_response.get('address', 'the specified address')}. Task ID: {agent_response.get('task_id', 'unknown')}"
            elif agent_response['status'] == 'error':
                return f"Error checking broadband: {agent_response.get('error', agent_response.get('message', 'Unknown error'))}"
            elif agent_response['status'] == 'completed':
                # Extract data from completed response
                data = agent_response.get('data', {})
                if data:
                    agent_response = data  # Process the data section
        
        # Check if this is a result response with exchange/cabinet info
        if 'exchange_name' in agent_response or 'cabinet_number' in agent_response or 'data' in agent_response:
            # Extract data if nested
            if 'data' in agent_response:
                data = agent_response['data']
            else:
                data = agent_response
            
            result_parts = []
            
            # Add task_id if available
            task_id = agent_response.get('task_id', '')
            if task_id:
                result_parts.append(f"Task ID: {task_id}")
            
            # Add address if available
            if 'address' in data:
                result_parts.append(f"Address: {data['address']}")
            
            # Exchange and cabinet info (show even if empty)
            exchange = data.get('exchange_name', '')
            cabinet = data.get('cabinet_number', '')
            result_parts.append(f"Exchange: {exchange if exchange else 'Not found'}")
            result_parts.append(f"Cabinet: {cabinet if cabinet else 'Not found'}")
            
            # Speed information
            if data.get('vdsl_range_a_downstream_high'):
                down_low = data.get('vdsl_range_a_downstream_low', '')
                down_high = data['vdsl_range_a_downstream_high']
                if down_low:
                    result_parts.append(f"Download Speed: {down_low}-{down_high} Mbps")
                else:
                    result_parts.append(f"Download Speed: up to {down_high} Mbps")
            
            if data.get('vdsl_range_a_upstream_high'):
                up_low = data.get('vdsl_range_a_upstream_low', '')
                up_high = data['vdsl_range_a_upstream_high']
                if up_low:
                    result_parts.append(f"Upload Speed: {up_low}-{up_high} Mbps")
                else:
                    result_parts.append(f"Upload Speed: up to {up_high} Mbps")
            
            # WLR3 availability
            if 'wlr3_available' in data:
                wlr3_status = "Yes" if data['wlr3_available'] else "No"
                result_parts.append(f"WLR3 Available: {wlr3_status}")
            
            # Recording path and presigned URLs
            recording_path = data.get('recording_path', '')
            session_id = data.get('session_id', '')
            
            if recording_path:
                result_parts.append(f"Recording: {recording_path}")
            elif task_id:
                # If no recording_path but we have task_id, construct expected path
                expected_path = f"s3://nova-act-browser-results-prod-672915487120/broadband-checker/{task_id}/"
                result_parts.append(f"Expected Recording: {expected_path}")
                recording_path = expected_path
            else:
                result_parts.append("Recording: Not available")
                
            if session_id:
                result_parts.append(f"Session ID: {session_id}")
            
            # Generate presigned URLs for HTML recordings
            if recording_path and recording_path.startswith('s3://'):
                # Parse S3 path: s3://bucket/prefix/
                s3_parts = recording_path.replace('s3://', '').split('/', 1)
                if len(s3_parts) == 2:
                    bucket = s3_parts[0]
                    prefix = s3_parts[1]
                    presigned_urls = generate_presigned_urls(prefix, bucket)
                    
                    if presigned_urls:
                        result_parts.append("\nBrowser Recording URLs (valid for 1 hour):")
                        for i, url_info in enumerate(presigned_urls, 1):
                            result_parts.append(f"  {i}. {url_info['filename']}: {url_info['url']}")
                    else:
                        result_parts.append("No HTML recordings found in S3 (might still be uploading)")
            
            if result_parts:
                return "\n".join(result_parts)
    
    # If response is a string, return it
    if isinstance(agent_response, str):
        return agent_response
    
    # Default: return as JSON string for debugging
    return json.dumps(agent_response, indent=2) if isinstance(agent_response, dict) else str(agent_response)


def transform_shopping_output(agent_response: Any) -> str:
    """
    Transform shopping agent response to standard format
    """
    # Shopping agent typically returns product listings
    if isinstance(agent_response, str):
        return agent_response
    elif isinstance(agent_response, dict):
        if 'products' in agent_response:
            # Format product list
            products = agent_response['products']
            if isinstance(products, list):
                result_lines = []
                for i, product in enumerate(products[:10], 1):
                    name = product.get('name', 'Unknown')
                    price = product.get('price', 'N/A')
                    result_lines.append(f"{i}. {name} - {price}")
                return "\n".join(result_lines)
        elif 'result' in agent_response:
            return agent_response['result']
    
    return str(agent_response)


def transform_search_output(agent_response: Any) -> str:
    """
    Transform search agent response to standard format
    """
    if isinstance(agent_response, str):
        return agent_response
    elif isinstance(agent_response, dict):
        if 'results' in agent_response:
            return json.dumps(agent_response['results'], indent=2)
        elif 'extracted_data' in agent_response:
            return json.dumps(agent_response['extracted_data'], indent=2)
        elif 'result' in agent_response:
            return agent_response['result']
    
    return str(agent_response)


# Export transformation functions for dynamic lookup
TRANSFORMERS = {
    'transform_broadband_input': transform_broadband_input,
    'transform_broadband_output': transform_broadband_output,
    'transform_shopping_input': transform_shopping_input,
    'transform_shopping_output': transform_shopping_output,
    'transform_search_input': transform_search_input,
    'transform_search_output': transform_search_output
}


def get_transformer(name: str):
    """Get a transformer function by name"""
    return TRANSFORMERS.get(name)