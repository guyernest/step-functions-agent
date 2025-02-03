import boto3
import json
from datetime import datetime, timedelta
import time

QUERY_GENERATION_PROMPT = """
Generate a CloudWatch Logs Insights query based on the following guidelines and examples.

The logs are generated using AWS Lambda Powertools Logger with the following standard fields:
- @timestamp: The timestamp of the log entry
- @message: The main log message
- level: The log level (INFO, ERROR, WARNING, etc.)
- service: The service name
- functionName: The Lambda function name
- cold_start: Boolean indicating if this was a cold start
- sampling_rate: Sampling rate if used
- exception_details: Details of exceptions when errors occur
- xray_trace_id: X-Ray trace ID for request tracing

Common Query Patterns:

1. Basic Error Detection:
    fields @timestamp, @message, exception_details | 
    filter level = 'ERROR' | 
    sort @timestamp desc | 
    limit 100
2. Cold Start Analysis:
    fields @timestamp, @message, functionName, duration | 
    filter cold_start = true | 
    stats count(*) as cold_starts by functionName | 
    sort cold_starts desc
3. Service Performance:
    fields @timestamp, @message, service, duration | 
    stats avg(duration) as avg_duration, max(duration) as max_duration, min(duration) as min_duration by service | 
    sort avg_duration desc
4. Error Pattern Analysis:
    fields @timestamp, @message, exception_details | 
    filter level = 'ERROR' | 
    stats count(*) as error_count by exception_details | 
    sort error_count desc | 
    limit 10
5. Request Tracing:
    fields @timestamp, @message, xray_trace_id | 
    filter service = 'payment-service' and level = 'ERROR' | 
    sort @timestamp desc

Query Syntax Guidelines:
1. Use 'fields' to specify which fields to include in results
2. Use 'filter' for conditions (equivalent to WHERE in SQL)
3. Use 'stats' for aggregations
4. Use 'sort' to order results
5. Use 'limit' to restrict number of results
6. Use 'parse' to extract fields from @message if needed

Common Operations:
- Finding errors: filter level = 'ERROR'
- Time-based filtering: filter @timestamp > timestamp
- Pattern matching: filter @message like /pattern/
- Numeric comparisons: filter duration > 1000
- Multiple conditions: filter condition1 and condition2
- Group by: stats count(*) by fieldName
- Time buckets: bin(30s) as time_bucket

When crafting queries:
1. Start with essential fields using 'fields'
2. Apply filters to narrow down the data
3. Use stats if aggregation is needed
4. Always sort results
5. Consider adding a reasonable limit
6. Focus on specific service/function names when possible
7. Use 'parse' if needed to extract more details from @message
"""

class CloudWatchInterface:
    def __init__(self):
        self.logs_client = boto3.client('logs')

    def find_log_groups_by_tag(self, tag_name: str, tag_value: str) -> list:
        """Find CloudWatch log groups that have a specific tag."""
        log_groups = []
        paginator = self.logs_client.get_paginator('describe_log_groups')
        
        try:
            for page in paginator.paginate():
                for log_group in page['logGroups']:
                    # Get tags for each log group
                    response = self.logs_client.list_tags_log_group(
                        logGroupName=log_group['logGroupName']
                    )
                    
                    # Check if the specified tag exists with the correct value
                    tags = response.get('tags', {})
                    if tags.get(tag_name) == tag_value:
                        log_groups.append(log_group['logGroupName'])
                        
            return log_groups
        except Exception as e:
            return {
                'error': f"Failed to find log groups: {str(e)}"
            }

    def execute_query(self, log_groups: list, query: str, time_range: str) -> dict:
        """Execute a CloudWatch Insights query on specified log groups."""
        try:
            # Calculate start and end times based on the time range
            end_time = int(time.time() * 1000)  # Current time in milliseconds
            
            # Parse time range
            time_mapping = {
                'last_hour': timedelta(hours=1),
                'last_day': timedelta(days=1),
                'last_week': timedelta(weeks=1),
                'last_month': timedelta(days=30)
            }
            
            if time_range not in time_mapping:
                return {
                    'error': f"Invalid time range. Supported values: {', '.join(time_mapping.keys())}"
                }
                
            start_time = int((datetime.now() - time_mapping[time_range]).timestamp() * 1000)
            
            # Start the query execution
            response = self.logs_client.start_query(
                logGroupNames=log_groups,
                startTime=start_time,
                endTime=end_time,
                queryString=query
            )
            
            query_id = response['queryId']
            
            # Wait for query to complete
            while True:
                response = self.logs_client.get_query_results(queryId=query_id)
                status = response['status']
                
                if status in ['Complete', 'Failed', 'Cancelled']:
                    break
                    
                time.sleep(1)
            
            if status == 'Failed':
                return {
                    'error': 'Query execution failed'
                }
            elif status == 'Cancelled':
                return {
                    'error': 'Query was cancelled'
                }
                
            # Process and format results
            results = []
            for result in response['results']:
                result_dict = {}
                for field in result:
                    result_dict[field['field']] = field['value']
                results.append(result_dict)
                
            return results
            
        except Exception as e:
            return {
                'error': f"Failed to execute query: {str(e)}"
            }

    def get_query_generation_prompt(self) -> str:
        """Returns the prompt for generating CloudWatch Logs Insights queries."""
        return QUERY_GENERATION_PROMPT

