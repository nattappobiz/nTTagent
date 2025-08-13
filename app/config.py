"""Configuration loader for the application.

This module reads the YAML configuration file shipped with the application and
exposes its contents via accessor functions. Using a dedicated configuration
module makes it simple to adjust paths and patterns in one place without
touching other parts of the code base. The configuration is cached on first
load to avoid unnecessary disk I/O during runtime.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


@lru_cache(maxsize=1)
def get_config() -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Load application and mask configuration from the YAML file.

    Returns
    -------
    tuple
        A tuple where the first element is the application configuration
        dictionary and the second element is the dictionary of mask patterns.
    """
    config_path = Path(__file__).resolve().parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    app_config = data.get("app", {})
    mask_patterns = data.get("mask_patterns", {})
    return app_config, mask_patterns


def setup_logging() -> None:
    """Configure application-wide logging with PII masking.

    The logger is configured to write to the path specified in the configuration
    file. A custom filter is attached to all handlers to mask any personally
    identifiable information (PII) matching the configured regular expressions.
    """
    import os
    import re
    from logging.handlers import RotatingFileHandler

    app_config, mask_patterns = get_config()
    log_file = app_config.get("log_file", "app.log")
    # Ensure log directory exists
    log_path = Path(log_file)
    if log_path.parent and not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Compile regex patterns once for performance
    compiled_patterns = {key: re.compile(pattern) for key, pattern in mask_patterns.items()}

    class MaskingFilter(logging.Filter):
        """Logging filter that masks configured patterns in log messages."""

        def filter(self, record: logging.LogRecord) -> bool:
            message = record.getMessage()
            for regex in compiled_patterns.values():
                message = regex.sub("***", message)
            record.msg = message
            return True

    # Create root logger and set level to INFO
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Avoid attaching multiple handlers when setup_logging() is called multiple times
    if not logger.handlers:
        handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        handler.addFilter(MaskingFilter())
        logger.addHandler(handler)

    # Silence overly verbose loggers from dependencies
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)