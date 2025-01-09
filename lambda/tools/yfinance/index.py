# Lambda function to get data from yfinance as a tool for the AI agent
import json
import yfinance as yf
import pandas as pd
from aws_lambda_powertools import Logger
import pandas as pd
import boto3
import os
from datetime import datetime, timedelta


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

def get_ticker_data(ticker: str, start_date: str, end_date: str) -> str:
    """
    Get the data for a given ticker symbol from the start date to the end date.

    Args:
        ticker (str): The ticker symbol to get the data for.
        start_date (str): The start date to get the data from. Format: '2022-01-01'
        end_date (str): The end date to get the data up to. Format: '2022-01-01'

    Returns:
        str: The data as a JSON object.
    """
    logger.info(f"Getting data for {ticker} from {start_date} to {end_date}")
    data = yf.download(ticker, start=start_date, end=end_date)
    return prepare_yf_data(data)

def get_ticker_recent_history(ticker, period: str='1mo', interval: str='1d') -> str:
    """
    Get the recent history for a given ticker symbol over a given period and interval.

    Args:
        ticker (str): The ticker symbol to get the data for.
        period (str, optional): The period to get the data for. Defaults to '1mo'. Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max Either Use period parameter or use start and end date.
        interval (str, optional): The interval to get the data for. Defaults to '1d'. Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo Intraday data cannot extend last 60 days.

    Returns:
        str: The recent history as a JSON object.
    """
    logger.info(f"Getting recent history for {ticker} for {period}")
    data = yf.Ticker(ticker).history(period=period, interval=interval)
    return prepare_yf_data(data)

def list_industries(sector_key: str) -> str:
    """
    List the industries for a given sector key. The sector key can be one of the following:

    - 'real-estate'
    - 'healthcare'
    - 'financial-services'
    - 'technology'
    - 'consumer-cyclical'
    - 'consumer-defensive'
    - 'basic-materials'
    - 'industrials'
    - 'energy'
    - 'utilities'
    - 'communication-services'

    :param sector_key: the sector key
    :return: a string containing the list of industries
    """
    logger.info(f"Listing industries for sector: {sector_key}")
    # get the list of industries from Yahoo Finance
    industries_dataframe = yf.Sector(sector_key).industries
    industries = industries_dataframe.to_dict()
    return json.dumps(industries)

def top_sector_companies(sector_key: str) -> str:
    """
    Get the top companies for a given sector key.

    The sector key can be one of the following:

    - 'real-estate'
    - 'healthcare'
    - 'financial-services'
    - 'technology'
    - 'consumer-cyclical'
    - 'consumer-defensive'
    - 'basic-materials'
    - 'industrials'
    - 'energy'
    - 'utilities'
    - 'communication-services'

    :param sector_key: the sector key
    :return: a string containing the list of companies
    """
    logger.info(f"Getting top companies for sector: {sector_key}")
    # get the top companies from Yahoo Finance
    companies_dataframe = yf.Sector(sector_key).top_companies
    companies = companies_dataframe.to_dict()
    return json.dumps(companies)


def top_industry_companies(industry_key: str) -> str:
    """
    Get the top companies for a given industry key.

    :param industry_key: the industry key
    :return: a string containing the list of companies
    """
    logger.info(f"Getting top companies for industry: {industry_key}")
    # get the top companies from Yahoo Finance
    companies_dataframe = yf.Industry(industry_key).top_companies
    companies = companies_dataframe.to_dict()
    return json.dumps(companies)

DATA_BUCKET_NAME = os.environ.get('DATA_BUCKET_NAME', 'mlguy-mlops-courses')

def download_tickers_data(
        tickers: list[str], 
        days: int, 
    ) -> str:
    """
    Download the data for a list of tickers from the start date to the end date, put them in S3 bucket for further processing
    params:
        tickers: list of tickers
        days: number of days backwards from today to start downloading the data
    returns:
        bucket name and object key
    """

    s3 = boto3.client('s3')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    data = yf.download(
        tickers,
        start=start_date,
        end=end_date,
        interval='1d'
    )

    # Extract close prices
    if len(tickers) == 1:
        # Handle single ticker case
        closes = pd.DataFrame(data['Close'])
        closes.columns = [tickers[0]]
    else:
        closes = data['Close']

    # Forward fill missing values
    closes = closes.fillna(method='ffill')

    # Normalize each stock's prices
    normalized = {}
    for ticker in closes.columns:
        series = closes[ticker]
        # Normalize to percentage changes from first day
        normalized[ticker] = (series / series.iloc[0] - 1) * 100

    data = (
        pd
        .DataFrame(normalized)
        .fillna(0.0)
    )

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_key = f'stock_vectors/stock_data_{timestamp}.csv'

    # Save data to S3
    bucket = DATA_BUCKET_NAME
    key = csv_key

    csv_data = []
    for ticker in data.columns:
        row = [ticker] + data[ticker].tolist()
        csv_data.append(','.join(map(str, row)))
        
    # Save as CSV
    csv_str = '\n'.join(csv_data)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_str
    )

    return json.dumps({
        'bucket': bucket,
        'key': key
    })

