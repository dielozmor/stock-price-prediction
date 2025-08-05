import os
import argparse
import logging
import json
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime

# Define project root and default config path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CONFIG_PATH = os.getenv("STOCK_CONFIG_PATH", "config/config.json")

def parse_arguments(
    mandatory_args: Optional[List[str]] = None
) -> argparse.Namespace:
    """Parse command-line arguments with enhanced error handling and scalability."""
    parser = argparse.ArgumentParser(description="Stock data or notebook export script")
    
    argument_configs = {
        "stock_symbol": {"type": str, "help": "Stock symbol (e.g., 'TSLA')"},
        "fetch_id": {"type": str, "help": "Fetch ID for the data (e.g., 'fetch_20250617_093553')"},
        "config": {"type": str, "default": "config/config.json", "help": "Path to configuration file"},
        "api_function": {"type": str, "default": "TIME_SERIES_DAILY", "help": "Alpha Vantage API function"},
        "days_back": {"type": int, "default": 365, "help": "Number of days back to fetch data"},
        "outputsize": {"type": str, "default": "full", "help": "API output size ('compact' or 'full')"},
        "step": {"type": str, "choices": ["clean", "feature"], "help": "Processing step: clean or feature"},
        "notebook": {"type": str, "help": "Name of the notebook to export (e.g., inspect_data.ipynb)"},
        "output_dir": {"type": str, "help": "Directory to save exported files (e.g., docs/data_evaluation)"},
    }
        
    if mandatory_args:
        invalid_args = [arg for arg in mandatory_args if arg not in argument_configs]
        if invalid_args:
            parser.error(f"Invalid mandatory arguments: {', '.join(invalid_args)}")
    
    for arg, spec in argument_configs.items():
        if arg in (mandatory_args or []):
            parser.add_argument(f"--{arg}", type=spec["type"], required=True, help=spec["help"])
        else:
            parser.add_argument(
                f"--{arg}",
                type=spec["type"],
                default=spec.get("default"),
                choices=spec.get("choices"),
                help=spec["help"],
            )
    
    return parser.parse_args()


def get_stock_symbol(
    args: Optional[argparse.Namespace] = None,
    logger: Optional[logging.Logger] = None,
    config: Optional[Dict] = None,
    mandatory: bool = False
) -> str:
    """Retrieve stock symbol from command-line arguments or config."""
    if mandatory:
        if args is None or not hasattr(args, 'stock_symbol') or not args.stock_symbol:
            raise ValueError("Stock symbol is required but not provided via command-line")
        stock_symbol = args.stock_symbol.upper()
        if logger:
            logger.info(f"Using stock symbol from command-line: {stock_symbol}")
        return stock_symbol
    else:
        if args and hasattr(args, 'stock_symbol') and args.stock_symbol:
            stock_symbol = args.stock_symbol.upper()
            if logger:
                logger.info(f"Using stock symbol from command-line: {stock_symbol}")
            return stock_symbol
        elif config and "current_fetch" in config and "stock_symbol" in config["current_fetch"]:
            stock_symbol = config["current_fetch"]["stock_symbol"].upper()
            if logger:
                logger.info(f"Using stock symbol from current_fetch in config: {stock_symbol}")
            return stock_symbol
        elif config and "stock_symbol" in config:
            stock_symbol = config["stock_symbol"].upper()
            if logger:
                logger.info(f"Using stock symbol from config: {stock_symbol}")
            return stock_symbol
        else:
            raise ValueError("Stock symbol must be provided via command-line, current_fetch in config, or top-level config")


def get_fetch_id(
    args: Optional[argparse.Namespace] = None,
    logger: Optional[logging.Logger] = None,
    config: Optional[Dict] = None,
    stock_symbol: Optional[str] = None,
    mandatory: bool = False
) -> str:
    """Retrieve fetch ID from command-line arguments or config."""
    if args and hasattr(args, 'fetch_id') and args.fetch_id:
        fetch_id = args.fetch_id
        if logger:
            logger.info(f"Using fetch ID from command-line: {fetch_id} for stock symbol: {stock_symbol or 'N/A'}")
        return fetch_id
    elif config and "current_fetch" in config and "fetch_id" in config["current_fetch"]:
        fetch_id = config["current_fetch"]["fetch_id"]
        if logger:
            logger.info(f"Using fetch ID from current_fetch in config: {fetch_id} for stock symbol: {stock_symbol or 'N/A'}")
        return fetch_id
    elif mandatory:
        raise ValueError("Fetch ID is required but not provided via command-line")
    else:
        raise ValueError("Fetch ID must be provided via command-line or current_fetch in config")


