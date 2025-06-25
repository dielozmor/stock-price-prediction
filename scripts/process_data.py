import argparse
import json
import logging
import os

import pandas as pd
from dotenv import load_dotenv

# Set up model-specific logger
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command-line arguments for symbol and step."""
    parser = argparse.ArgumentParser(description="Process stock data.") # Creates an ArgumentParser object to handle command-line arguments
    parser.add_argument('--symbol', type=str, help='Stock symbol (e.g., TSLA)') # Adds a --symbol argument to accept a stock symbol as a string
    parser.add_argument('--step', type=str, choices=['clean', 'feature'], required=True, help='Step to perform: clean or feature')
    return parser.parse_args()  # Parses command-line arguments and stores them in args

def load_config(config_path='data/config.json'):
    """Load configuration from a json file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found.")    # Warning as this can proceed with no config file
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file {config_path}: {e}")
        return {}
    except PermissionError as e:
        logger.error(f"Permission denied when reading {config_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading config from {config_path}: {e}")
        return {}
    
def get_stock_symbol(args, config):
    """Determine the stock symbol from command-line, config.json, .env, or default."""

    # Priority: command-line > config.json > environment variable > default
    if args.symbol:
        return args.symbol.upper()
    elif 'stock_symbol' in config:
        return config['stock_symbol'].upper()
    elif (stock_symbol := os.environ.get('STOCK_SYMBOL')):
        return stock_symbol.upper()
    else:
        return 'TSLA'

def load_raw_data(stock_symbol):
    """Load raw stock data from a CSV file."""
    file_path = f"data/raw/raw_{stock_symbol.lower()}_data.csv"   # Calling get_stock_symbol would make this function rely on it
    try:
        df = pd.read_csv(file_path, parse_dates=['date'], index_col='date')
        if df.index.tz is None:
            logger.info("Localizing index to UTC")
            df.index = df.index.tz_localize('UTC')   # Ensure UTC timezone
        else:
            logger.info("Converting index to UTC")
            df.index = df.index.tz_convert('UTC')
        logger.info(f"Loaded data for {stock_symbol} with shape {df.shape}")
        return df
    except FileNotFoundError:
        logger.error(f"Raw data file {file_path} not found.")  # Error as this needs to be solved
        raise   # Raises FileNotFoundError

def load_cleaned_data(stock_symbol):
    """Load cleaned stock data from a CSV file."""
    file_path = f"data/processed/cleaned_{stock_symbol.lower()}_data.csv"
    try:
        df = pd.read_csv(file_path, parse_dates=['date'], index_col='date')
        if df.index.tz is None:
            logger.info("Localizing index to UTC")
            df.index = df.index.tz_localize('UTC')
        else:
            logger.info("Converting index to UTC")
            df.index = df.index.tz_convert('UTC')
        logger.info(f"Loaded cleaned data for {stock_symbol} with shape {df.shape}")
        return df
    except FileNotFoundError:
        logger.error(f"Cleaned data file {file_path} not found.")
        raise

def clean_data(df, stock_symbol, config):
    """Clean the stock data: handle missing values, duplicates, validate data, and detect outliers."""
    # Check for missing values
    if df.isnull().sum().sum() > 0:
        logger.info("Missing values found. Applying forward fill.")
        df = df.ffill() # Forward fill strategy
    else:
        logger.info("No missing values found.")

    # Remove duplicates based on date index
    duplicates = df.index.duplicated().sum()
    if duplicates > 0:
        logger.info(f"Removing {duplicates} duplicate rows.")
        df = df.drop_duplicates(keep='first')
    else:
        logger.info("No duplicates found.")

    # Validate required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        raise KeyError(f"Missing required columns: {missing_columns}")
    
    # Enforce data types
    expected_dtypes = {
        'open': 'float64',
        'high': 'float64',
        'low': 'float64',
        'close': 'float64',
        'volume': 'float64'
    }
    for col, dtype in expected_dtypes.items():
        if df[col].dtype != dtype:
            logger.error(f"Invalid data type for {col}: expected {dtype}, got {df[col].dtype}")
            raise ValueError(f"Invalid data type for {col}")
        
    # Check for negative values
    if (df[['open', 'high', 'low', 'close', 'volume']] < 0).any().any():
        logger.error("Negative values found in price or volume columns.")
        # df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].clip(lower=0)
        # logger.info("Negative vlaues clipped to 0.")
        raise ValueError("Negative values found in data")
    
    return df

def flag_outliers(df, config):
    """Flag outliers in the DataFrame using dates from config.json"""
    # Verify config file and flag outliers
    if 'outliers' in config and config['outliers']:
        # Create column with default value
        df['is_outlier'] = False
        for outlier in config['outliers']:
            try:
                outlier_date = pd.to_datetime(outlier['date'], utc=True)
                if outlier_date in df.index:
                    df.loc[outlier_date, 'is_outlier'] = True
                    logger.info(f"Flagged outlier on {outlier_date.date()} in {outlier.get('column', 'unknown')}")
                else:
                    logger.warning(f"Outlier date {outlier_date.date()} not found in data.")
            except (ValueError, KeyError) as e:  # Both errors in case key or value from config missing or with errors
                logger.error(f"Invalid outlier entry in config: {outlier}. Error: {e}")
    else:
        logger.info("No outliers defined in config: skipping is_outlier column.")
    return df

def engineer_features(df, config):
    """Add engineer features to the DataFrame."""
    df['prev_close'] = df['close'].shift(1)
    df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
    df['next_close'] = df['close'].shift(-1)
    logger.info("Added features: prev_close, ma5, next_close")
    return df

    
def save_cleaned_data(df, stock_symbol):
    """ Save the cleaned data to a CSV file."""
    file_path = f"data/processed/cleaned_{stock_symbol.lower()}_data.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        df.to_csv(file_path, index=True)
        logger.info(f"Cleaned data saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save cleaned data to {file_path}: {e}")
        raise

def save_processed_data(df, stock_symbol):
    """Save the processed data with features to a final CSV file."""
    file_path = f"data/processed/processed_{stock_symbol.lower()}_data.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        df.to_csv(file_path, index=True)
        logger.info(f"Processed data saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save processed data to {file_path}: {e}")
        raise

def main():
    """Main function to process the stock data based on the specified step."""
    config = load_config()
    args = parse_arguments()
    stock_symbol = get_stock_symbol(args, config)
    step = args.step
    
    if step == 'clean':
        logger.info(f"Cleaning data for {stock_symbol}")
        df = load_raw_data(stock_symbol)
        df_cleaned = clean_data(df, stock_symbol, config)
        df_cleaned = flag_outliers(df_cleaned, config)
        save_cleaned_data(df_cleaned, stock_symbol)
    elif step == 'feature':
        logger.info(f"Engineering features for {stock_symbol}")
        df_cleaned = load_cleaned_data(stock_symbol)
        df_featured = engineer_features(df_cleaned, config)
        save_processed_data(df_featured, stock_symbol)

if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()