#!/usr/bin/env python3
"""
Monitor model performance from models_history.jsonl and save summary to docs/model_evaluation/performance_summary_tsla_TIMESTAMP.csv.
"""
import os
import json
import pandas as pd
from datetime import datetime
from spp.logging_utils import setup_logging

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logger = setup_logging(logger_name="monitor_performance", log_dir="logs")

def get_latest_timestamp(history_path="models/models_history.jsonl"):
    """Get the latest timestamp from models_history.jsonl."""
    try:
        models = []
        history_file = os.path.join(PROJECT_ROOT, history_path)
        if not os.path.exists(history_file):
            logger.error(f"Model history file not found: {history_file}")
            raise FileNotFoundError(f"Model history file not found: {history_file}")
        with open(history_file, "r") as f:
            for line in f:
                models.append(json.loads(line.strip()))
        if not models:
            logger.warning("No models found in history file.")
            return datetime.now().strftime("%Y%m%d_%H%M%S")
        return max(model["timestamp"] for model in models)
    except Exception as e:
        logger.error(f"Failed to get latest timestamp: {str(e)}")
        raise

def monitor_performance(history_path="models/models_history.jsonl"):
    """Monitor model performance and save summary with timestamp."""
    try:
        # Load model history
        models = []
        history_file = os.path.join(PROJECT_ROOT, history_path)
        if not os.path.exists(history_file):
            logger.error(f"Model history file not found: {history_file}")
            raise FileNotFoundError(f"Model history file not found: {history_file}")
        with open(history_file, "r") as f:
            for line in f:
                models.append(json.loads(line.strip()))
        df = pd.DataFrame(models)

        # Extract metrics
        df["R2"] = df["performance_metrics"].apply(lambda x: x["R2"])
        df["RMSE"] = df["performance_metrics"].apply(lambda x: x["RMSE"])
        df["MAE"] = df["performance_metrics"].apply(lambda x: x["MAE"])

        # Filter for TSLA and fetch_20250617_093553
        df = df[(df["stock_symbol"] == "TSLA") & (df["fetch_id"] == "fetch_20250617_093553")]
        logger.info(f"Monitoring {len(df)} models for TSLA (fetch_20250617_093553)")

        # Flag models with R² < 0.75
        df["Status"] = df["R2"].apply(lambda x: "Review" if x < 0.75 else "Good")
        summary = df[["model_id", "model_type", "outlier_handling", "R2", "RMSE", "MAE", "Status"]]

        # Save summary with timestamp
        timestamp = get_latest_timestamp(history_path)
        summary_path = os.path.join(PROJECT_ROOT, f"docs/model_evaluation/performance_summary_tsla_{timestamp}.csv")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        summary.to_csv(summary_path, index=False)
        logger.info(f"Performance summary saved to {summary_path}")

        # Log flagged models
        flagged = summary[summary["Status"] == "Review"]
        if not flagged.empty:
            logger.warning(f"Flagged models for review (R² < 0.75):\n{flagged}")

    except Exception as e:
        logger.error(f"Monitoring failed: {str(e)}")
        raise

if __name__ == "__main__":
    monitor_performance()