def load_data(
    config: Dict[str, Any],
    stock_symbol: str,
    fetch_id: str,
    data_type: str = "raw",
    logger: Optional[logging.Logger] = None,
) -> pd.DataFrame:
    """Load stock data from a CSV file based on type, stock symbol, and fetch_id."""
    # Get the specific data file from config, if available
    data_file = config.get("current_fetch", {}).get(f"{data_type}_data_file")
    
    if data_file is not None:
        # Use the provided data_file as a relative path from PROJECT_ROOT
        data_file_path = os.path.join(PROJECT_ROOT, data_file)
    else:
        # Construct the path if no specific file is provided
        dir_map = {"raw": "raw_data_dir", "cleaned": "processed_data_dir", "processed": "processed_data_dir"}
        dir_key = dir_map.get(data_type, "data")
        data_dir = config.get(dir_key, "data")
        file_name = f"{data_type}_{stock_symbol.lower()}_{fetch_id}.csv"
        data_file_path = os.path.join(PROJECT_ROOT, data_dir, file_name)

    if not os.path.exists(data_file_path):
        error_msg = f"Data file {data_file_path} not found for {data_type} data"
        if logger:
            logger.error(error_msg, extra={"fetch_id": fetch_id})
        raise FileNotFoundError(error_msg)

    try:
        df = pd.read_csv(data_file_path, parse_dates=["date"], index_col="date")
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be a DatetimeIndex")
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")
        required_columns = ["open", "high", "low", "close", "volume"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
        if logger:
            logger.info(f"Loaded {data_type} data from {data_file_path} with {len(df)} rows", extra={"fetch_id": fetch_id})
        return df
    except pd.errors.EmptyDataError as e:
        if logger:
            logger.error(f"CSV file {data_file_path} is empty: {e}", extra={"fetch_id": fetch_id})
        raise
    except Exception as e:
        if logger:
            logger.error(f"Error loading {data_file_path}: {e}", extra={"fetch_id": fetch_id})
        raise


def save_data(
    df: pd.DataFrame,
    stock_symbol: str,
    fetch_id: str,
    data_type: str,
    project_root: str,
    config: Dict[str, Any],
    logger: Optional[logging.Logger] = None,
) -> str:
    """Save stock data to a CSV file based on type, stock symbol, and fetch_id."""
    dir_map = {"raw": "raw_data_dir", "cleaned": "processed_data_dir", "processed": "processed_data_dir"}
    dir_key = dir_map.get(data_type, "data")
    output_dir = config.get(dir_key, "data")  # Get the actual directory from config
    output_rel_path = f"{output_dir}/{data_type}_{stock_symbol.lower()}_{fetch_id}.csv"
    output_abs_path = os.path.join(project_root, output_rel_path)

    try:
        os.makedirs(os.path.dirname(output_abs_path), exist_ok=True)
        df.to_csv(output_abs_path, index=True)
        if logger:
            logger.info(f"{data_type.capitalize()} data saved to {output_rel_path} with {len(df)} rows", extra={"fetch_id": fetch_id})
        return output_rel_path
    except Exception as e:
        if logger:
            logger.error(f"Failed to save {data_type} data to {output_rel_path}: {e}", extra={"fetch_id": fetch_id})
        raise


def format_df(
    df: pd.DataFrame
) -> pd.DataFrame:
    """Format a DataFrame for display with financial data formatting."""
    def format_cell(x, row_index, col_name):
        if row_index == "count":
            return '{:,.0f}'.format(x) if pd.api.types.is_number(x) else str(x)
        elif col_name == "volume":
            return '{:,.0f}'.format(x) if pd.api.types.is_number(x) else str(x)
        elif col_name in ["high", "low", "close", "open"]:
            return '{:,.2f}'.format(x) if pd.api.types.is_number(x) else str(x)
        else:
            return '{:,.2f}'.format(x) if pd.api.types.is_number(x) else str(x)
    
    formatted_data = {}
    for col in df.columns:
        formatted_data[col] = [format_cell(df.at[idx, col], idx, col) for idx in df.index]
    
    if isinstance(df.index, pd.DatetimeIndex):
        formatted_index = df.index.strftime('%Y-%m-%d')
    else:
        formatted_index = df.index
    
    formatted_df = pd.DataFrame(formatted_data, index=formatted_index)
    return formatted_df


def load_config(
    config_path: str = DEFAULT_CONFIG_PATH,
    logger: Optional[logging.Logger] = None,
    fetch_id: Optional[str] = None
) -> dict:
    """Load configuration from a JSON file."""
    abs_config_path = os.path.join(PROJECT_ROOT, config_path)
    try:
        if not os.path.exists(abs_config_path):
            error_msg = f"Config file {abs_config_path} not found"
            if logger:
                logger.error(error_msg, extra={"fetch_id": fetch_id or "N/A"})
            raise FileNotFoundError(error_msg)
        with open(abs_config_path, 'r') as f:
            config = json.load(f)
            if logger:
                logger.info(f"Successfully loaded config file from {abs_config_path}", extra={"fetch_id": fetch_id or "N/A"})
                logger.info(f"Config keys: {', '.join(config.keys())}", extra={"fetch_id": fetch_id or "N/A"})
            return config
    except json.JSONDecodeError as e:
        error_msg = f"Failed to decode JSON from {abs_config_path}: {str(e)}"
        if logger:
            logger.error(error_msg, extra={"fetch_id": fetch_id or "N/A"})
        raise
    except OSError as e:
        error_msg = f"Error reading config file {abs_config_path}: {str(e)}"
        if logger:
            logger.error(error_msg, extra={"fetch_id": fetch_id or "N/A"})
        raise


def update_config(
    config_path: str = DEFAULT_CONFIG_PATH,
    history_path: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> None:
    """Update config.json and append to fetch_history.jsonl only if current_fetch is not empty."""
    fetch_id = kwargs.get("fetch_id", "N/A")
    if "current_fetch" in kwargs and isinstance(kwargs["current_fetch"], dict):
        fetch_id = kwargs["current_fetch"].get("fetch_id", fetch_id)
    
    # Load existing config or initialize
    abs_config_path = os.path.join(PROJECT_ROOT, config_path)
    if os.path.exists(abs_config_path):
        with open(abs_config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}
        os.makedirs(os.path.dirname(abs_config_path), exist_ok=True)

    # Update config with kwargs
    if "current_fetch" in kwargs:
        config["current_fetch"] = kwargs["current_fetch"]
    if "current_models" in kwargs:
        config["current_models"] = kwargs["current_models"]
    config.update({k: v for k, v in kwargs.items() if k not in ["current_fetch", "current_models"]})

    # Save updated config
    with open(abs_config_path, "w") as f:
        json.dump(config, f, indent=4)
    if logger:
        logger.info(f"Updated {config_path} with {kwargs}", extra={"fetch_id": fetch_id})

    # Append to fetch_history.jsonl only if history_path is provided, current_fetch is in kwargs, and current_fetch is not empty
    if history_path and "current_fetch" in kwargs and kwargs["current_fetch"]:
        abs_history_path = os.path.join(PROJECT_ROOT, history_path)
        os.makedirs(os.path.dirname(abs_history_path), exist_ok=True)
        with open(abs_history_path, "a") as f:
            f.write(json.dumps(kwargs["current_fetch"]) + "\n")
        if logger:
            logger.info(f"Appended fetch to {history_path}", extra={"fetch_id": fetch_id})


def extract_timestamp(
    model_id: str
) -> str:
    """Extract the timestamp from a model ID.

    Args:
        model_id (str): The model ID, e.g., 'model_tsla_20250730_102338_with_outliers'.

    Returns:
        str: The timestamp, e.g., '20250730_102338'.

    Raises:
        ValueError: If the model ID format is invalid.
    """
    # Split by underscores
    parts = model_id.split('_')
    
    # Ensure at least 6 parts
    if len(parts) < 6:
        raise ValueError(f"Model ID has too few parts: {len(parts)} < 6")
    
    # Check prefix
    if parts[0] != 'model':
        raise ValueError(f"Model ID must start with 'model', got '{parts[0]}'")
    
    # Check suffix
    suffix = '_'.join(parts[-2:])
    if suffix not in ['with_outliers', 'without_outliers']:
        raise ValueError(f"Model ID must end with 'with_outliers' or 'without_outliers', got '{suffix}'")
    
    # Extract timestamp
    timestamp = '_'.join(parts[-4:-2])
    
    # Validate timestamp format
    try:
        datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
    except ValueError:
        raise ValueError(f"Invalid timestamp format: '{timestamp}'")
    
    return timestamp
