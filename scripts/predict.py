#!/usr/bin/env python3
"""
Generate stock price predictions using trained models and save results.

This script loads the latest processed data and trained models, generates predictions for the next trading day,
and saves the results to a CSV file. It supports predictions with available model variants (with/without outliers).
Configurations are managed via config.json.
"""

import os
import pandas as pd
import joblib
from datetime import datetime, timedelta
from typing import Dict, Optional
from spp.logging_utils import setup_logging
from spp.data_utils import parse_arguments, load_config, get_stock_symbol, get_fetch_id, load_data, PROJECT_ROOT
import logging

# Initialize logger
logger = setup_logging(logger_name="predict", log_dir="logs")

def load_models(config: Dict[str, any], models_dir: str, fetch_id: str) -> Dict[str, tuple]:
    """Load available models from the models directory based on config."""
    current_models = config.get("current_models", {})
    models = {}
    
    for variant in ["with_outliers", "without_outliers"]:
        model_id = current_models.get(variant)
        if model_id:
            model_path = os.path.join(models_dir, f"{model_id}.pkl")
            if os.path.exists(model_path):
                model = joblib.load(model_path)
                models[variant] = (model, model_id)
                logger.info(f"Loaded model {model_id} for variant '{variant}'", extra={"fetch_id": fetch_id})
            else:
                logger.warning(f"Model file not found for {variant}: {model_path}", extra={"fetch_id": fetch_id})
    
    if not models:
        raise ValueError("No models available for prediction.")
    
    return models

def generate_predictions(
    df: pd.DataFrame,
    models: Dict[str, tuple],
    stock_symbol: str,
    fetch_id: str
) -> pd.DataFrame:
    """Generate predictions using the loaded models."""
    features = ['prev_close', 'volume', 'ma5']
    if not all(col in df.columns for col in features):
        raise KeyError(f"Missing required features: {features}")
    
    last_row = df.iloc[-1]
    last_features = last_row[features].values.reshape(1, -1)
    last_date = last_row.name
    next_date = last_date + timedelta(days=1)  # TODO: Implement trading day logic
    
    predictions_data = []
    timestamp_now = datetime.now().isoformat()
    
    for variant, (model, model_id) in models.items():
        pred = model.predict(last_features)[0]
        predictions_data.append({
            'future_date': next_date,
            'predicted_next_close': pred,
            'model_variant': variant,
            'based_on_date': last_date,
            'fetch_id': fetch_id,
            'model_id': model_id,
            'timestamp': timestamp_now
        })
        logger.info(f"Predicted {pred:.2f} for {variant} variant", extra={"fetch_id": fetch_id})
    
    return pd.DataFrame(predictions_data)

def save_predictions(
    predictions: pd.DataFrame,
    stock_symbol: str,
    project_root: str,
    config: Dict[str, any]
) -> str:
    """Save the predictions DataFrame to a CSV file."""
    predictions_dir = os.path.join(project_root, "data/predictions")
    os.makedirs(predictions_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_rel_path = os.path.join("data/predictions", f"{stock_symbol.lower()}_predictions_{timestamp}.csv")
    output_abs_path = os.path.join(project_root, output_rel_path)
    predictions.to_csv(output_abs_path, index=False)
    logger.info(f"Predictions saved to {output_rel_path}", extra={"fetch_id": "N/A"})
    return output_rel_path

def main() -> None:
    """Main function to orchestrate the prediction process."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Load config
        config_path = args.config if hasattr(args, 'config') else "config/config.json"
        if not os.path.isabs(config_path):
            config_path = os.path.join(PROJECT_ROOT, config_path)
        config = load_config(config_path, logger)
        
        # Get stock symbol and fetch ID
        stock_symbol = args.stock_symbol.upper() if hasattr(args, 'stock_symbol') and args.stock_symbol else get_stock_symbol(config=config)
        fetch_id = get_fetch_id(config=config)
        logger.info(f"Starting predictions for stock symbol: {stock_symbol}", extra={"fetch_id": fetch_id})
        
        # Load latest processed data
        df = load_data(config, stock_symbol, fetch_id, data_type="processed")
        if df.empty:
            raise ValueError("Loaded DataFrame is empty.")
        
        # Load models
        models_dir = os.path.join(PROJECT_ROOT, config.get("models_dir", "models"))
        models = load_models(config, models_dir, fetch_id)
        
        # Generate predictions
        predictions = generate_predictions(df, models, stock_symbol, fetch_id)
        
        # Save predictions
        save_predictions(predictions, stock_symbol, PROJECT_ROOT, config)
        
        logger.info(f"Completed predictions for {stock_symbol}", extra={"fetch_id": fetch_id})
    
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}", extra={"fetch_id": fetch_id if 'fetch_id' in locals() else "N/A"})
        raise SystemExit(1)
    except KeyError as e:
        logger.error(f"Data error: {str(e)}", extra={"fetch_id": fetch_id if 'fetch_id' in locals() else "N/A"})
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={"fetch_id": fetch_id if 'fetch_id' in locals() else "N/A"})
        raise SystemExit(1)

if __name__ == "__main__":
    main()