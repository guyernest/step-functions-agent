#!/usr/bin/env python3
"""
Broadband Availability Checker Agent for Bedrock Agent Core
Extracts broadband service availability data from BT Wholesale portal
"""

import logging
import json
import time
import threading
import os
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Import Agent Core components
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.tools.browser_client import browser_session
from strands import Agent, tool
from strands.multiagent import GraphBuilder
from strands_tools import file_write, file_read
from strands.models import BedrockModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configure Nova Act timeouts to handle slow responses
os.environ["NOVA_ACT_STEP_TIMEOUT"] = "60"  # 60 seconds timeout per step
os.environ["NOVA_ACT_MAX_RETRIES"] = "3"    # Retry failed requests

# Function to get Nova Act API key
def get_nova_act_api_key():
    """Get Nova Act API key from environment or AWS Parameter Store"""
    # First try environment variable
    api_key = os.environ.get("NOVA_ACT_API_KEY")
    if api_key and api_key != "placeholder-api-key":
        return api_key
    
    # Try AWS Parameter Store
    try:
        ssm = boto3.client('ssm', region_name='us-west-2')
        response = ssm.get_parameter(
            Name='/agentcore/nova-act-api-key',
            WithDecryption=True
        )
        api_key = response['Parameter']['Value']
        if api_key and api_key != "placeholder-api-key":
            return api_key
    except Exception as e:
        logger.warning(f"Could not retrieve Nova Act API key from Parameter Store: {e}")
    
    # Return empty string if no valid key found
    logger.warning("Nova Act API key not found - browser automation may fail")
    return ""

# Get and set the API key
nova_act_key = get_nova_act_api_key()
if nova_act_key:
    os.environ["NOVA_ACT_API_KEY"] = nova_act_key
    logger.info("Nova Act API key configured")
else:
    logger.warning("Warning: Nova Act API key not found - you need to set it in Parameter Store or environment")


# Initialize the app
app = BedrockAgentCoreApp()

# Use Nova Pro model
nova_pro = BedrockModel(model_id="us.amazon.nova-pro-v1:0")

# Set bypass tool consent
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Track active tasks for health check
active_tasks = set()
last_update_time = time.time()

# ============== Configuration Classes ==============

@dataclass
class ExtractionRule:
    """Defines a rule for extracting data from the broadband checker results"""
    field_name: str
    selector_path: str  # CSS selector or text pattern
    condition_field: Optional[str] = None  # Field to check for conditional extraction
    condition_value: Optional[str] = None  # Value to match for condition
    fallback_value: Optional[str] = None  # Default value if not found
    data_type: str = "string"  # string, number, boolean
    
@dataclass
class AddressInput:
    """Structured address input"""
    building_number: Optional[str] = None
    building_name: Optional[str] = None
    street: Optional[str] = None
    town: Optional[str] = None
    postcode: Optional[str] = None
    
    def to_search_string(self) -> str:
        """Convert to search string for the portal"""
        parts = []
        if self.building_number:
            parts.append(self.building_number)
        if self.building_name:
            parts.append(self.building_name)
        if self.street:
            parts.append(self.street)
        if self.town:
            parts.append(self.town)
        if self.postcode:
            parts.append(self.postcode)
        return ", ".join(filter(None, parts))

@dataclass
class BroadbandCheckResult:
    """Structured result from broadband availability check"""
    address: str
    address_selected: str
    exchange_name: str
    cabinet_number: str
    vdsl_range_a_downstream_high: Optional[float] = None
    vdsl_range_a_downstream_low: Optional[float] = None
    vdsl_range_a_upstream_high: Optional[float] = None
    vdsl_range_a_upstream_low: Optional[float] = None
    vdsl_range_b_downstream_high: Optional[float] = None
    vdsl_range_b_downstream_low: Optional[float] = None
    gfast_range_a_available: bool = False
    gfast_range_b_available: bool = False
    fttp_available: bool = False
    fttp_install_process: Optional[str] = None
    wlr_withdrawal: bool = False
    soadsl_restriction: bool = False
    session_id: Optional[str] = None
    recording_path: Optional[str] = None
    extraction_timestamp: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

