# Lambda function to get data from yfinance as a tool for the AI agent
import json
import yfinance as yf
import pandas as pd
from aws_lambda_powertools import Logger

logger = Logger()
logger.setLevel("INFO")

# First, let's flatten the columns if they are multi-level
def prepare_yf_data(df):
    # If we have multi-level columns, flatten them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col 
                     for col in df.columns]
    
    # Reset index to make the date a column
    df = df.reset_index()
    
    # Convert datetime to string format
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    # Convert to records format
    return json.dumps(df.to_dict(orient='records'))

def get_ticker_data(ticker, start_date, end_date):
    logger.info(f"Getting data for {ticker} from {start_date} to {end_date}")
    data = yf.download(ticker, start=start_date, end=end_date)
    return prepare_yf_data(data)

def lambda_handler(event, context):    
    logger.info(f"Received event: {event}")
    # Get the tool name from the input event
    tool_use = event

    try:
        if tool_use["name"] == "get_ticker_data":
            # Extract the ticker and date range from the event
            ticker = tool_use.get('input').get('ticker')
            start_date = tool_use.get('input').get('start_date')
            end_date = tool_use.get('input').get('end_date')
            if not ticker or not start_date or not end_date:
                logger.error("No ticker, start_date, or end_date provided in the event")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'No ticker, start_date, or end_date provided in the event'
                    })
                }
                    
            # Execute the code
            result = get_ticker_data(ticker, start_date, end_date)
            logger.info("ticket data successful", extra={"result": result})
        else:
            logger.error(f"Unknown tool name: {tool_use['name']}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f"Unknown tool name: {tool_use['name']}"
                })
            }
        
        return {
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            "content": result
        }
    except Exception as e:
        logger.error(f"Error getting data for {ticker} from {start_date} to {end_date}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Error getting data for {ticker} from {start_date} to {end_date}: {e}"
            })
        }   

# Testing locally lambda function
if __name__ == "__main__":
    respose = lambda_handler({
        "name": "get_ticket_data",
        "id": "get_ticket_data_unique_id",
        "input": {
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "end_date": "2022-12-31"
        },
        "type": "tool_use"
    }, None)

    print(respose)