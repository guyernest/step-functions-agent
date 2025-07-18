import json
import boto3
import uuid
import os
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from e2b_code_interpreter import Sandbox

# Initialize Powertools
logger = Logger()

try:
    # Use the new tool-specific secret path
    E2B_API_KEY = json.loads(parameters.get_secret("/ai-agent/tools/execute-code/prod"))["E2B_API_KEY"]
except ValueError:
    raise ValueError("E2B API keys not found in Secrets Manager")

IMAGE_BUCKET_NAME = os.environ.get('IMAGE_BUCKET_NAME', 'mlguy-mlops-courses')

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
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use.get('name')
    tool_input = tool_use.get('input')

    try:
        match tool_name:
            case "execute_python":
                code = tool_input.get('code')
                if not code:
                    logger.error("No code provided in the event")
                    return {
                        "type": "tool_result",
                        "name": tool_name,
                        "tool_use_id": tool_use["id"],
                        "content": json.dumps({
                            'error': 'No code provided.'
                        })
                    }
                
                # Execute the code
                result = code_interpret(code)
                logger.info("Code execution successful", extra={"result": result})
                
                png_result = None
                has_png = any(r.png is not None for r in result)

                if result and not has_png:
                    return {
                        "type": "tool_result",
                        "name": tool_name,
                        "tool_use_id": tool_use["id"],
                        "content": result[0].text
                    }
                elif result and has_png:
                    # Find the first result with PNG content
                    png_result = next(r for r in result if r.png is not None)

                # To avoid the max token limit of moving large base64 images, we can create write the image to S3
                # and return the S3 URL. We also need to generate a presigned URL for the S3 object.
                # We can use the S3 SDK to generate the presigned URL.
                s3 = boto3.client('s3')
                uuid_str = str(uuid.uuid4())
                object_name = f'images/code_interpreter_{uuid_str}.html'
                html_content = f"""
                <html>
                <head>
                </head>
                <body>
                    <img src="data:image/png;base64,{png_result.png}" />
                </body>
                </html>
                """

                s3.put_object(
                    Body=html_content, 
                    Bucket=IMAGE_BUCKET_NAME, 
                    Key=object_name, 
                    ContentType='text/html'
                )

                # We can use the S3 SDK to generate the presigned URL.
                result = s3.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': IMAGE_BUCKET_NAME,
                        'Key': object_name
                    },
                    ExpiresIn=3600
                )
            case _:  # Default case
                logger.error(f"Unknown tool name: {tool_name}")
                result = json.dumps({
                    'error': f"Unknown tool name: {tool_name}"
                })

        # Return the execution results
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        }
        
    except Exception as e:
        logger.exception("Error executing code")
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": str(e)
        }

if __name__ == "__main__":
    # Test event with a simple Python code
    test_event = {
        "name": "execute_python",
        "id": "code_interpreter_unique_id",
        "input": {
            "code": "print('Hello, World!')\nx = 5 + 3\nprint(f'Result: {x}')\nx"
        }
    }
    
    # Call the lambda handler with the test event and None as context
    result = lambda_handler(test_event, None)
    
    # Print the result
    print("Lambda Response:")
    print(result)

    chart_code = """
import pandas as pd
import matplotlib.pyplot as plt

# Create the data
data = {
    'State': ['CA', 'TX', 'FL', 'IL', 'GA', 'NY', 'OH', 'PA', 'AL', 'NJ'],
    '1970s': [334, 106, 101, 79, 47, 71, 57, 51, 34, 32],
    '1980s': [334, 169, 148, 55, 61, 35, 48, 37, 30, 30]
}

df = pd.DataFrame(data)

# Create the bar chart
plt.figure(figsize=(12, 6))
x = range(len(df['State']))
width = 0.35

plt.bar([i - width/2 for i in x], df['1970s'], width, label='1970s', color='skyblue')
plt.bar([i + width/2 for i in x], df['1980s'], width, label='1980s', color='lightcoral')

plt.xlabel('State')
plt.ylabel('Number of Players')
plt.title('Top 10 States Where Baseball Players Were Born: 1970s vs 1980s')
plt.xticks(x, df['State'])
plt.legend()

# Add value labels on top of each bar
for i in x:
    plt.text(i - width/2, df['1970s'][i], str(df['1970s'][i]),
             ha='center', va='bottom')
    plt.text(i + width/2, df['1980s'][i], str(df['1980s'][i]),
             ha='center', va='bottom')

plt.tight_layout()
plt.show()
    """   

    # Call the lambda handler with the test event and None as context
    result = lambda_handler(
        {
            "name": "execute_python", 
            "id": "code_interpreter_unique_id", 
            "input": {"code": chart_code}
        }, 
        None
    )

    # Print the result
    print("Lambda Response:")
    print(result)

    multiple_results_chart_code = """
import matplotlib.pyplot as plt
import pandas as pd

# Create data for visualization
birth_years = [1985, 1985, 1985, 1986, 1986, 1987, 1987, 1987, 1988, 1988, 1988, 
               1989, 1989, 1989, 1990, 1990, 1991, 1991, 1993, 1993]

# Create a histogram
plt.figure(figsize=(10, 6))
plt.hist(birth_years, bins=range(1985, 1997, 1), edgecolor='black', color='skyblue')
plt.title('Distribution of Washington-Born Players (1985-1995)')
plt.xlabel('Birth Year')
plt.ylabel('Number of Players')
plt.grid(True, alpha=0.3)
plt.xticks(range(1985, 1996))

# Add value labels on top of each bar
counts, bins, _ = plt.hist(birth_years, bins=range(1985, 1997, 1), edgecolor='black', color='skyblue')
plt.clf()  # Clear the figure

plt.figure(figsize=(10, 6))
plt.hist(birth_years, bins=range(1985, 1997, 1), edgecolor='black', color='skyblue')
for i in range(len(counts)):
    if counts[i] > 0:
        plt.text(bins[i] + 0.5, counts[i], int(counts[i]), ha='center', va='bottom')

plt.title('Distribution of Washington-Born Players (1985-1995)')
plt.xlabel('Birth Year')
plt.ylabel('Number of Players')
plt.grid(True, alpha=0.3)
plt.xticks(range(1985, 1996))
plt.show()
"""   

    # Call the lambda handler with the test event and None as context
    result = lambda_handler(
        {
            "name": "execute_python", 
            "id": "code_interpreter_unique_id", 
            "input": {"code": multiple_results_chart_code}
        }, 
        None
    )

    # Print the result
    print("Lambda Response:")
    print(result)