# ============== Extraction Configuration ==============

# Flexible extraction rules configuration - can be loaded from file or database
EXTRACTION_RULES = [
    # VDSL Range A (Clean) - Always extract when available
    ExtractionRule(
        field_name="vdsl_range_a_downstream_high",
        selector_path="VDSL Range A (Clean) -> Downstream Line Rate -> High",
        data_type="number"
    ),
    ExtractionRule(
        field_name="vdsl_range_a_downstream_low",
        selector_path="VDSL Range A (Clean) -> Downstream Line Rate -> Low",
        data_type="number"
    ),
    ExtractionRule(
        field_name="vdsl_range_a_upstream_high",
        selector_path="VDSL Range A (Clean) -> Upstream Line Rate -> High",
        data_type="number"
    ),
    ExtractionRule(
        field_name="vdsl_range_a_upstream_low",
        selector_path="VDSL Range A (Clean) -> Upstream Line Rate -> Low",
        data_type="number"
    ),
    
    # VDSL Range B (Impacted) - Extract when G.fast A is unavailable
    ExtractionRule(
        field_name="vdsl_range_b_downstream_high",
        selector_path="VDSL Range B (Impacted) -> Downstream Line Rate -> High",
        condition_field="gfast_range_a_available",
        condition_value="false",
        data_type="number"
    ),
    
    # G.fast availability
    ExtractionRule(
        field_name="gfast_range_a_available",
        selector_path="G.fast Range A (Clean) -> WBC SOGEA Availability",
        data_type="boolean"
    ),
    
    # FTTP availability
    ExtractionRule(
        field_name="fttp_available",
        selector_path="FTTP on Demand -> Availability Date",
        data_type="boolean"
    ),
    
    # Exchange restrictions
    ExtractionRule(
        field_name="wlr_withdrawal",
        selector_path="WLR Withdrawal -> Status",
        data_type="boolean"
    ),
]

# ============== Helper Functions ==============

def _parse_address_string(address_str: str) -> AddressInput:
    """
    Parse a string address into components
    Handles formats like:
    - "13C Albion Dr, London E8 4LX, UK"
    - "13 Albion Drive, Hackney, London, E8 4LX"
    - "Flat 2, 45 High Street, Manchester M1 2AB"
    """
    import re
    
    # Clean up the address string
    address_str = address_str.strip()
    
    # Extract UK postcode (pattern: letter(s) + number(s) + space + number + letter(s))
    postcode_pattern = r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2})\b'
    postcode_match = re.search(postcode_pattern, address_str, re.IGNORECASE)
    
    postcode = ""
    address_without_postcode = address_str
    
    if postcode_match:
        postcode = postcode_match.group(1).upper()
        # Remove postcode and any trailing comma/country from the address
        address_without_postcode = address_str[:postcode_match.start()].strip().rstrip(',')
        # Also remove anything after postcode (like ", UK")
        remainder = address_str[postcode_match.end():].strip().lstrip(',').strip()
    
    # Split the remaining address by commas
    parts = [p.strip() for p in address_without_postcode.split(',')]
    
    # Try to identify components
    building_number = ""
    building_name = ""
    street = ""
    town = ""
    
    if parts:
        # First part usually contains building number/name and street
        first_part = parts[0]
        
        # Extract building number (digits optionally followed by a letter)
        number_match = re.match(r'^(\d+[A-Za-z]?)\s+(.+)$', first_part)
        if number_match:
            building_number = number_match.group(1)
            street = number_match.group(2)
        elif first_part.lower().startswith(('flat', 'apartment', 'unit')):
            # Handle flat/apartment format
            building_name = first_part
            if len(parts) > 1:
                # Next part might be number + street
                second_part = parts[1]
                number_match = re.match(r'^(\d+[A-Za-z]?)\s+(.+)$', second_part)
                if number_match:
                    building_number = number_match.group(1)
                    street = number_match.group(2)
                    parts = parts[2:]  # Skip the parts we've used
                else:
                    street = second_part
                    parts = parts[2:]
            parts = parts[1:] if parts else []
        else:
            # Assume the whole first part is the street
            street = first_part
            parts = parts[1:]
    
    # Remaining parts are usually town/city
    if parts:
        # Join remaining parts as town (handles "Hackney, London" -> "Hackney, London")
        town = ", ".join(parts)
    
    # Ensure required fields have values
    if not street and building_name:
        # If we only have building name, use it as street
        street = building_name
        building_name = ""
    
    if not town:
        town = "London"  # Default to London if no town found
    
    logger.info(f"Parsed address: number='{building_number}', name='{building_name}', street='{street}', town='{town}', postcode='{postcode}'")
    
    return AddressInput(
        building_number=building_number or None,
        building_name=building_name or None,
        street=street or None,
        town=town or None,
        postcode=postcode or None
    )