def lambda_handler(event, context):    
    logger.info(f"Received event: {event}")
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use["name"]
    tool_input = tool_use["input"]

    try:
        result: str = None
        match tool_name:
            case "get_ticker_data":
                # Extract the ticker and date range from the event
                ticker = tool_input.get('ticker')
                start_date = tool_input.get('start_date')
                end_date = tool_input.get('end_date')
                if not ticker or not start_date or not end_date:
                    logger.error("No ticker, start_date, or end_date provided in the event")
                    result = json.dumps({
                        'error': 'No ticker, start_date, or end_date provided in the event'
                    })
                else:
                    result = get_ticker_data(ticker, start_date, end_date)                   
                    logger.info("ticket data successful", extra={"result": result})
            
            case "get_ticker_recent_history":
                ticker = tool_input.get('ticker')
                period = tool_input.get('period', '1mo')
                interval = tool_input.get('interval', '1d')
                if not ticker:
                    logger.error("No ticker, period, or interval provided in the event")
                    result = json.dumps({
                        'error': 'No ticker, period, or interval provided in the event'
                    })
                else:
                    result = get_ticker_recent_history(ticker, period, interval)
                    logger.info("ticket recent history successful", extra={"result": result})
            
            case "list_industries":
                sector_key = tool_input.get('sector_key')
                if not sector_key:
                    logger.error("No sector_key provided in the event")
                    result =  json.dumps({
                        'error': 'No sector_key provided in the event'
                    })                    
                else:
                    result = list_industries(sector_key)
                    logger.info("Listing industries successful", extra={"result": result})
            
            case "top_sector_companies":
                sector_key = tool_input.get('sector_key')
                if not sector_key:
                    logger.error("No sector_key provided in the event")
                    result =  json.dumps({
                        'error': 'No sector_key provided in the event'
                    })                    
                else:
                    result = top_sector_companies(sector_key)
                    logger.info("Getting top companies successful", extra={"result": result})
            
            case "top_industry_companies":
                industry_key = tool_input.get('industry_key')
                if not industry_key:
                    logger.error("No industry_key provided in the event")
                    result =  json.dumps({
                        'error': 'No industry_key provided in the event'
                    })                    
                else:
                    result = top_industry_companies(industry_key)
                    logger.info("Getting top companies successful", extra={"result": result})
            
            case "download_tickers_data":
                tickers = tool_input.get('tickers')
                days = tool_input.get('days')
                if not tickers or not days:
                    logger.error("No tickers or days provided in the event")
                    result =  json.dumps({
                        'error': 'No tickers or days provided in the event'
                    })                    
                else:
                    result = download_tickers_data(tickers, days)
                    logger.info("Downloading tickers data successful", extra={"result": result})

            case _:
                logger.error(f"Unknown tool name: {tool_use['name']}")
                result =  json.dumps({
                    'error': f"Unknown tool name: {tool_use['name']}"
                })
        
        return {
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            "content": result
        }
    except Exception as e:
        logger.error(f"Error while accessing yfinance: {e}")
        return {
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            'content': f"Error while accessing yfinance: {e}"
        }   

# Testing locally lambda function
if __name__ == "__main__":

    logger.setLevel("DEBUG")
    respose = lambda_handler({
        "name": "get_ticker_data",
        "id": "get_ticket_data_unique_id",
        "input": {
            "ticker": "AAPL",
            "start_date": "2022-01-01",
            "end_date": "2022-12-31"
        },
        "type": "tool_use"
    }, None)

    print(respose is not None)

    respose = lambda_handler({
        "name": "get_ticker_recent_history",
        "id": "get_ticker_recent_history_unique_id",
        "input": {
            "ticker": "AAPL",
            "period": "1mo",
            "interval": "1d"
        },
        "type": "tool_use"
    }, None)

    print(respose is not None)

    respose = lambda_handler({
        "name": "list_industries",
        "id": "list_industries_unique_id",
        "input": {
            "sector_key": "real-estate"
        },
        "type": "tool_use"
    }, None)

    print(respose is not None)

    respose = lambda_handler({
        "name": "top_sector_companies",
        "id": "top_sector_companies_unique_id",
        "input": {
            "sector_key": "real-estate"
        },
        "type": "tool_use"
    }, None)

    print(respose is not None)

    respose = lambda_handler({
        "name": "top_industry_companies",
        "id": "top_industry_companies_unique_id",
        "input": {
            "industry_key": "mortgage-finance"
        },
        "type": "tool_use"
    }, None)

    print(respose is not None)  

    respose = lambda_handler({
        "name": "download_tickers_data",
        "id": "download_tickers_data_unique_id",
        "input": {
            "tickers": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "BAC", "C"] ,
            "days": 120
        },
        "type": "tool_use"
    }, None)

    print(respose is not None)