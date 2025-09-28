"""
Structured output configuration for the broadband checker agent.
Simple, flat schema for broadband availability data.
"""

BROADBAND_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "exchange_station": {
            "type": "string",
            "description": "The name or identifier of the telephone exchange serving this address"
        },
        "download_speed": {
            "type": "number",
            "description": "Maximum download speed available in Mbps"
        },
        "upload_speed": {
            "type": "number",
            "description": "Maximum upload speed available in Mbps"
        },
        "screenshot_url": {
            "type": "string",
            "description": "Presigned URL of the last page screenshot showing broadband availability",
            "format": "uri"
        }
    },
    "required": ["exchange_station", "download_speed", "upload_speed"],
    "additionalProperties": False
}

STRUCTURED_OUTPUT_CONFIG = {
    "enabled": True,
    "enforced": True,
    "toolName": "return_broadband_data",
    "schemas": {
        "broadband_check": {
            "schema": BROADBAND_OUTPUT_SCHEMA,
            "description": """Extract broadband availability information from the conversation.
            Focus on finding the telephone exchange station name, maximum speeds available,
            and the URL of any screenshot that shows the broadband checker results page.""",
            "examples": [
                {
                    "exchange_station": "Kensington Exchange",
                    "download_speed": 67.0,
                    "upload_speed": 20.0,
                    "screenshot_url": "https://s3.amazonaws.com/bucket/screenshots/abc123.png"
                }
            ]
        },
        "error": {
            "schema": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["error"]
            },
            "description": "Use when unable to retrieve broadband information"
        }
    },
    "defaultSchema": "broadband_check"
}