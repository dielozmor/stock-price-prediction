import pandas as pd
from dotenv import load_dotenv
import json
import logging
import os
import argparse
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command-line arguments for symbol"""
    parser = argparse.ArgumentParser(description="Set model.")
    parser.add_argument('--symbol', type=str, help='Stock symbol (e.g., TSLA)')
    parser.add_argument('--data-path', type=str, default=None, help='Path to processed data CSV')
    return parser.parse_args()

def load_config(config_path="data/config.json"):
    """Load configuration from a json file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file {config_path} not found.")
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
    elif stock_symbol := os.getenv('STOCK_SYMBOL'):
        return stock_symbol.upper()
    else:
        return 'TSLA'

def load_data(stock_symbol, data_path=None):
    file_path = data_path or f"data/processed/processed_{stock_symbol.lower()}_data.csv"
    try:
        df = pd.read_csv(file_path, parse_dates=['date'], index_col='date')
        df = df.sort_index()    # Ensure data is sorted by index
        if df.index.tz is None:
            logger.info("Localizing index to UTC")
            df.index = df.index.tz_localize('UTC')
        else:
            logger.info("Converting index to UTC")
            df.index = df.index.tz_convert('UTC')
        logger.info(f"Loaded data for {stock_symbol} with shape {df.shape}")
        return df
    except FileNotFoundError:
        logger.error(f"Process data file {file_path} not found.")
        raise
    except pd.errors.ParserError:
        logger.error(f"Error parsing CSV file {file_path}.")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"CSV file {file_path} is empty.")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading data from {file_path}: {e}")
        raise

def select_features(df):
    """
    Select features and target for modeling, with validation to ensure all required columns are present.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the stock data.

    Returns:
    X (pd.DataFrame): Features dataframe with columns ['prev_close', 'volume', 'ma5']
    Y (pd.Series): Target series with 'next_close'

    Raises:
    ValueError: If any required columns are missing from the dataframe.
    """
    features = ['prev_close', 'volume', 'ma5']
    label = 'next_close'
    required_columns = features + [label]

    # Check for missing columns
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing columns in DataFrame: {missing}")
        raise ValueError(f"Missing columns: {missing}")
    
    # Select features and target if all columns are present
    X = df[features]
    Y = df[label]

    # Check for Nan values
    if X.isnull().any().any() or Y.isnull().any():
        logger.error(f"NaN values found in features or label.")
        raise ValueError("NaN values in data.")

    return X, Y

def split_data(X, Y, test_size=0.2):
    """Split data into training and testing sets."""
    try:
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=test_size, shuffle=False)        
        logger.info(f"Split data: {len(X_train)} training, {len(X_test)} testing samples.")
        return X_train, X_test, Y_train, Y_test
    except Exception as e:
        logger.error(f"Error splitting data: {e}")
        raise

def train_model(X_train, Y_train, stock_symbol, timestamp):
    """Train a linear regression model and save it."""
    try:
        model = LinearRegression()
        model.fit(X_train, Y_train)
        model_filename = f"models/{stock_symbol.lower()}_model_{timestamp}.pkl"
        joblib.dump(model, model_filename)  # Save model for later use
        logger.info(f"Trained and saved model for {stock_symbol} to {model_filename}")
        return model
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise

def evaluate_model(model, X_test, Y_test, stock_symbol, timestamp):
    """Evaluate model performance and save metrics."""
    try:
        Y_pred = model.predict(X_test)
        rmse = root_mean_squared_error(Y_test, Y_pred)
        mae = mean_absolute_error(Y_test, Y_pred)
        r2 = r2_score(Y_test, Y_pred)
        metrics = {'RMSE': rmse, 'MAE': mae, 'R2': r2}
        metrics_path = f"docs/model_metrics_{stock_symbol.lower()}_{timestamp}.txt"
        with open(metrics_path, 'w') as f:
            f.write(f"RMSE: {rmse:.2f}\nMAE: {mae:.2f}\nR2: {r2:.2f}\n")
        logger.info(f"Model evaluation for {stock_symbol}: RMSE={rmse:.2f}, MAE={mae:.2f}, R2={r2:.2f}")
        return metrics
    except Exception as e:
        logger.error(f"Error evaluating model: {e}")
        raise

def test_outliers_sensitivity(df, X, Y, stock_symbol, metrics, timestamp):
    """Test model sensitivity to outliers."""
    try:
        if 'is_outlier' not in df.columns:
            logger.warning("No 'is_outlier' column found. Skipping outlier sensitivity test.")
            return None
        df_no_outliers = df[df['is_outlier'] == False]
        X_no_outliers, Y_no_outliers = select_features(df_no_outliers)
        X_train_no, X_test_no, Y_train_no, Y_test_no = split_data(X_no_outliers, Y_no_outliers)
        model_no_outliers = train_model(X_train_no, Y_train_no, f"{stock_symbol}_no_outliers", timestamp)
        metrics_no_outliers = evaluate_model(model_no_outliers, X_test_no, Y_test_no, f"{stock_symbol}_no_outliers", timestamp)
        logger.info(f"Outlier-free model metrics for {stock_symbol}: {metrics_no_outliers}")
        logger.info(f"Comparison: With outliers RMSE={metrics['RMSE']:.2f}, Without outliers RMSE={metrics_no_outliers['RMSE']:.2f}")
        return metrics_no_outliers
    except Exception as e:
        logger.error(f"Error testing outlier sensitivity: {e}")
        raise

def main():
    """Orchestrate the modeling pipeline."""
    config = load_config()
    args = parse_arguments()
    stock_symbol = get_stock_symbol(args, config)
    df = load_data(stock_symbol, args.data_path)

    X, Y = select_features(df)
    X_train, X_test, Y_train, Y_test = split_data(X, Y)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")   
    model = train_model(X_train, Y_train, stock_symbol, timestamp)
    metrics = evaluate_model(model, X_test, Y_test, stock_symbol, timestamp)
    metrics_no_outliers = test_outliers_sensitivity(df, X, Y, stock_symbol, metrics, timestamp)

if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    os.makedirs('models', exist_ok=True)
    os.makedirs('docs', exist_ok=True)
    main()