#!/usr/bin/env python3
"""
Initializes the config.json file with project paths.

This script sets up the configuration file for the stock price prediction project by defining and storing various directory paths used throughout the project. It creates the config directory if it does not exist and logs its actions to the 'logs' directory.

Command-line arguments:
--config_dir: Directory for config files (relative to project_root or absolute). Default is 'config'.
--project_root: Project root directory. Default is '/home/dielozmor/dev/projects/portfolio/stock-price-prediction'.
"""

import argparse
import os
from spp.data_utils import update_config
from spp.logging_utils import setup_logging

# Initialize logger
logger = setup_logging(logger_name="initialize_config", log_dir="logs")

def main():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description="Initialize config.json with project paths")
    parser.add_argument("--config_dir", default="config", help="Directory for config files (relative to project_root or absolute)")
    parser.add_argument("--project_root", default="/home/dielozmor/dev/projects/portfolio/stock-price-prediction", help="Project root directory")
    args = parser.parse_args()

    # Determine the config directory
    if os.path.isabs(args.config_dir):
        config_dir = args.config_dir
    else:
        config_dir = os.path.join(args.project_root, args.config_dir)

    # Create the config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)

    # Define paths for config.json and fetch_history.jsonl
    config_path = os.path.join(config_dir, "config.json")
    history_path = "data/fetch_history.jsonl"

    # Define a placeholder fetch_id for the initial setup
    fetch_id = "initial_setup"

    # Define all relevant paths for the project
    paths = {
        "project_root": args.project_root,
        "utils_dir": "utils",
        "log_dir": "logs",
        "plots_dir": "plots",
        "models_dir": "models",
        "raw_data_dir": "data/raw",
        "processed_data_dir": "data/processed",
        "gaps_dir": "data/intermediate",
        "outliers_dir": "data/outliers",
        "docs_data_eval_dir": "docs/data_evaluation",
        "docs_model_eval_dir": "docs/model_evaluation",
        "current_fetch": {},
        "current_models": {}
    }

    # Log the start of the script
    logger.info(f"Starting config initialization in directory: {config_dir}")

    try:
        # Update the config file, passing the logger
        update_config(
            config_path=config_path,
            history_path=history_path,
            fetch_id=fetch_id,
            logger=logger,
            **paths
        )
        # Log success
        logger.info(f"Successfully initialized config.json at {config_path}")
    except Exception as e:
        # Log any errors and re-raise
        logger.error(f"Failed to initialize config.json: {e}")
        raise

if __name__ == "__main__":
    main()  