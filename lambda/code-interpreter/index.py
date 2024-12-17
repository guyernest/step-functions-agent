import json
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from e2b_code_interpreter import Sandbox

# Initialize Powertools
logger = Logger()

try:
    E2B_API_KEY = json.loads(parameters.get_secret("/ai-agent/e2b-api-key"))["/ai-agent/e2b-api-key"]
except ValueError:
    E2B_API_KEY = parameters.get_secret("/ai-agent/e2b-api-key")


def code_interpret(code):
    logger.info("Starting code interpretation")
        
    with Sandbox(api_key=E2B_API_KEY) as code_interpreter:
        exec = code_interpreter.run_code(code,
            on_stderr=lambda stderr: logger.warning(f"[Code Interpreter] {stderr}"),
            on_stdout=lambda stdout: logger.info(f"[Code Interpreter] {stdout}"))

        if exec.error:
            logger.error(f"[Code Interpreter ERROR] {exec.error}")
            raise Exception(exec.error)
        else:
            return exec.results    

def lambda_handler(event, context):
    try:
        # Extract the Python code from the event
        code = event.get('code')
        if not code:
            logger.error("No code provided in the event")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No code provided in the event'
                })
            }
                
        # Execute the code
        result = code_interpret(code)
        logger.info("Code execution successful", extra={"result": result})
        
        # Return the execution results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'text': result[0].text,
                'png': result[0].png
            })
        }
        
    except Exception as e:
        logger.exception("Error executing code")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

if __name__ == "__main__":
    # Test event with a simple Python code
    test_event = {
        "code": "print('Hello, World!')\nx = 5 + 3\nprint(f'Result: {x}')\nx"
    }
    
    # Call the lambda handler with the test event and None as context
    result = lambda_handler(test_event, None)
    
    # Print the result
    print("Lambda Response:")
    print(f"Status Code: {result['statusCode']}")
    print("Body:")
    print(json.dumps(json.loads(result['body']), indent=2))