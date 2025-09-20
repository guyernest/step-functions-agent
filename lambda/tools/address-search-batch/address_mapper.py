"""
Address Search Batch Mapper
Specialized input/output mapper for UK address searches
"""

import json
import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Route to appropriate mapper based on action
    """
    action = event.get('action', 'map_input')
    
    if action == 'map_input':
        return map_address_input(event)
    elif action == 'map_output':
        return map_search_output(event)
    else:
        raise ValueError(f"Unknown action: {action}")

def map_address_input(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map address CSV row to web search agent input

    Expected CSV columns:
    - address: Full address string
    - postcode: UK postcode (optional)
    - property_name: Property or building name (optional)
    """
    row = event['row']
    mapping_config = event.get('mapping_config', {})

    # Check if we have a transformation template
    transformations = mapping_config.get('transformations', {})

    # Get the query transformation config
    query_transform = transformations.get('query', {})

    # Normalize postcode if present
    postcode = row.get('postcode', '')
    if postcode:
        postcode = normalize_uk_postcode(postcode)

    # Build the search query using template or fallback to simple concatenation
    if query_transform.get('type') == 'template':
        template_config = query_transform.get('config', {})
        template = template_config.get('template', '{address} {postcode}')
        variables = template_config.get('variables', {})

        # Prepare substitution values
        substitutions = {}
        for var_name, column_name in variables.items():
            value = row.get(column_name, '')
            # Use normalized postcode if it's the postcode field
            if column_name == 'postcode' and postcode:
                value = postcode
            substitutions[var_name] = value

        # Apply template substitution
        search_query = template
        for var_name, value in substitutions.items():
            search_query = search_query.replace(f'{{{var_name}}}', str(value))

        # Clean up any extra spaces
        search_query = ' '.join(search_query.split())
    else:
        # Fallback to simple concatenation if no template
        base_query = row.get('address', '')
        if postcode:
            search_query = f"{base_query} {postcode}".strip()
        else:
            search_query = base_query

    # Store original address for reference
    original_address = row.get('address', '')

    # Format for web-search-agent-unified which expects messages array
    return {
        "messages": [
            {
                "role": "user",
                "content": search_query
            }
        ],
        "metadata": {
            "original_address": original_address,
            "postcode": postcode,
            "search_type": "property_information",
            "max_results": 5
        }
    }

