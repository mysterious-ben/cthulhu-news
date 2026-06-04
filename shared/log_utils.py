"""Shared logging for the db and web apps.

This module is the single place that configures loguru. Other modules should
import ``logger`` from here (not from ``loguru`` directly) so logging stays
centralized and the backend can be swapped in one place.
"""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

__all__ = ["get_logger", "logger", "setup_logging"]

DEFAULT_FORMAT = "{time:YYYY-MM-DDTHH:mm:ss.SSS!UTC}Z {name} {level}: {message}"


def setup_logging(
    file_path: str | Path,
    *,
    level: str | int = "DEBUG",
    fmt: str = DEFAULT_FORMAT,
    rotation: str = "20 MB",
    retention: int = 1,
    enqueue: bool = False,
) -> None:
    """Configure loguru with a stderr sink and a rotating file sink."""

    logger.remove()
    logger.add(sys.stderr, format=fmt, level=level, enqueue=enqueue)
    logger.add(
        file_path,
        format=fmt,
        level=level,
        rotation=rotation,
        retention=retention,
        enqueue=enqueue,
    )


def get_logger() -> Any:
    """Get the appropriate logger based on context.

    Returns the Prefect run logger inside a flow/task context, otherwise the
    loguru logger. The Prefect import is lazy so importing this module does not
    require Prefect.
    """

    try:
        from prefect.logging import get_run_logger

        return get_run_logger()
    except (RuntimeError, ImportError):
        # Not in a flow/task context (or Prefect not installed): use loguru.
        return logger
