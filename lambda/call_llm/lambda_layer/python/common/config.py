import json
from aws_lambda_powertools.utilities import parameters

def get_api_keys():
    try:
        keys = json.loads(parameters.get_secret("/ai-agent/api-keys"))
        return keys
    except ValueError:
        raise ValueError("API keys not found in Secrets Manager")