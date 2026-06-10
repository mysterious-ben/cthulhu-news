"""Shared logging for the db and web apps.

This module is the single place that configures loguru. Other modules should
import ``logger`` from here (not from ``loguru`` directly) so logging stays
centralized and the backend can be swapped in one place.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger as _loguru_logger

if TYPE_CHECKING:
    from loguru import Logger

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

    _loguru_logger.remove()
    _loguru_logger.add(sys.stderr, format=fmt, level=level, enqueue=enqueue)
    _loguru_logger.add(
        file_path,
        format=fmt,
        level=level,
        rotation=rotation,
        retention=retention,
        enqueue=enqueue,
    )


def _get_logger() -> logging.Logger | Logger:
    """Get the appropriate logger based on context.

    Returns the Prefect run logger inside a flow/task context, otherwise the
    loguru logger. The Prefect import is lazy so importing this module does not
    require Prefect.
    """

    try:
        from prefect.logging import get_run_logger

        return get_run_logger()  # type: ignore[return]
    except (RuntimeError, ImportError):
        # Not in a flow/task context (or Prefect not installed): use loguru.
        return _loguru_logger


class _LoggerProxy:
    """Picklable stand-in that resolves the real logger on every access.

    Prefect submits scheduled flow runs by cloudpickling the flow (and every
    global it closes over) for execution in a subprocess. Binding the loguru
    logger to a module global is therefore unsafe: its rotating file sink owns
    an append-mode file handle, and cloudpickle cannot serialize an open file
    (``PicklingError: Cannot pickle files that are not opened for reading: a``).

    ``__slots__ = ()`` makes instances stateless, so a captured proxy pickles to
    just a reference to this class — never the loguru object or its open file.
    Every attribute access is forwarded to :func:`_get_logger`, so logging
    routes to the Prefect run logger inside a flow/task and to loguru elsewhere.
    """

    __slots__ = ()  # stateless: pickles as a bare class reference, no open file

    def __getattr__(self, name: str) -> Any:
        return getattr(_get_logger(), name)


# Import this shared proxy as ``logger`` instead of binding ``_get_logger()`` to a
# module global, so a captured flow never drags loguru's open file into a pickle.
logger = _LoggerProxy()
