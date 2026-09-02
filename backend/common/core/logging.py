"""Logging setup using the standard library."""

import logging

from common.core.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)
