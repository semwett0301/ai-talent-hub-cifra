"""Shared logging — `configure_logging()` once at startup, `get_logger()` per module."""

from domain.core.logging.setup import (
    CHATTY_LOGGERS,
    NOISY_LOGGERS,
    configure_logging,
    get_logger,
)

__all__ = ["CHATTY_LOGGERS", "NOISY_LOGGERS", "configure_logging", "get_logger"]
