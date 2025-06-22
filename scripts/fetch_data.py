#!/usr/bin/env python3
"""
Fetch daily stock data from the Alpha Vantage API and save it to a CSV file.

This script retrieves daily stock data for a specified ticker symbol, stores it as a CSV file,
and saves a configuration file with the ticker and fetch timestamp. The ticker can be provided
via command-line arguments or an environment variable.

Attributes:
    parser: Command-line argument parser for the stock ticker.
    API_KEY: Alpha Vantage API key loaded from environment variables.
    stock_symbol: Stock ticker symbol (e.g., 'TSLA', 'AAPL').

Example:
    $ ./fetch_data.py TSLA
    $ ./fetch_data.py --symbol AAPL
"""

import requests
import pandas as pd
from dotenv import load_dotenv
import os
import argparse
import json

# Set up command-line argument parser  ->  accepts the symbol as command-line argument when running fetch_data.py
parser = argparse.ArgumentParser(description="Fetch daily stock data from Alpha Vantage API.")
parser.add_argument("symbol", type=str, help="Stock ticker (e.g., TSLA, AAPL)", nargs="?")  # ?: Allows exe without arg
args = parser.parse_args()

# Load environmental variables from .env file
load_dotenv()

# Get API key from .env
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
if not API_KEY:
    raise ValueError("API key not found in .env file")

# Get stock symbol from .env
stock_symbol = args.symbol or os.getenv("STOCK_SYMBOL", "TSLA")
if not stock_symbol:
    raise ValueError("No stock symbol provided via command-line or .env")

def fetch_data(symbol, outputsize="full"):
    """
    Fetch daily stock data for a given symbol from the Alpha Vantage API.

    Sends a request to the Alpha Vantage API, converts the response to a pandas DataFrame, and
    filters it to include only the last year of data.

    Parameters:
        symbol (str): Stock ticker symbol (e.g., 'TSLA', 'AAPL').
        outputsize (str): Amount of data to retrieve ('full' for full history, 'compact' for 100 days).
                         Defaults to 'full'.

    Returns:
        pandas.DataFrame: DataFrame with daily stock data, including columns 'open', 'high', 'low',
                          'close', 'volume', and a datetime index ('date').

    Exceptions:
        Exception: If the API request fails or the response contains an error (e.g., invalid symbol
                   or rate limit).
    """
    # Construct API url
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize={outputsize}&apikey={API_KEY}"
    print(f"Fetching data for {symbol}...")     # Debug purpose: Print ticker
    
    response = requests.get(url)

    # Check if request was successful
    if response.status_code != 200:
        raise Exception(f"API request failed for {symbol} with status code {response.status_code}")
    
    data = response.json() # Response brings a JSON string and here we parse it to a python dictionary (JSON structure)
    print(f"API response keys for {symbol}: {data.keys()}")     # Debug purpose: Print response keys

    # Check if API errors
    if "Time Series (Daily)" not in data:
        raise Exception(f"Error in API response: {data.get('Note', 'Unknown error')}")

    # Convert API data to DataFrame
    time_series = data["Time Series (Daily)"]   # we only need the "Time Series (Daily)" key-value pair from data
    df = pd.DataFrame.from_dict(time_series, orient="index")    # we need dates as index
    df = df.astype(float)   # Convert values to float
    df.index = pd.to_datetime(df.index, utc=True) # Convert index to datetime

    # Rename columns for clarity
    df.index.name = "date"
    df.columns = ["open", "high", "low", "close", "volume"]

    # Sort by date (ascending) and select 1 year of data
    df = df.sort_index()
    one_year_ago = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=365)).floor('D') # floor('D') rounds timestamp to start of day 00:00:00
    df = df[df.index >= one_year_ago]

    return df

if __name__ == "__main__":  # only runs when script is executed directly
    """
    Execute the script to fetch and save stock data.

    Calls fetch_data to retrieve stock data, saves it to a CSV file, and stores the ticker and
    fetch timestamp in a configuration file.

    Exceptions:
        Exception: If an error occurs during data fetching or saving.
    """
    try:
        # Fetch stock data using command-line argument
        stock_symbol = stock_symbol.upper()  # Convert to uppercase for consistency
        stock_data = fetch_data(stock_symbol)
        print(f"Fetched {stock_symbol} data:")
        print(stock_data.head())

        # Save data to CSV
        output_path = f"data/raw/raw_{stock_symbol.lower()}_data.csv"   # Dynamic naming
        os.makedirs("data", exist_ok=True)
        stock_data.to_csv(output_path, index=True)
        print(f"Data saved to {output_path}")

        # Store the ticker (stock symbol) to config file
        config = {"stock_symbol": stock_symbol, "fetch_time": pd.Timestamp.now().isoformat()}
        with open("data/config.json", "w") as f:
            json.dump(config, f)

    except Exception as e:
        print(f"Error fetching or saving data: {e}")