def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use['name']
    tool_input = tool_use['input']
    
    cloudwatch = CloudWatchInterface()
    
    match tool_name:
        case 'find_log_groups_by_tag':
            if 'tag_name' not in tool_input or 'tag_value' not in tool_input:
                result = json.dumps({
                    'error': 'Missing required parameters: tag_name and tag_value'
                })
            else:
                result = json.dumps(
                    cloudwatch.find_log_groups_by_tag(
                        tool_input['tag_name'],
                        tool_input['tag_value']
                    )
                )
                
        case 'execute_query':
            required_params = ['log_groups', 'query', 'time_range']
            if not all(param in tool_input for param in required_params):
                result = json.dumps({
                    'error': f"Missing required parameters: {', '.join(required_params)}"
                })
            else:
                result = json.dumps(
                    cloudwatch.execute_query(
                        tool_input['log_groups'],
                        tool_input['query'],
                        tool_input['time_range']
                    )
                )
                
        case 'get_query_generation_prompt':
            result = json.dumps({
                'prompt': cloudwatch.get_query_generation_prompt()
            })
 
        case _:
            result = json.dumps({
                'error': f"Unknown tool name: {tool_name}"
            })
            
    return {
        "type": "tool_result",
        "name": tool_name,
        "tool_use_id": tool_use["id"],
        "content": result
    }

if __name__ == "__main__":
    # Test event for find_log_groups_by_tag
    test_event_find_logs = {
        "name": "find_log_groups_by_tag",
        "id": "find_logs_unique_id",
        "input": {
            "tag_name": "application",
            "tag_value": "ai-agents"
        },
        "type": "tool_use"
    }

    # Call lambda handler with test events
    # print("\nTesting find_log_groups_by_tag:")
    # response_find_logs = lambda_handler(test_event_find_logs, None)
    # print(response_find_logs)
    
        # Test event for execute_query
    test_event_execute_query = {
        "name": "execute_query",
        "id": "execute_query_unique_id",
        "input": {
            "log_groups": ["/aws/lambda/CallClaudeLLM"],
            "query": "fields @timestamp, @message | sort @timestamp desc | limit 20",
            "time_range": "last_hour"
        },
        "type": "tool_use"
    }

    print("\nTesting execute_query:")
    response_execute_query = lambda_handler(test_event_execute_query, None)
    print(response_execute_query)

    # Test event for get_query_generation_prompt
    test_event_get_prompt = {
        "name": "get_query_generation_prompt",
        "id": "get_prompt_unique_id",
        "type": "tool_use",
        "input": {}
    }

    print("\nTesting get_query_generation_prompt:")
    response_get_prompt = lambda_handler(test_event_get_prompt, None)
    print(response_get_prompt)