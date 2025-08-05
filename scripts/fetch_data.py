#!/usr/bin/env python3
"""
Fetch stock data from the Alpha Vantage API and save it to a CSV file.

This script retrieves stock data based on the specified API function (e.g., daily, weekly, intraday),
saves it as a CSV, and manages configurations:
- config.json: Stores the configuration for the most recent fetch under 'current_fetch'.
- fetch_history.jsonl: Appends each fetch's full configuration for historical tracking.
"""

import requests
import pandas as pd
from dotenv import load_dotenv
import os
from typing import Optional
from spp.logging_utils import setup_logging
from spp.data_utils import parse_arguments, update_config, load_config

# Define project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Initialize logger
logger = setup_logging(logger_name="fetch_data", log_dir="logs")

def fetch_stock_data(
    stock_symbol: str,
    api_key: str,
    fetch_id: str,
    api_function: str = "TIME_SERIES_DAILY",
    days_back: int = 365,
    outputsize: str = "full",
    interval: Optional[str] = None
) -> pd.DataFrame:
    """Fetch stock data from Alpha Vantage API with a dynamic time series key."""
    if api_function == "TIME_SERIES_INTRADAY" and interval is None:
        raise ValueError("Interval is required for TIME_SERIES_INTRADAY")

    # Determine the time series key Fbased on api_function
    if api_function == "TIME_SERIES_DAILY":
        time_series_key = "Time Series (Daily)"
    elif api_function == "TIME_SERIES_WEEKLY":
        time_series_key = "Weekly Time Series"
    elif api_function == "TIME_SERIES_MONTHLY":
        time_series_key = "Monthly Time Series"
    elif api_function == "TIME_SERIES_INTRADAY":
        time_series_key = f"Time Series ({interval})"
    else:
        raise ValueError(f"Unsupported API function: {api_function}")

    # Construct the API URL
    url = f"https://www.alphavantage.co/query?function={api_function}&symbol={stock_symbol}"
    if api_function == "TIME_SERIES_INTRADAY":
        url += f"&interval={interval}"
    url += f"&outputsize={outputsize}&apikey={api_key}"

    # Make the API request
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Check for the time series key in the response
    if time_series_key not in data:
        error_msg = data.get('Note', 'Unknown error')
        logger.error(f"Error in API response for {stock_symbol}: {error_msg}", extra={"fetch_id": fetch_id})
        raise Exception(f"Error in API response for {stock_symbol}: {error_msg}")

    # Convert the data to a DataFrame
    time_series = data[time_series_key]
    df = pd.DataFrame.from_dict(time_series, orient="index")
    df = df.astype(float)
    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "date"
    df.columns = ["open", "high", "low", "close", "volume"]
    df = df.sort_index()

    # Filter by days_back
    cutoff_date = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days_back)).floor('D')
    df = df[df.index >= cutoff_date]

    if df.empty:
        logger.warning(f"No data fetched for {stock_symbol}", extra={"fetch_id": fetch_id})

    return df

def save_stock_data(
    df: pd.DataFrame,
    stock_symbol: str,
    fetch_id: str,
    project_root: str,
    config: dict
) -> str:
    """Save the stock data DataFrame to a CSV file."""
    output_rel_path = os.path.join(config["raw_data_dir"], f"raw_{stock_symbol.lower()}_{fetch_id}.csv")
    output_abs_path = os.path.join(project_root, output_rel_path)
    os.makedirs(os.path.dirname(output_abs_path), exist_ok=True)
    df.to_csv(output_abs_path, index=True)
    logger.info(f"Data saved to {output_rel_path} with {len(df)} rows", extra={"fetch_id": fetch_id})
    return output_rel_path

def main() -> None:
    """Main function to orchestrate the stock data fetching process."""
    try:
        # Parse arguments using the utility function
        args = parse_arguments(mandatory_args=["stock_symbol"])

        # Handle config path
        config_path = args.config
        if not os.path.isabs(config_path):
            config_path = os.path.join(PROJECT_ROOT, config_path)
        config_dir = os.path.dirname(config_path)
        os.makedirs(config_dir, exist_ok=True)
        history_path = "data/fetch_history.jsonl"

        # Use provided fetch_id or generate one
        if hasattr(args, 'fetch_id') and args.fetch_id:
            fetch_id = args.fetch_id
        else:
            fetch_timestamp = pd.Timestamp.now()
            fetch_id = f"fetch_{fetch_timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting fetch for stock symbol: {args.stock_symbol}", extra={"fetch_id": fetch_id})

        # Check for interval if api_function is TIME_SERIES_INTRADAY
        if args.api_function == "TIME_SERIES_INTRADAY" and not args.interval:
            logger.error("Interval is required for TIME_SERIES_INTRADAY", extra={"fetch_id": fetch_id})
            raise ValueError("Interval is required for TIME_SERIES_INTRADAY")

        # Determine stock symbol
        stock_symbol = args.stock_symbol.upper()

        # Load API key
        load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            logger.error("API key not found in .env file", extra={"fetch_id": fetch_id})
            raise ValueError("API key not found in .env file")
        
        # Load current config
        config = load_config(config_path, logger, fetch_id)

        # Fetch stock data
        stock_data = fetch_stock_data(
            stock_symbol,
            api_key,
            fetch_id,
            api_function=args.api_function,
            days_back=args.days_back,
            outputsize=args.outputsize,
            interval=args.interval if hasattr(args, 'interval') else None
        )
        
        # Log fetch details
        logger.info(
            f"Fetched {stock_symbol} data using {args.api_function} with shape {stock_data.shape}, "
            f"date range: {stock_data.index.min()} to {stock_data.index.max()}",
            extra={"fetch_id": fetch_id}
        )

        # Generate fetch metadata
        fetch_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        output_path = save_stock_data(stock_data, stock_symbol, fetch_id, PROJECT_ROOT, config)
        
        # Create fetch details
        fetch_details = {
            "fetch_id": fetch_id,
            "stock_symbol": stock_symbol,
            "fetch_time": fetch_time,
            "raw_data_file": output_path,
            "data_start_date": stock_data.index.min().strftime("%Y-%m-%d") if not stock_data.empty else None,
            "data_end_date": stock_data.index.max().strftime("%Y-%m-%d") if not stock_data.empty else None,
            "api_function": args.api_function,
            "days_back": args.days_back,
            "outputsize": args.outputsize,
            "interval": args.interval if hasattr(args, 'interval') else None,
            "row_count": len(stock_data)
        }

        # Update config files with current_fetch
        update_config(
            config_path=config_path,
            history_path=history_path,
            logger=logger,
            current_fetch=fetch_details
        )

        logger.info(f"Completed fetch for {stock_symbol}", extra={"fetch_id": fetch_id})

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}", extra={"fetch_id": fetch_id if 'fetch_id' in locals() else "N/A"})
        raise SystemExit(1)
    except requests.RequestException as e:
        logger.error(f"Network error: {str(e)}", extra={"fetch_id": fetch_id if 'fetch_id' in locals() else "N/A"})
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={"fetch_id": fetch_id if 'fetch_id' in locals() else "N/A"})
        raise SystemExit(1)

if __name__ == "__main__":
    main()