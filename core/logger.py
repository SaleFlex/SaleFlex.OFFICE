"""
Logging utilities for SaleFlex.OFFICE.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from settings.settings import Settings


_LOGGER_CONFIGURED = False


def _configure_root_logger() -> None:
    """Configure application-wide logging once."""
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    settings = Settings()
    level_name = settings.logging_level.upper()
    level = getattr(logging, level_name, logging.INFO)

    handlers: list[logging.Handler] = []
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if settings.logging_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    if settings.logging_file:
        log_dir = Path(settings.logging_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / settings.logging_file_name
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)
    _LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance."""
    _configure_root_logger()
    return logging.getLogger(name)
