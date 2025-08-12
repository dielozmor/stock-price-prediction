import os
import pandas as pd
import joblib
from datetime import datetime, timedelta
from spp.data_utils import parse_arguments, load_config, get_stock_symbol, get_fetch_id, load_data, extract_timestamp, PROJECT_ROOT
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(args):
    """Generate stock price predictions using trained models and save results."""
    try:
        # Load config
        config = load_config()
        logger.info("Configuration loaded successfully.")

        # Get stock symbol and fetch ID
        stock_symbol = args.stock_symbol.upper() if args.stock_symbol else get_stock_symbol(config=config)
        fetch_id = get_fetch_id(config=config)
        logger.info(f"Processing stock: {stock_symbol}, fetch_id: {fetch_id}")

        # Load latest processed data
        df = load_data(config, stock_symbol, fetch_id, data_type="processed")
        if df.empty:
            logger.error("Loaded DataFrame is empty.")
            raise ValueError("No data available for predictions.")

        # Validate features
        features = ['prev_close', 'volume', 'ma5']
        if not all(col in df.columns for col in features):
            logger.error(f"Missing required features: {features}")
            raise KeyError("Required features not found in data.")

        # Get the last row's features
        last_row = df.iloc[-1]
        last_features = last_row[features].values.reshape(1, -1)

        # Load models
        models_dir = os.path.join(PROJECT_ROOT, "models")
        model_id_with = config["current_models"]["with_outliers"]
        model_id_without = config["current_models"]["without_outliers"]

        for model_id in [model_id_with, model_id_without]:
            model_path = os.path.join(models_dir, f"{model_id}.pkl")
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                raise FileNotFoundError(f"Model {model_id} not found.")

        model_with = joblib.load(os.path.join(models_dir, f"{model_id_with}.pkl"))
        model_without = joblib.load(os.path.join(models_dir, f"{model_id_without}.pkl"))
        logger.info("Models loaded successfully.")

        # Predict next_close
        pred_with = model_with.predict(last_features)[0]
        pred_without = model_without.predict(last_features)[0]

        # Calculate next trading day
        last_date = last_row.name
        next_date = last_date + timedelta(days=1)  # TODO: Add trading day logic

        # Create predictions DataFrame
        predictions = pd.DataFrame({
            'future_date': [next_date, next_date],
            'predicted_next_close': [pred_with, pred_without],
            'model_variant': ['with_outliers', 'without_outliers'],
            'based_on_date': [last_date, last_date],
            'fetch_id': [fetch_id, fetch_id],
            'model_id': [model_id_with, model_id_without],
            'timestamp': [datetime.now().isoformat(), datetime.now().isoformat()]
        })

        # Save to predictions dir
        predictions_dir = os.path.join(PROJECT_ROOT, "data/predictions")
        os.makedirs(predictions_dir, exist_ok=True)
        predictions_file = os.path.join(predictions_dir, f"{stock_symbol.lower()}_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        predictions.to_csv(predictions_file, index=False)
        logger.info(f"Predictions saved to: {predictions_file}")

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise

if __name__ == "__main__":
    args = parse_arguments()
    main(args)