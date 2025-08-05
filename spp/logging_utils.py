import os
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

# Define project root and default log directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_LOG_DIR = os.getenv("STOCK_LOG_DIR", "logs")


class FetchIdFilter(logging.Filter):
    """Add a default 'fetch_id' to log records if not present.

    This filter ensures that every log record includes a 'fetch_id' attribute, 
    defaulting to 'N/A' if not specified, for consistent logging.

    Attributes:
        None

    Methods:
        filter(record): Adds 'fetch_id' to the log record if missing.

    Returns:
        bool: Always returns True to allow the log record to be processed.
    """
    def filter(self, record):
        if not hasattr(record, 'fetch_id'):
            record.fetch_id = "N/A"
        return True


def setup_logging(
    logger_name: str,
    log_dir: str = DEFAULT_LOG_DIR,
    log_level: int = logging.INFO
) -> logging.Logger:
    """Configure a logger with rotating file logs and console output.

    Sets up a logger with a detailed file handler (rotating daily, keeping 7 days of logs)
    and a simple console handler. Includes a custom filter to ensure 'fetch_id' is present in logs.

    Args:
        logger_name (str): Name of the logger (e.g., 'inspecting_data').
        log_dir (str): Directory for log files, relative to project root if not absolute.
                       Defaults to STOCK_LOG_DIR env variable or 'logs'.
        log_level (int): Logging level (e.g., logging.INFO, logging.DEBUG). Defaults to logging.INFO.

    Returns:
        logging.Logger: Configured logger instance with file and console handlers.

    Raises:
        OSError: If the log directory cannot be created or accessed.
    """
    # Construct absolute log directory path
    log_dir_abs = log_dir if os.path.isabs(log_dir) else os.path.join(PROJECT_ROOT, log_dir)
    os.makedirs(log_dir_abs, exist_ok=True)

    # Get or create the logger instance
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)  # Fixed: Removed duplicate 'log_level'

    # Define formatters
    detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(fetch_id)s] - %(message)s")
    simple_formatter = logging.Formatter("%(message)s")

    # Add the custom filter to handle fetch_id
    logger.addFilter(FetchIdFilter())

    # Clear existing handlers to avoid duplicates
    logger.handlers = []

    # Set up rotating file handler with detailed formatter
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir_abs, f"{logger_name}.log"),
        when="midnight",  # Rotate logs at midnight
        interval=1,       # Rotate daily
        backupCount=7     # Keep 7 days of logs
    )
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Set up console handler with simple formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # Log that the logger has been set up
    logger.info(f"Logger '{logger_name}' has been set up with log level {logging.getLevelName(log_level)}")

    return logger