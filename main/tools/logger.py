"""
Logging utility for Hyper-RVC.
Provides a centralized logging configuration for the application.
"""

import logging
import os
import sys
from datetime import datetime


def setup_logger(
    name: str = "Hyper-RVC",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = None
) -> logging.Logger:
    """
    Set up and return a logger with both console and file handlers.

    Args:
        name: Name of the logger
        level: Logging level (default: INFO)
        log_to_file: Whether to log to a file
        log_dir: Directory to store log files (default: logs/ in project root)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        if log_dir is None:
            now_dir = os.getcwd()
            log_dir = os.path.join(now_dir, "logs")

        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"hyper_rvc_{timestamp}.log")

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Create a default logger instance
logger = setup_logger()


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Optional name for a child logger

    Returns:
        Logger instance
    """
    if name:
        return setup_logger(name)
    return logger
