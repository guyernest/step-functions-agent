"""Base Nova Act agent implementation for Agent Core."""

import os
import boto3
from dataclasses import dataclass
from typing import Any
from datetime import datetime

from nova_act import NovaAct
from nova_act.util.s3_writer import S3Writer


@dataclass
class AgentConfig:
    """Configuration for Nova Act Agent."""

    headless: bool = True
    ignore_https_errors: bool = True
    step_timeout: int = 60
    max_retries: int = 3
    retry_delay: int = 2
    record_video: bool = True
    recordings_bucket: str | None = None

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create config from environment variables."""
        return cls(
            headless=os.getenv("NOVA_ACT_HEADLESS", "true").lower() == "true",
            ignore_https_errors=os.getenv("NOVA_ACT_IGNORE_HTTPS", "true").lower() == "true",
            step_timeout=int(os.getenv("NOVA_ACT_STEP_TIMEOUT", "60")),
            max_retries=int(os.getenv("NOVA_ACT_MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("NOVA_ACT_RETRY_DELAY", "2")),
            record_video=os.getenv("NOVA_ACT_RECORD_VIDEO", "true").lower() == "true",
            recordings_bucket=os.getenv("NOVA_ACT_RECORDINGS_BUCKET"),
        )


class NovaActAgent:
    """Base class for Nova Act agents."""

    def __init__(self, config: AgentConfig | None = None):
        """Initialize the Nova Act agent.

        Args:
            config: Agent configuration. If None, loads from environment.
        """
        self.config = config or AgentConfig.from_env()
        os.environ["NOVA_ACT_STEP_TIMEOUT"] = str(self.config.step_timeout)
        self.boto_session = boto3.Session() if self.config.recordings_bucket else None

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a web browsing task.

        Args:
            task: Task dictionary containing:
                - url: Starting URL
                - instructions: Instructions for Nova Act
                - extract_data: Optional data extraction requirements

        Returns:
            Result dictionary containing:
                - success: Whether the task completed successfully
                - response: Nova Act response
                - extracted_data: Any extracted data
                - session_id: Nova Act session ID
                - recording_url: S3 URL for session recording
                - error: Error message if failed
        """
        url = task.get("url", "")
        instructions = task.get("instructions", "")
        extract_data = task.get("extract_data")

        if not url or not instructions:
            return {
                "success": False,
                "error": "Missing required fields: url and instructions",
            }

        result = {
            "success": False,
            "response": None,
            "extracted_data": None,
            "session_id": None,
            "recording_url": None,
            "error": None,
        }

        try:
            # Prepare S3Writer for automatic session upload
            stop_hooks = []
            if self.config.recordings_bucket and self.boto_session:
                timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H")
                s3_writer = S3Writer(
                    boto_session=self.boto_session,
                    s3_bucket_name=self.config.recordings_bucket,
                    s3_prefix=f"nova-act-sessions/{timestamp}/",
                    metadata={
                        "url": url,
                        "task_type": "general",
                    }
                )
                stop_hooks.append(s3_writer)

            with NovaAct(
                starting_page=url,
                headless=self.config.headless,
                ignore_https_errors=self.config.ignore_https_errors,
                record_video=self.config.record_video,
                stop_hooks=stop_hooks,
            ) as nova:
                # Execute main instructions
                nova_result = nova.act(instructions)

                result["response"] = nova_result.response
                result["session_id"] = str(nova_result.metadata.session_id)

                # Build S3 URL for session data
                if self.config.recordings_bucket and result["session_id"]:
                    timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H")
                    result["recording_url"] = f"s3://{self.config.recordings_bucket}/nova-act-sessions/{timestamp}/{result['session_id']}/"

                # Extract data if requested
                if extract_data and nova_result.response:
                    extracted = self._extract_data(nova_result.response, extract_data)
                    result["extracted_data"] = extracted

                result["success"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    def _extract_data(self, response: str, extract_config: dict[str, Any]) -> dict[str, Any]:
        """Extract structured data from Nova Act response.

        Args:
            response: Raw response from Nova Act
            extract_config: Configuration for data extraction

        Returns:
            Extracted data dictionary
        """
        # This is a simple implementation that can be extended
        extracted = {}

        if isinstance(extract_config, list):
            # List of fields to extract
            for field in extract_config:
                field_lower = field.lower()
                response_lower = response.lower()

                if field_lower in response_lower:
                    # Simple extraction - can be made more sophisticated
                    lines = response.split("\n")
                    for line in lines:
                        if field_lower in line.lower():
                            # Extract value after the field name
                            parts = line.split(":", 1)
                            if len(parts) > 1:
                                extracted[field] = parts[1].strip()
                                break

        elif isinstance(extract_config, dict):
            # More complex extraction logic
            for _key, _pattern in extract_config.items():
                # Implement pattern-based extraction here
                pass

        return extracted


class ShoppingAgent(NovaActAgent):
    """Specialized agent for apartment/shopping searches using Zumper pattern."""

    def search_apartments(self, search_params: dict[str, Any]) -> dict[str, Any]:
        """Search for apartments on Zumper.

        Args:
            search_params: Dictionary with keys: city, bedrooms, baths, min_results

        Returns:
            Result dictionary with apartment listings
        """
        from pydantic import BaseModel

        class Apartment(BaseModel):
            address: str
            price: str
            beds: str
            baths: str

        class ApartmentList(BaseModel):
            apartments: list[Apartment]

        url = "https://zumper.com/"
        city = search_params.get("city", "Redwood City")
        bedrooms = search_params.get("bedrooms", 2)
        baths = search_params.get("baths", 1)
        min_results = search_params.get("min_results", 5)

        result = {
            "success": False,
            "response": None,
            "apartments": [],
            "session_id": None,
            "recording_url": None,
            "error": None,
        }

        try:
            # Prepare S3Writer for automatic session upload
            stop_hooks = []
            if self.config.recordings_bucket and self.boto_session:
                timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H")
                s3_writer = S3Writer(
                    boto_session=self.boto_session,
                    s3_bucket_name=self.config.recordings_bucket,
                    s3_prefix=f"nova-act-sessions/{timestamp}/",
                    metadata={
                        "city": city,
                        "bedrooms": str(bedrooms),
                        "baths": str(baths),
                    }
                )
                stop_hooks.append(s3_writer)

            with NovaAct(
                starting_page=url,
                headless=self.config.headless,
                ignore_https_errors=self.config.ignore_https_errors,
                record_video=self.config.record_video,
                stop_hooks=stop_hooks,
            ) as nova:
                # Step 1: Search and filter (matching Zumper example)
                nova.act(
                    f"Close any cookie banners. "
                    f"Search for apartments near {city} "
                    f"then filter for {bedrooms} bedrooms and {baths} bathrooms. "
                    "If you see a dialog about saving a search, close it. "
                    "If results mode is 'Split', switch to 'List'. "
                )

                all_apartments = []
                # Step 2: Extract apartments with scrolling
                for _ in range(5):  # Scroll down a max of 5 times
                    apartment_result = nova.act(
                        "Return the currently visible list of apartments",
                        schema=ApartmentList.model_json_schema()
                    )

                    if apartment_result.matches_schema:
                        apartment_list = ApartmentList.model_validate(apartment_result.parsed_response)
                        all_apartments.extend(apartment_list.apartments)

                        if len(all_apartments) >= min_results:
                            break
                        nova.act("Scroll down once")
                    else:
                        break

                result["apartments"] = [apt.model_dump() for apt in all_apartments]
                result["response"] = f"Found {len(all_apartments)} apartments"
                result["session_id"] = str(apartment_result.metadata.session_id)
                result["success"] = True

                # Build S3 URL for session data
                if self.config.recordings_bucket and result["session_id"]:
                    timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H")
                    result["recording_url"] = f"s3://{self.config.recordings_bucket}/nova-act-sessions/{timestamp}/{result['session_id']}/"

        except Exception as e:
            result["error"] = str(e)

        return result


class BroadbandCheckerAgent(NovaActAgent):
    """Specialized agent for BT Broadband Checker."""

    def check_broadband(self, address: dict[str, str]) -> dict[str, Any]:
        """Check broadband availability for an address.

        Args:
            address: Dictionary with keys: building_number, street, town, postcode

        Returns:
            Result dictionary with broadband information
        """
        url = "https://www.broadbandchecker.btwholesale.com/#/ADSL/AddressHome"

        result = {
            "success": False,
            "response": None,
            "extracted_data": None,
            "session_id": None,
            "recording_url": None,
            "error": None,
        }

        try:
            # Prepare S3Writer for automatic session upload
            stop_hooks = []
            if self.config.recordings_bucket and self.boto_session:
                timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H")
                s3_writer = S3Writer(
                    boto_session=self.boto_session,
                    s3_bucket_name=self.config.recordings_bucket,
                    s3_prefix=f"nova-act-sessions/{timestamp}/",
                    metadata={
                        "address": f"{address.get('building_number')} {address.get('street')}",
                        "postcode": address.get('postcode', ''),
                    }
                )
                stop_hooks.append(s3_writer)

            # Use multiple Nova Act calls within same browser session (like working test)
            # Note: Nova Act uses API key from environment (NOVA_ACT_API_KEY)
            # boto_session is only used by S3Writer, not passed to NovaAct
            with NovaAct(
                starting_page=url,
                headless=self.config.headless,
                ignore_https_errors=self.config.ignore_https_errors,
                record_video=self.config.record_video,
                stop_hooks=stop_hooks,
            ) as nova:
                # Step 1: Fill in the form and click Submit (matching working test exactly)
                building_number = address['building_number']
                street = address['street']
                town = address['town']
                postcode = address['postcode']

                form_prompt = f"""
        Fill in the address form with these details:
        - Building Number field: {building_number}
        - Street/Road field: {street}
        - Town field: {town}
        - PostCode field: {postcode}

        Then click the Submit button.
        """
                nova.act(form_prompt)

                # Step 2: Handle address selection if list appears (matching working test)
                full_address = f"{building_number}, {street}, {town}, {postcode}"
                nova.act(f"If an address list appears, select the closest match to: {full_address}")

                # Step 3: Extract broadband information (matching working test format)
                extraction_prompt = """Extract the broadband availability information from the results page.
            Look for:
            - The selected address
            - Exchange name (e.g., "KINGSLAND GREEN")
            - Cabinet number (e.g., "Cabinet 9")
            - VDSL Range A downstream and upstream rates
            - Availability status
            """
                nova_result = nova.act(extraction_prompt)

                result["response"] = nova_result.response
                result["session_id"] = str(nova_result.metadata.session_id)
                result["success"] = True

                # Build S3 URL for session data
                if self.config.recordings_bucket and result["session_id"]:
                    timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H")
                    result["recording_url"] = f"s3://{self.config.recordings_bucket}/nova-act-sessions/{timestamp}/{result['session_id']}/"

                # Post-process for broadband-specific data
                if result["response"]:
                    result["broadband_info"] = self._parse_broadband_info(result["response"])

        except Exception as e:
            result["error"] = str(e)

        return result

    def _parse_broadband_info(self, response: str) -> dict[str, Any]:
        """Parse broadband-specific information from response."""
        info = {
            "exchange": None,
            "cabinet": None,
            "max_speed": None,
            "technologies": [],
            "available": False,
        }

        response_lower = response.lower()

        # Extract exchange
        if "exchange" in response_lower:
            lines = response.split("\n")
            for line in lines:
                if "exchange" in line.lower():
                    parts = line.split("exchange", 1)
                    if len(parts) > 1:
                        exchange_text = parts[1].strip(":").strip()
                        if exchange_text:
                            info["exchange"] = exchange_text.split()[0]
                            break

        # Extract cabinet
        if "cabinet" in response_lower:
            import re

            numbers = re.findall(r"cabinet\s*(\d+)", response_lower)
            if numbers:
                info["cabinet"] = f"Cabinet {numbers[0]}"

        # Check technologies
        for tech in ["VDSL", "FTTC", "FTTP", "ADSL"]:
            if tech.lower() in response_lower:
                info["technologies"].append(tech)

        # Check availability
        if "available" in response_lower:
            info["available"] = "not available" not in response_lower

        # Extract speeds
        import re

        speed_matches = re.findall(r"up to (\d+(?:\.\d+)?)\s*[Mm]bps", response)
        if speed_matches:
            speeds = [float(s) for s in speed_matches]
            info["max_speed"] = max(speeds)

        return info


class AuthenticatedBroadbandCheckerAgent(NovaActAgent):
    """BT Broadband Checker with authentication for internal portal access."""

    def check_broadband(self, address: dict[str, str], credentials: dict[str, str] | None = None) -> dict[str, Any]:
        """Check broadband availability for an address using authenticated portal.

        Args:
            address: Dictionary with keys: building_number, street, town, postcode
            credentials: Dictionary with keys: username, password

        Returns:
            Result dictionary with broadband information
        """
        # Start at BT Wholesale homepage for login
        url = "https://www.btwholesale.com/"

        # Extract credentials or use defaults
        username = credentials.get("username", "username") if credentials else "user"
        password = credentials.get("password", "password") if credentials else "password"

        result = {
            "success": False,
            "response": None,
            "extracted_data": None,
            "session_id": None,
            "recording_url": None,
            "error": None,
        }

        try:
            # Prepare S3Writer for automatic session upload
            stop_hooks = []
            if self.config.recordings_bucket and self.boto_session:
                timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H")
                s3_writer = S3Writer(
                    boto_session=self.boto_session,
                    s3_bucket_name=self.config.recordings_bucket,
                    s3_prefix=f"nova-act-sessions/{timestamp}/",
                    metadata={
                        "address": f"{address.get('building_number')} {address.get('street')}",
                        "postcode": address.get('postcode', ''),
                        "authenticated": "true",
                    }
                )
                stop_hooks.append(s3_writer)

            # Enhanced anti-bot detection measures
            # Use realistic Firefox user agent string for Windows 10
            firefox_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"

            with NovaAct(
                starting_page=url,
                headless=self.config.headless,
                ignore_https_errors=self.config.ignore_https_errors,
                record_video=self.config.record_video,
                stop_hooks=stop_hooks,
                user_agent=firefox_user_agent,
                screen_width=1920,  # Standard Full HD width (within NovaAct's required range)
                screen_height=1080,  # Standard Full HD height (within NovaAct's required range)
            ) as nova:
                # Step 1: Accept cookies
                nova.act("Close the cookies banner by accepting all cookies")

                # Step 2: Login to My BT Wholesale
                login_prompt = f"""
                Click the login button in the top right and select "My BT Wholesale".
                Fill in the login form:
                - Username: {username}
                - Password: {password}
                - If you see checkbox (I'm not a robot), check it.
                Then click the submit/login button.
                """
                nova.act(login_prompt)

                # Step 3: Navigate to Enhanced Broadband Availability Checker
                check_app_navigation_prompt = f"""
                Wait for login to complete.
                Select 'My Apps' tab, wait for page to load.
                Find 'Enhanced Broadband Availability Checker' and click 'Open app', wait for page to load.
                Select 'Address Checker' tab
                """

                nova.act(check_app_navigation_prompt)

                # Step 4: Fill in address form and submit
                building_number = address.get('building_number', '')
                street = address.get('street', '')
                town = address.get('town', '')
                postcode = address.get('postcode', '')

                form_prompt = f"""
                Fill in the address form with these details:
                - Building Number field: {building_number}
                - Street/Road field: {street}
                - Town field: {town}
                - PostCode field: {postcode}

                Then click the Submit button.
                """
                nova.act(form_prompt)

                # Step 5: Handle address selection if list appears
                full_address = f"{building_number}, {street}, {town}, {postcode}"
                nova.act(f"If an address list appears, select the closest match to: {full_address}")

                # Step 6: Extract broadband information
                extraction_prompt = """Extract the broadband availability information from the results page.
                Look for:
                - Exchange name and code
                - Cabinet number
                - VDSL Range A downstream and upstream rates
                - FTTC/FTTP availability
                - Any service restrictions or notes
                """
                nova_result = nova.act(extraction_prompt)

                result["response"] = nova_result.response
                result["session_id"] = str(nova_result.metadata.session_id)
                result["success"] = True

                # Build S3 URL for session data
                if self.config.recordings_bucket and result["session_id"]:
                    timestamp = datetime.utcnow().strftime("%Y/%m/%d/%H")
                    result["recording_url"] = f"s3://{self.config.recordings_bucket}/nova-act-sessions/{timestamp}/{result['session_id']}/"

                # Post-process for broadband-specific data
                if result["response"]:
                    result["broadband_info"] = self._parse_broadband_info(result["response"])

        except Exception as e:
            result["error"] = str(e)

        return result

    def _parse_broadband_info(self, response: str) -> dict[str, Any]:
        """Parse broadband-specific information from response."""
        info = {
            "exchange": None,
            "cabinet": None,
            "max_speed": None,
            "technologies": [],
            "available": False,
        }

        response_lower = response.lower()

        # Extract exchange
        if "exchange" in response_lower:
            lines = response.split("\n")
            for line in lines:
                if "exchange" in line.lower():
                    parts = line.split("exchange", 1)
                    if len(parts) > 1:
                        exchange_text = parts[1].strip(":").strip()
                        if exchange_text:
                            info["exchange"] = exchange_text.split()[0]
                            break

        # Extract cabinet
        if "cabinet" in response_lower:
            import re
            numbers = re.findall(r"cabinet\s*(\d+)", response_lower)
            if numbers:
                info["cabinet"] = f"Cabinet {numbers[0]}"

        # Check technologies
        for tech in ["VDSL", "FTTC", "FTTP", "ADSL"]:
            if tech.lower() in response_lower:
                info["technologies"].append(tech)

        # Check availability
        if "available" in response_lower:
            info["available"] = "not available" not in response_lower

        # Extract speeds
        import re
        speed_matches = re.findall(r"up to (\d+(?:\.\d+)?)\s*[Mm]bps", response)
        if speed_matches:
            speeds = [float(s) for s in speed_matches]
            info["max_speed"] = max(speeds)

        return info
