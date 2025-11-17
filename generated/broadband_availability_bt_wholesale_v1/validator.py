"""
Validator for broadband_availability_bt_wholesale schema
Auto-generated from canonical schema version 1.0.0
"""

from jsonschema import validate, ValidationError
from typing import Dict, Any
import json


class broadband_availability_bt_wholesaleValidator:
    """Validator for broadband_availability_bt_wholesale inputs and outputs"""

    INPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "building_number": {
                "type": "",
                "description": "Building number (e.g., &#x27;1&#x27;, &#x27;23A&#x27;)"
            },
            "full_address": {
                "type": "",
                "description": "Full address for disambiguation when multiple matches exist"
            },
            "postcode": {
                "type": "",
                "description": "UK postcode in format like SW1A 1AA",
                "pattern": "^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$"
            },
            "street": {
                "type": "",
                "description": "Street or road name (e.g., &#x27;High Street&#x27;, &#x27;Park Road&#x27;)"
            }
        },
        "required": ["postcode", "building_number", "street"]
    }

    OUTPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "availability": {
                "type": "",
                "description": "Whether broadband service is available"
            },
            "cabinet": {
                "type": "",
                "description": "Street cabinet number"
            },
            "downstream_mbps": {
                "type": "",
                "description": "Maximum download speed in Mbps"
            },
            "exchange": {
                "type": "",
                "description": "BT exchange station name"
            },
            "metadata": {
                "type": "",
                "description": "Additional metadata from the extraction"
            },
            "screenshot_url": {
                "type": "",
                "description": "URL of browser recording or screenshot"
            },
            "service_type": {
                "type": "",
                "description": "Type of broadband service available"
            },
            "success": {
                "type": "",
                "description": "Whether the broadband availability check succeeded"
            },
            "upstream_mbps": {
                "type": "",
                "description": "Maximum upload speed in Mbps"
            }
        },
        "required": ["success"]
    }

    @classmethod
    def validate_input(cls, data: Dict[str, Any]) -> bool:
        """Validate input data against schema"""
        try:
            validate(instance=data, schema=cls.INPUT_SCHEMA)
            return True
        except ValidationError as e:
            print(f"Input validation error: {e.message}")
            return False

    @classmethod
    def validate_output(cls, data: Dict[str, Any]) -> bool:
        """Validate output data against schema"""
        try:
            validate(instance=data, schema=cls.OUTPUT_SCHEMA)
            return True
        except ValidationError as e:
            print(f"Output validation error: {e.message}")
            return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python validator.py --input <input.json> --output <output.json>")
        sys.exit(1)

    # Simple CLI for testing
    if "--input" in sys.argv:
        idx = sys.argv.index("--input")
        with open(sys.argv[idx + 1]) as f:
            input_data = json.load(f)
        if broadband_availability_bt_wholesaleValidator.validate_input(input_data):
            print("✓ Input validation passed")
        else:
            print("✗ Input validation failed")
            sys.exit(1)

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        with open(sys.argv[idx + 1]) as f:
            output_data = json.load(f)
        if broadband_availability_bt_wholesaleValidator.validate_output(output_data):
            print("✓ Output validation passed")
        else:
            print("✗ Output validation failed")
            sys.exit(1)
