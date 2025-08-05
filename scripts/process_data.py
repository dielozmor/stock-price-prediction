#!/usr/bin/env python3
"""
Process stock data by cleaning raw data or engineering features based on the specified step.

This script processes stock data in two possible steps:
- 'clean': Loads raw data, cleans it, flags outliers based on config, and saves the cleaned data.
- 'feature': Loads cleaned data, engineers features, and saves the processed data.
It uses utility functions from data_utils and logging_utils for consistency with fetch_data.py.
"""

import argparse
import json
import logging
import os
from typing import Dict, Optional

import pandas as pd
from dotenv import load_dotenv

from spp.data_utils import (
    parse_arguments,
    load_config,
    get_stock_symbol,
    get_fetch_id,
    load_data,
    save_data,
    update_config,
)
from spp.logging_utils import setup_logging

# Define project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Initialize logger
logger = setup_logging(logger_name="process_data", log_dir="logs")

def clean_data(df: pd.DataFrame, stock_symbol: str) -> pd.DataFrame:
    """Clean the stock data: handle missing values, duplicates, and validate data."""
    # Handle missing values
    if df.isnull().sum().sum() > 0:
        logger.info("Missing values found. Applying forward fill.")
        df = df.ffill()
    else:
        logger.info("No missing values found.")

    # Remove duplicates based on date index
    duplicates = df.index.duplicated().sum()
    if duplicates > 0:
        logger.info(f"Removing {duplicates} duplicate rows.")
        df = df.drop_duplicates(keep="first")
    else:
        logger.info("No duplicates found.")

    # Validate required columns
    required_columns = ["open", "high", "low", "close", "volume"]
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        raise KeyError(f"Missing required columns: {missing_columns}")

    # Enforce data types
    expected_dtypes = {col: "float64" for col in required_columns}
    for col, dtype in expected_dtypes.items():
        if df[col].dtype != dtype:
            logger.error(f"Invalid data type for {col}: expected {dtype}, got {df[col].dtype}")
            raise ValueError(f"Invalid data type for {col}")

    # Check for negative values
    if (df[required_columns] < 0).any().any():
        logger.error("Negative values found in price or volume columns.")
        raise ValueError("Negative values found in data")

    return df

def flag_outliers(df: pd.DataFrame, config: Dict, fetch_id: str) -> pd.DataFrame:
    """Flag outliers in the DataFrame based on a JSON file in the outliers directory."""
    outliers_dir = config.get("outliers_dir", "data/outliers")
    outliers_file = os.path.join(outliers_dir, "outliers.json")

    try:
        with open(outliers_file, 'r') as f:
            outliers_data = json.load(f)
        
        if "outliers" in outliers_data:
            outliers = outliers_data["outliers"]
            df["is_outlier"] = False
            for outlier in outliers:
                try:
                    outlier_date = pd.to_datetime(outlier["date"], utc=True)
                    if outlier_date in df.index:
                        df.loc[outlier_date, "is_outlier"] = True
                        logger.info(f"Flagged outlier on {outlier_date.date()}", extra={"fetch_id": fetch_id})
                    else:
                        logger.warning(f"Outlier date {outlier_date.date()} not found in data.", extra={"fetch_id": fetch_id})
                except (ValueError, KeyError) as e:
                    logger.error(f"Invalid outlier entry: {outlier}. Error: {e}", extra={"fetch_id": fetch_id})
        else:
            logger.info("No outliers defined in the file: skipping is_outlier column.", extra={"fetch_id": fetch_id})

    except FileNotFoundError:
        logger.warning(f"Outliers file {outliers_file} not found. Skipping outlier flagging.", extra={"fetch_id": fetch_id})
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in outliers file {outliers_file}: {e}", extra={"fetch_id": fetch_id})
    except Exception as e:
        logger.error(f"Unexpected error while reading outliers file: {e}", extra={"fetch_id": fetch_id})

    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add engineered features to the DataFrame."""
    df["prev_close"] = df["close"].shift(1).fillna(df["close"])
    df["ma5"] = df["close"].rolling(window=5, min_periods=1).mean()
    df["next_close"] = df["close"].shift(-1).fillna(df["close"])
    logger.info("Added features: prev_close, ma5, next_close")
    return df

def main():
    """Process stock data based on the specified step."""
    args = parse_arguments(mandatory_args=["step"])
    config_path = os.path.join(PROJECT_ROOT, args.config)
    config = load_config(config_path, logger)
    current_fetch = config.get("current_fetch", {})

    stock_symbol = get_stock_symbol(args, logger, config)
    fetch_id = get_fetch_id(args, logger, config)
    extra = {"fetch_id": fetch_id}

    try:
        if args.step == "clean":
            logger.info(f"Cleaning data for {stock_symbol}", extra=extra)
            df = load_data(config, stock_symbol, fetch_id, data_type="raw", logger=logger)
            df_cleaned = clean_data(df, stock_symbol)
            df_cleaned = flag_outliers(df_cleaned, config, fetch_id)
            output_path = save_data(df_cleaned, stock_symbol, fetch_id, "cleaned", PROJECT_ROOT, config, logger)
            current_fetch["cleaned_data_file"] = output_path
            update_config(config_path=config_path, logger=logger, current_fetch=current_fetch)

        elif args.step == "feature":
            logger.info(f"Engineering features for {stock_symbol}", extra=extra)
            df_cleaned = load_data(config, stock_symbol, fetch_id, data_type="cleaned", logger=logger)
            df_featured = engineer_features(df_cleaned)
            output_path = save_data(df_featured, stock_symbol, fetch_id, "processed", PROJECT_ROOT, config, logger)
            current_fetch["processed_data_file"] = output_path
            update_config(config_path=config_path, logger=logger, current_fetch=current_fetch)

    except Exception as e:
        logger.error(f"Processing failed: {e}", extra=extra)
        raise

if __name__ == "__main__":
    load_dotenv()
    main()