def map_search_output(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map agent results to structured information (property or broadband)
    """
    original_row = event.get('original_row', {})
    search_result = event.get('execution_result', {})

    # Start with original row data (but remove large fields)
    output = {k: v for k, v in original_row.items()
              if k not in ['execution_result', 'mapped_input']}

    # Extract search results - handle both agent execution and direct results
    if isinstance(search_result, dict):
        # Handle Step Functions execution result
        if 'Output' in search_result:
            actual_result = search_result['Output']
        else:
            actual_result = search_result
    else:
        actual_result = {"error": "Invalid result format"}

    # Parse information from search results
    extracted_info = extract_property_info(actual_result)

    # Check if this is broadband data or property data
    if 'download_speed' in extracted_info or 'exchange' in extracted_info:
        # Broadband-specific output
        output.update({
            "broadband_type": extracted_info.get('type', 'Unknown'),
            "exchange": extracted_info.get('exchange', ''),
            "cabinet": extracted_info.get('cabinet', ''),
            "download_speed": extracted_info.get('download_speed', ''),
            "upload_speed": extracted_info.get('upload_speed', ''),
            "search_summary": extracted_info.get('summary', ''),
            "data_source": "broadband checker"
        })
    else:
        # Property-specific output
        output.update({
            "property_type": extracted_info.get('type', 'Unknown'),
            "bedrooms": extracted_info.get('bedrooms', ''),
            "estimated_value": extracted_info.get('estimated_value', ''),
            "council_tax_band": extracted_info.get('council_tax_band', ''),
            "last_sold": extracted_info.get('last_sold', ''),
            "floor_area": extracted_info.get('floor_area', ''),
            "search_summary": extracted_info.get('summary', ''),
            "data_source": extracted_info.get('source', 'web search')
        })

    # Add minimal metadata
    if '_row_number' in original_row:
        output['_row_number'] = original_row['_row_number']
    if '_row_id' in original_row:
        output['_row_id'] = original_row['_row_id']

    # Add execution status from metadata if available
    execution_metadata = event.get('execution_metadata', {})
    output['_status'] = execution_metadata.get('status', 'UNKNOWN')
    if 'error_message' in execution_metadata:
        output['_error'] = execution_metadata['error_message']

    return output

def normalize_uk_postcode(postcode: str) -> str:
    """
    Normalize UK postcode to standard format
    """
    if not postcode:
        return ""
    
    # Remove spaces and convert to uppercase
    postcode = postcode.upper().replace(' ', '')
    
    # UK postcode pattern
    if len(postcode) >= 5:
        # Insert space before last 3 characters
        return f"{postcode[:-3]} {postcode[-3:]}"
    
    return postcode

def extract_property_info(search_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured information from agent results (property or broadband)
    """
    info = {
        'type': 'Unknown',
        'summary': ''
    }

    # Check if this is a broadband agent response
    if 'messages' in search_result:
        # Extract from the last assistant message
        messages = search_result.get('messages', [])
        for msg in reversed(messages):
            if msg.get('role') == 'assistant':
                content = msg.get('content', [])
                if isinstance(content, list):
                    # Look for text content
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text = item.get('text', '')
                            info.update(extract_broadband_info(text))
                            break
                elif isinstance(content, str):
                    info.update(extract_broadband_info(content))
                break

        # Also check for tool results
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'tool_result':
                            tool_content = item.get('content', '')
                            if 'Download Speed:' in tool_content:
                                info.update(extract_broadband_info(tool_content))

        return info

    # Original property search logic
    results = search_result.get('results', [])
    if not results:
        results = search_result.get('search_results', [])

    # Combine relevant text from search results
    combined_text = ""
    sources = []

    for result in results[:5]:  # Look at top 5 results
        if isinstance(result, dict):
            snippet = result.get('snippet', '') or result.get('description', '')
            title = result.get('title', '')
            combined_text += f"{title} {snippet} "

            source = result.get('source') or result.get('url', '')
            if source:
                sources.append(source)

    # Extract property type
    property_types = ['detached', 'semi-detached', 'terraced', 'flat', 'apartment',
                     'bungalow', 'cottage', 'maisonette', 'house']
    for ptype in property_types:
        if ptype in combined_text.lower():
            info['type'] = ptype.title()
            break

    # Extract bedrooms
    bedroom_match = re.search(r'(\d+)\s*(?:bed|bedroom)', combined_text, re.IGNORECASE)
    if bedroom_match:
        info['bedrooms'] = bedroom_match.group(1)

    # Extract council tax band
    tax_band_match = re.search(r'(?:council tax |tax band |band )([A-H])', combined_text, re.IGNORECASE)
    if tax_band_match:
        info['council_tax_band'] = f"Band {tax_band_match.group(1).upper()}"

    # Extract price/value
    price_match = re.search(r'£([\d,]+(?:k|K)?)', combined_text)
    if price_match:
        price_str = price_match.group(1).replace(',', '')
        if 'k' in price_str.lower():
            price_str = price_str.lower().replace('k', '000')
        info['estimated_value'] = f"£{int(float(price_str)):,}"

    # Extract last sold date
    sold_match = re.search(r'(?:sold|sale) (?:in |on )?(\d{4}|\w+ \d{4})', combined_text, re.IGNORECASE)
    if sold_match:
        info['last_sold'] = sold_match.group(1)

    # Extract floor area
    area_match = re.search(r'(\d+)\s*(?:sq\.?\s*ft|square feet|m²|sqm)', combined_text, re.IGNORECASE)
    if area_match:
        area_value = area_match.group(1)
        area_unit = 'sq ft' if 'ft' in area_match.group(0).lower() else 'm²'
        info['floor_area'] = f"{area_value} {area_unit}"

    # Create summary
    if results:
        first_result = results[0]
        if isinstance(first_result, dict):
            info['summary'] = first_result.get('snippet', '')[:200]

    # Add source information
    if sources:
        info['source'] = sources[0] if len(sources) == 1 else f"Multiple ({len(sources)} sources)"

    return info

def extract_broadband_info(text: str) -> Dict[str, Any]:
    """
    Extract broadband information from text
    """
    info = {}

    # Extract exchange - handle variations like "WHITEHALL" or "KINGSLAND GREEN"
    exchange_match = re.search(r'Exchange[:\s]+([A-Z][A-Z\s]+?)(?:\n|Cabinet)', text, re.IGNORECASE)
    if exchange_match:
        info['exchange'] = exchange_match.group(1).strip()

    # Extract cabinet - handle "Not found" case
    cabinet_match = re.search(r'Cabinet[:\s]+([\w\s]+?)(?:\n|Download)', text, re.IGNORECASE)
    if cabinet_match:
        cabinet_value = cabinet_match.group(1).strip()
        info['cabinet'] = cabinet_value if cabinet_value.lower() != 'not found' else 'Direct Exchange'

    # Extract download speed
    download_match = re.search(r'Download Speed[:\s]+([\d.-]+\s*(?:Mbps|Gbps))', text, re.IGNORECASE)
    if download_match:
        info['download_speed'] = download_match.group(1)

    # Extract upload speed
    upload_match = re.search(r'Upload Speed[:\s]+([\d.-]+\s*(?:Mbps|Gbps))', text, re.IGNORECASE)
    if upload_match:
        info['upload_speed'] = upload_match.group(1)

    # Determine broadband type based on speeds and text content
    if 'download_speed' in info:
        speed_str = info['download_speed'].lower()
        if '330' in speed_str or 'gbps' in speed_str:
            info['type'] = 'FTTP/Full Fiber'
        elif '50' in speed_str or '74' in speed_str or '80' in speed_str:
            info['type'] = 'VDSL/FTTC'
        else:
            info['type'] = 'Broadband'
    elif 'VDSL' in text or 'FTTC' in text:
        info['type'] = 'VDSL/FTTC'
    elif 'FTTP' in text or 'Fiber to the Premises' in text:
        info['type'] = 'FTTP'
    elif 'ADSL' in text:
        info['type'] = 'ADSL'
    else:
        info['type'] = 'Broadband'

    # Create summary
    if 'download_speed' in info and 'upload_speed' in info:
        info['summary'] = f"{info.get('download_speed', 'N/A')} download, {info.get('upload_speed', 'N/A')} upload"

    # If we found any broadband info, mark it as found
    if info:
        info['found'] = True

    return info

# Test cases
if __name__ == "__main__":
    # Test input mapping
    test_input = {
        "action": "map_input",
        "row": {
            "address": "10 Downing Street, Westminster, London",
            "postcode": "SW1A 2AA"
        },
        "config": {}
    }
    
    print("Test Input Mapping:")
    print(json.dumps(map_address_input(test_input), indent=2))
    
    # Test output mapping
    test_output = {
        "action": "map_output",
        "original_row": {
            "address": "10 Downing Street",
            "postcode": "SW1A 2AA"
        },
        "execution_result": {
            "results": [
                {
                    "title": "10 Downing Street - Grade I Listed Building",
                    "snippet": "Georgian terraced house, 4 bedrooms, Council Tax Band H",
                    "url": "example.com"
                }
            ]
        }
    }
    
    print("\nTest Output Mapping:")
    print(json.dumps(map_search_output(test_output), indent=2))