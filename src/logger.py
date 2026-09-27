"""
Logging Configuration Module
Provides structured, thread-safe console and file logging.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from src.config import CONFIG


def get_logger(name: str = "CodeAlpha") -> logging.Logger:
    """
    Returns a configured logger with console and rotating file handlers.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Rotating File Handler (up to 5MB, 3 backups)
        os.makedirs(CONFIG.paths.logs_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            CONFIG.paths.log_file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