# ============== Browser Automation Functions ==============

@tool(name="check_broadband_availability", 
      description="Check broadband availability for a given address using BT Wholesale portal")
def check_broadband_availability(
    address: Dict[str, str],
    extract_fields: Optional[List[str]] = None,
    wait_for_completion: bool = False,
    max_steps: int = 10
) -> Dict[str, Any]:
    """
    Check broadband availability for an address
    
    Args:
        address: Dictionary with address components (building_number, street, town, postcode)
        extract_fields: Optional list of specific fields to extract
        wait_for_completion: Whether to wait for task completion before returning
    
    Returns:
        Dictionary with task status and results location
    """
    logger.info(f"Starting broadband availability check for address: {address}")
    
    # Convert to AddressInput - handle both string and dict formats
    if isinstance(address, str):
        # Parse string address into components
        addr_input = _parse_address_string(address)
    elif isinstance(address, dict):
        # Use structured address
        addr_input = AddressInput(**address)
    else:
        return {
            "status": "error",
            "message": f"Invalid address format. Expected string or dict, got {type(address).__name__}"
        }
    
    # Create task ID - use timestamp to ensure uniqueness
    task_id = f"broadband_check_{addr_input.postcode}_{int(time.time()*1000)}"
    
    # Check if we're already processing this address
    for active_task in active_tasks:
        if addr_input.postcode in active_task:
            logger.info(f"Check already in progress for postcode {addr_input.postcode}")
            return {
                "status": "duplicate",
                "task_id": active_task,
                "message": f"A check is already in progress for {addr_input.postcode}"
            }
    
    # Add to app's task tracking
    app.add_async_task(task_id)
    
    try:
        # Start browser task in background
        thread = threading.Thread(
            target=_run_broadband_check,
            args=(addr_input, extract_fields, task_id, max_steps),
            daemon=True
        )
        thread.start()
        
        if wait_for_completion:
            # Wait for thread to complete (with timeout)
            thread.join(timeout=120)
            
        return {
            "status": "started",
            "task_id": task_id,
            "address": addr_input.to_search_string(),
            "message": "Broadband check started. Results will be saved when complete."
        }
        
    except Exception as e:
        app.complete_async_task(task_id)
        logger.error(f"Broadband check error: {e}")
        return {
            "status": "error",
            "task_id": task_id,
            "error": str(e)
        }

