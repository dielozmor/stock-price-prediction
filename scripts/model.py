#!/usr/bin/env python3
"""
Model training and evaluation script for stock price prediction.

This script trains Random Forest models on processed stock data, evaluates their performance,
updates config.json with model IDs, and appends metadata to models_history.jsonl.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Tuple
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from spp.logging_utils import setup_logging
from spp.data_utils import load_config, parse_arguments, get_stock_symbol, get_fetch_id, load_data, update_config

# Project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Initialize logger
logger = setup_logging(logger_name="train_model", log_dir="logs")

def select_features(df: pd.DataFrame, config: Dict) -> Tuple[pd.DataFrame, pd.Series]:
    """Select features and target from DataFrame based on config.

    Args:
        df (pd.DataFrame): Processed stock data.
        config (Dict): Configuration dictionary.

    Returns:
        Tuple[pd.DataFrame, pd.Series]: Features (X) and target (Y).

    Raises:
        ValueError: If required columns are missing or NaN values are present.
    """
    features = config['features']
    target = config['target']
    required_columns = features + [target]
    
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    
    X, Y = df[features], df[target]
    if X.isnull().any().any() or Y.isnull().any():
        raise ValueError("NaN values in features or target.")
    
    return X, Y

def split_data(X: pd.DataFrame, Y: pd.Series, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split data into training and testing sets."""
    return train_test_split(X, Y, test_size=test_size, shuffle=False)

def train_model(X_train: pd.DataFrame, Y_train: pd.Series, stock_symbol: str, timestamp: str, fetch_id: str, outlier_handling: str) -> Tuple[RandomForestRegressor, Dict[str, any]]:
    """Train and save a Random Forest model, returning the model and metadata."""
    try:
        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        model.fit(X_train, Y_train)
        model_id = f"model_{stock_symbol.lower()}_{timestamp}_{outlier_handling}"
        model_dir = os.path.join(PROJECT_ROOT, "models")
        os.makedirs(model_dir, exist_ok=True)
        model_filename = os.path.join(model_dir, f"{model_id}.pkl")
        joblib.dump(model, model_filename)
        logger.info(f"Model saved to {model_filename}", extra={"fetch_id": fetch_id})

        metadata = {
            "model_id": model_id,
            "stock_symbol": stock_symbol,
            "fetch_id": fetch_id,
            "timestamp": timestamp,
            "outlier_handling": outlier_handling,
            "features": X_train.columns.tolist(),
            "target": "next_close",
            "model_type": "RandomForest",
            "hyperparameters": {
                "n_estimators": 300,
                "max_depth": 20,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
                "random_state": 42
            }
        }
        return model, metadata
    except Exception as e:
        logger.error(f"Model training failed: {e}", extra={"fetch_id": fetch_id})
        raise

def evaluate_model(model: RandomForestRegressor, X_test: pd.DataFrame, Y_test: pd.Series) -> Dict[str, float]:
    """Evaluate the model and return performance metrics."""
    Y_pred = model.predict(X_test)
    metrics = {
        "RMSE": float(root_mean_squared_error(Y_test, Y_pred)),
        "MAE": float(mean_absolute_error(Y_test, Y_pred)),
        "R2": float(r2_score(Y_test, Y_pred))
    }
    return metrics

def append_to_models_history(metadata: Dict[str, any], history_path: str = "models/models_history.jsonl") -> None:
    """Append model metadata to models_history.jsonl."""
    abs_history_path = os.path.join(PROJECT_ROOT, history_path)
    os.makedirs(os.path.dirname(abs_history_path), exist_ok=True)
    with open(abs_history_path, "a") as f:
        f.write(json.dumps(metadata) + "\n")
    logger.info(f"Appended model metadata to {history_path}", extra={"model_id": metadata.get("model_id", "N/A")})

def main() -> None:
    """Run the model training and evaluation pipeline."""
    fetch_id = "N/A"
    config_path = os.path.join(PROJECT_ROOT, "config", "config.json")
    try:
        config = load_config(config_path, logger=logger)
        args = parse_arguments()
        stock_symbol = get_stock_symbol(args, logger, config)
        fetch_id = config.get("current_fetch", {}).get("fetch_id") or get_fetch_id(args, logger, config, stock_symbol)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Load and prepare data
        df = load_data(config, stock_symbol, fetch_id, data_type="processed", logger=logger)
        X, Y = select_features(df, config)
        X_train, X_test, Y_train, Y_test = split_data(X, Y)

        # Model with outliers
        model_with, metadata_with = train_model(X_train, Y_train, stock_symbol, timestamp, fetch_id, "with_outliers")
        metrics_with = evaluate_model(model_with, X_test, Y_test)
        metadata_with["performance_metrics"] = metrics_with
        append_to_models_history(metadata_with)

        # Model without outliers (if applicable)
        current_models = {"with_outliers": metadata_with["model_id"]}
        if 'is_outlier' in df.columns:
            df_no_outliers = df[df['is_outlier'] == False]
            if not df_no_outliers.empty:
                X_no, Y_no = select_features(df_no_outliers, config)
                X_train_no, X_test_no, Y_train_no, Y_test_no = split_data(X_no, Y_no)
                model_no, metadata_no = train_model(X_train_no, Y_train_no, stock_symbol, timestamp, fetch_id, "without_outliers")
                metrics_no = evaluate_model(model_no, X_test_no, Y_test_no)
                metadata_no["performance_metrics"] = metrics_no
                append_to_models_history(metadata_no)
                current_models["without_outliers"] = metadata_no["model_id"]
            else:
                logger.warning("No data after outlier removal.", extra={"fetch_id": fetch_id})
        else:
            logger.info("No 'is_outlier' column; skipping no-outlier model.", extra={"fetch_id": fetch_id})

        # Update config
        update_config(
            config_path=config_path,
            current_models=current_models,
            logger=logger
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", extra={"fetch_id": fetch_id})
        raise

if __name__ == "__main__":
    main()