def _run_broadband_check(
    address: AddressInput,
    extract_fields: Optional[List[str]],
    task_id: str,
    max_steps: int = 10
) -> BroadbandCheckResult:
    """
    Run the actual broadband check using Nova Act
    """
    global active_tasks, last_update_time
    
    # Add task to active set
    active_tasks.add(task_id)
    last_update_time = time.time()
    
    result = BroadbandCheckResult(
        address=address.to_search_string(),
        address_selected="",
        exchange_name="",
        cabinet_number="",
        extraction_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    try:
        # Try to create browser session with error handling
        logger.info(f"Creating browser session for address: {address.to_search_string()}")
        
        try:
            browser_client = browser_session("us-west-2")
        except Exception as browser_error:
            logger.error(f"Failed to create browser session: {browser_error}")
            # If SSL error, provide more context
            if "SSL" in str(browser_error) or "certificate" in str(browser_error).lower():
                logger.error("SSL certificate issue detected. This might be due to corporate proxy or firewall.")
                result.error = f"SSL/Certificate error: {str(browser_error)}"
            else:
                result.error = f"Browser session error: {str(browser_error)}"
            _save_results(result, task_id)
            return result
        
        with browser_client as client:
            logger.info("Browser session started successfully")
            time.sleep(3)
            
            ws_url, headers = client.generate_ws_headers()
            
            # Import Nova Act
            from nova_act import NovaAct
            
            # Go directly to the Address Checker form page
            starting_url = "https://www.broadbandchecker.btwholesale.com/#/ADSL/AddressHome"
            
            logger.info(f"Using starting URL: {starting_url}")
            
            # Configure Nova Act with S3 recording
            try:
                from nova_act.util.s3_writer import S3Writer
                
                # Create boto3 session for S3Writer
                boto_session = boto3.Session(region_name='us-west-2')
                
                # Create S3Writer for recording storage
                s3_writer = S3Writer(
                    boto_session=boto_session,
                    s3_bucket_name="nova-act-browser-results-prod-672915487120",
                    s3_prefix=f"broadband-checker/{task_id}/",
                    metadata={
                        "Agent": "broadband_checker",
                        "TaskID": task_id,
                        "Address": address.to_search_string()
                    }
                )
                
                with NovaAct(
                    cdp_endpoint_url=ws_url,
                    cdp_headers=headers,
                    nova_act_api_key=os.environ.get("NOVA_ACT_API_KEY", ""),
                    starting_page=starting_url,
                    stop_hooks=[s3_writer],
                    record_video=False,  # Set to True if video recording is needed
                    ignore_https_errors=True  # Bypass SSL verification for BT website
                ) as nova_act:
                    # Step 1: Fill and submit form
                    logger.info("📝 Step 1: Filling and submitting form...")
                    form_prompt = f"""
                    Fill form: Building Number "{address.building_number}", 
                    Street "{address.street}", Town "{address.town}", 
                    PostCode "{address.postcode}". Click Submit.
                    """
                    
                    result1 = nova_act.act(form_prompt)
                    logger.info("✓ Form submitted")
                    
                    # Wait for page to load
                    time.sleep(3)
                    
                    # Step 2: Select address from list
                    logger.info("📍 Step 2: Selecting address...")
                    result2 = nova_act.act("Click the first address in the list")
                    logger.info("✓ Address selected")
                    
                    # Wait for navigation to AddressFeatureProduct page
                    time.sleep(3)
                    
                    # Step 3: Verify we're on the results page
                    logger.info("🔍 Step 3: Verifying we're on results page...")
                    page_check = nova_act.act("""
                    Tell me:
                    1. What is in the browser URL bar? (should contain AddressFeatureProduct)
                    2. Is there a section showing "Line Test Results" or similar?
                    3. Do you see tabs like "Features" and "Products"?
                    4. Is there address information displayed at the top?
                    """)
                    logger.info(f"Page verification: {page_check.response[:200] if page_check.response else 'No response'}")
                    
                    # Step 4: Look for specific data fields
                    logger.info("📊 Step 4: Looking for specific data fields...")
                    data_check = nova_act.act("""
                    On this AddressFeatureProduct page, look for these specific items:
                    
                    Under "Line Test Results" or main content area:
                    - Text that says "Exchange" followed by a name
                    - Text that says "Cabinet" followed by a number
                    - Text about "VDSL Range A" or "Clean" speeds
                    - Downstream Line Rate values
                    - Upstream Line Rate values
                    - Text saying "WLR3 AVAILABLE" or "WLR3 NOT AVAILABLE"
                    
                    Tell me exactly what text you see for each of these.
                    """)
                    
                    if data_check.response:
                        logger.info(f"Data fields found: {data_check.response[:500]}")
                    
                    # Step 5: Extract specific values
                    logger.info("🎯 Step 5: Extracting specific values...")
                    extraction = nova_act.act("""
                    Please extract these exact values:
                    1. After "Exchange:" what is the name? (e.g., DALSTON)
                    2. After "Cabinet" what is the number? (e.g., 42)
                    3. What are the downstream speed numbers?
                    4. What are the upstream speed numbers?
                    5. Is WLR3 showing as AVAILABLE or NOT AVAILABLE?
                    
                    Give me just the values, one per line.
                    """)
                    
                    if extraction.response:
                        logger.info(f"Extracted values: {extraction.response}")
                        
                        # Parse the extraction response
                        result = _parse_detailed_response(
                            extraction.response,
                            data_check.response if data_check.response else "",
                            result
                        )
                    
                    # Add session info and S3 path
                    result.session_id = str(extraction.metadata.session_id if extraction else result1.metadata.session_id)
                    result.address_selected = address.to_search_string()
                    
                    # S3Writer will automatically upload the recording
                    s3_location = f"s3://nova-act-browser-results-prod-672915487120/broadband-checker/{task_id}/"
                    result.recording_path = s3_location
                    logger.info(f"Session {result.session_id} - Recording uploaded to S3: {s3_location}")
                    logger.info(f"Files will include act_*.html and other session data")
            except AttributeError as attr_err:
                # Handle the __traceback__ assignment error specifically
                logger.warning(f"Nova Act attribute error (likely __traceback__): {str(attr_err)}")
                # Continue with partial results
            except Exception as nova_err:
                logger.error(f"Nova Act error: {str(nova_err)}")
                result.error = str(nova_err)
                
                # Save results to file
                _save_results(result, task_id)
                
                # Log the extracted data
                logger.info(f"Broadband check completed for {address.to_search_string()}")
                logger.info(f"Extraction results: Exchange={result.exchange_name}, Cabinet={result.cabinet_number}")
                if result.session_id:
                    logger.info(f"Nova Act session ID: {result.session_id}")
                    logger.info(f"Recording should be at: {result.recording_path}")
                
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in broadband check: {error_msg}")
        result.error = error_msg
        # Save error results without accessing __traceback__
        try:
            _save_results(result, task_id)
        except Exception as save_error:
            logger.error(f"Error saving results: {str(save_error)}")
    
    finally:
        # Remove task from active set
        active_tasks.discard(task_id)
        last_update_time = time.time()
        
        try:
            app.complete_async_task(task_id)
        except Exception as complete_error:
            logger.error(f"Error completing task: {complete_error}")
    
    return result

def _create_extraction_prompt(address: AddressInput, extract_fields: Optional[List[str]]) -> str:
    """
    Create a concise prompt for Nova Act to perform the broadband check
    """
    # Build a simple, direct prompt like the apartment example
    prompt = f"""Click on "Address Checker" tab if not already selected.
Enter this address in the form:
- Building Number: {address.building_number or ''}
- Street: {address.street or ''}
- Town: {address.town or ''}
- Postcode: {address.postcode or ''}

Click Submit.

If an address list appears, select the closest match to: {address.to_search_string()}

Once on the results page, extract:
   - Exchange name (e.g., "KINGSLAND GREEN")
   - Cabinet number (e.g., "Cabinet 9")
   - VDSL Range A (Clean) - Downstream Line Rate (High and Low values)
   - VDSL Range A (Clean) - Upstream Line Rate (High and Low values)
   - VDSL Range B (Impacted) - Downstream Line Rate (if available)
   - G.fast Range A - WBC SOGEA Availability status
   - FTTP on Demand - Availability status
   - WLR Withdrawal status (Y/N)
   - SOADSL Restriction status (Y/N)

5. Return the extracted data in a structured format with clear labels for each field.

Important: 
- If a field shows "Unavailable" or "--", record it as such
- Include the actual address that was selected from the list
- Be precise with numeric values (e.g., "80" for downstream high, "74" for low)
"""
    
    # Add specific field requirements if provided
    if extract_fields:
        prompt += f"\n\nFocus especially on these fields: {', '.join(extract_fields)}"
    
    return prompt

def _parse_nova_response(response: str, result: BroadbandCheckResult, original_address: str) -> BroadbandCheckResult:
    """
    Parse Nova Act response and extract structured data
    """
    try:
        # This is a simplified parser - in production, you'd want more robust parsing
        # Nova Act typically returns structured responses we can parse
        
        lines = response.lower().split('\n')
        
        for line in lines:
            # Parse exchange and cabinet
            if 'exchange' in line and 'cabinet' in line:
                parts = line.split('cabinet')
                if len(parts) > 1:
                    result.cabinet_number = parts[1].strip().split()[0]
            
            # Parse VDSL Range A values
            if 'vdsl range a' in line or 'downstream' in line:
                # Extract numeric values
                import re
                numbers = re.findall(r'\d+\.?\d*', line)
                if numbers and 'high' in line:
                    result.vdsl_range_a_downstream_high = float(numbers[0])
                elif numbers and 'low' in line:
                    result.vdsl_range_a_downstream_low = float(numbers[0])
            
            # Parse availability flags
            if 'fttp' in line and 'available' in line:
                result.fttp_available = 'unavailable' not in line
            
            if 'wlr withdrawal' in line:
                result.wlr_withdrawal = 'y' in line or 'yes' in line
                
    except Exception as e:
        logger.error(f"Error parsing Nova response: {e}")
        result.error = f"Parsing error: {str(e)}"
    
    return result

def _parse_detailed_response(extraction_response: str, data_response: str, result: BroadbandCheckResult) -> BroadbandCheckResult:
    """
    Parse the detailed extraction response from Nova Act
    Based on the working approach from test_bt_verify_page.py
    """
    try:
        import re
        
        # Combine both responses for better parsing
        full_response = f"{extraction_response}\n{data_response}"
        
        # Parse Exchange name
        exchange_match = re.search(r'exchange[:\s]+([A-Z\s]+)', full_response, re.IGNORECASE)
        if exchange_match:
            exchange = exchange_match.group(1).strip()
            # Clean up common formatting
            exchange = exchange.replace(':', '').strip()
            if exchange and exchange.upper() != "EXCHANGE":
                result.exchange_name = exchange.upper()
        
        # Parse Cabinet number
        cabinet_match = re.search(r'cabinet[\s:]*(\d+)', full_response, re.IGNORECASE)
        if cabinet_match:
            result.cabinet_number = f"Cabinet {cabinet_match.group(1)}"
        
        # Parse downstream speeds - look for patterns like "80, 74" or "80/74" or "High: 80 Low: 74"
        downstream_pattern = r'downstream[^0-9]*(\d+)[^0-9]+(\d+)'
        downstream_match = re.search(downstream_pattern, full_response, re.IGNORECASE)
        if downstream_match:
            result.vdsl_range_a_downstream_high = float(downstream_match.group(1))
            result.vdsl_range_a_downstream_low = float(downstream_match.group(2))
        else:
            # Try alternate patterns
            if "downstream" in full_response.lower():
                numbers = re.findall(r'\d+', full_response.split('downstream')[1].split('\n')[0])
                if len(numbers) >= 2:
                    result.vdsl_range_a_downstream_high = float(numbers[0])
                    result.vdsl_range_a_downstream_low = float(numbers[1])
        
        # Parse upstream speeds
        upstream_pattern = r'upstream[^0-9]*(\d+)[^0-9]+(\d+)'
        upstream_match = re.search(upstream_pattern, full_response, re.IGNORECASE)
        if upstream_match:
            result.vdsl_range_a_upstream_high = float(upstream_match.group(1))
            result.vdsl_range_a_upstream_low = float(upstream_match.group(2))
        else:
            # Try alternate patterns
            if "upstream" in full_response.lower():
                numbers = re.findall(r'\d+', full_response.split('upstream')[1].split('\n')[0])
                if len(numbers) >= 2:
                    result.vdsl_range_a_upstream_high = float(numbers[0])
                    result.vdsl_range_a_upstream_low = float(numbers[1])
        
        # Parse WLR3 availability
        if "wlr3" in full_response.lower():
            if "not available" in full_response.lower():
                result.wlr_withdrawal = True
            elif "available" in full_response.lower():
                result.wlr_withdrawal = False
        
        # Parse FTTP availability
        if "fttp" in full_response.lower():
            if "available" in full_response.lower() and "not available" not in full_response.lower():
                result.fttp_available = True
            else:
                result.fttp_available = False
        
        # Parse G.fast availability
        if "g.fast" in full_response.lower() or "gfast" in full_response.lower():
            if "available" in full_response.lower() and "not available" not in full_response.lower():
                result.gfast_range_a_available = True
        
        logger.info(f"Parsed results - Exchange: {result.exchange_name}, Cabinet: {result.cabinet_number}")
        logger.info(f"Speeds - Down: {result.vdsl_range_a_downstream_high}/{result.vdsl_range_a_downstream_low}, Up: {result.vdsl_range_a_upstream_high}/{result.vdsl_range_a_upstream_low}")
        
    except Exception as e:
        logger.error(f"Error parsing detailed response: {e}")
        result.error = f"Parsing error: {str(e)}"
    
    return result

def _save_results(result: BroadbandCheckResult, task_id: str):
    """
    Save results to file for retrieval
    """
    filename = f"/tmp/broadband_result_{task_id}.json"
    
    result_dict = result.to_dict()
    with open(filename, "w") as f:
        json.dump(result_dict, f, indent=2)
    
    logger.info(f"Results saved to {filename}")
    
    # Log the extracted data for visibility
    logger.info(f"Extracted data - Address: {result.address_selected or 'Not found'}")
    logger.info(f"Extracted data - Exchange: {result.exchange_name or 'Not found'}")
    logger.info(f"Extracted data - Cabinet: {result.cabinet_number or 'Not found'}")
    if result.error:
        logger.warning(f"Check had error: {result.error}")
    
    # Also save a simplified CSV-friendly version
    csv_filename = f"/tmp/broadband_result_{task_id}.csv"
    with open(csv_filename, "w") as f:
        # Write header
        f.write(",".join(result.to_dict().keys()) + "\n")
        # Write values
        f.write(",".join(str(v) for v in result.to_dict().values()) + "\n")
    
    logger.info(f"CSV results saved to {csv_filename}")

# ============== Configuration Loading ==============

def load_extraction_config(config_path: Optional[str] = None) -> List[ExtractionRule]:
    """
    Load extraction configuration from file
    This allows for easy modification without code changes
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            return [ExtractionRule(**rule) for rule in config['extraction_rules']]
    return EXTRACTION_RULES

# ============== Agent Definitions ==============

@tool
def get_check_results(task_id: str) -> Dict[str, Any]:
    """Get results from a completed broadband check"""
    
    result_file = f"/tmp/broadband_result_{task_id}.json"
    
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            return json.load(f)
    
    return {"status": "pending", "message": "Results not yet available"}

@tool  
def batch_check_addresses(addresses: List[Dict[str, str]], parallel: bool = False) -> List[Dict[str, Any]]:
    """
    Check multiple addresses for broadband availability
    
    Args:
        addresses: List of address dictionaries
        parallel: Whether to run checks in parallel
        
    Returns:
        List of task IDs and statuses
    """
    results = []
    
    for address in addresses:
        result = check_broadband_availability(address, wait_for_completion=not parallel)
        results.append(result)
        
        if not parallel:
            # Add delay between sequential checks to avoid rate limiting
            time.sleep(2)
    
    return results

# ============== Main Agent ==============

broadband_agent = Agent(
    name="broadband_checker",
    system_prompt="""You are a broadband availability checking agent. You extract structured data from the BT Wholesale 
    broadband checker portal for given addresses. You provide accurate information about:
    - VDSL/ADSL line speeds (downstream/upstream)
    - G.fast availability
    - FTTP availability
    - Exchange and cabinet information
    - Service restrictions
    
    Always return structured data that can be easily integrated into spreadsheets or databases.
    Include the recording path for human verification when available.""",
    tools=[check_broadband_availability, get_check_results, batch_check_addresses, file_read, file_write],
    model=nova_pro
)

# ============== Health Check Function ==============

def health_check():
    """
    Health check function for Agent Core runtime
    Returns status and timestamp as required by the runtime contract
    """
    global active_tasks, last_update_time
    
    # Determine status based on active tasks
    status = "HealthyBusy" if active_tasks else "Healthy"
    
    return {
        "status": status,
        "time_of_last_update": int(last_update_time)
    }

# Register the health check endpoint
app.ping = health_check

# ============== Entry Point ==============

@app.entrypoint
def handler(payload):
    """
    Main entrypoint for the broadband checker agent
    
    Expected payload formats:
    1. Single check: {"address": {...}, "extract_fields": [...]}
    2. Batch check: {"addresses": [...], "parallel": true/false}
    3. Get results: {"task_id": "..."}
    4. Test: {"test": true}
    5. Prompt: {"prompt": "..."}
    """
    logger.info(f"Handler invoked with payload: {json.dumps(payload) if isinstance(payload, dict) else str(payload)[:200]}")
    
    try:
        # Handle test request
        if isinstance(payload, dict) and payload.get("test"):
            test_address = AddressInput(
                building_number="13",
                street="ALBION DRIVE", 
                town="HACKNEY, LONDON",
                postcode="E8 4LX"
            )
            result = check_broadband_availability(
                test_address.__dict__,
                wait_for_completion=True,
                max_steps=payload.get("max_steps", 8)  # Allow override, default to 8 for tests
            )
            return result
        
        # Ensure payload is a dictionary
        if not isinstance(payload, dict):
            return {
                "status": "error",
                "message": f"Invalid payload type: {type(payload).__name__}. Expected dict."
            }
        
        # Handle single address check
        if "address" in payload:
            address = payload["address"]
            extract_fields = payload.get("extract_fields")
            wait = payload.get("wait_for_completion", False)
            
            result = check_broadband_availability(address, extract_fields, wait)
            return result
        
        # Handle batch check
        if "addresses" in payload:
            addresses = payload["addresses"]
            parallel = payload.get("parallel", False)
            
            results = batch_check_addresses(addresses, parallel)
            return {"status": "success", "results": results}
        
        # Handle result retrieval
        if "task_id" in payload:
            task_id = payload["task_id"]
            result = get_check_results(task_id)
            return result
        
        # Handle prompt-based interaction
        if "prompt" in payload:
            # Use the agent for natural language interaction
            response = broadband_agent.run(payload["prompt"])
            return {"response": str(response)}
        
        return {
            "status": "error",
            "message": "Invalid payload. Expected 'address', 'addresses', 'task_id', or 'test' key"
        }
        
    except Exception as e:
        # Avoid __traceback__ assignment error
        error_msg = str(e)
        logger.error(f"Handler error: {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

# ============== Local Testing ==============

if __name__ == "__main__":
    # Run the app
    app.run()