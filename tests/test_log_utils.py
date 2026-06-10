"""Tests for the shared logging module."""

from pathlib import Path

import cloudpickle

from shared.log_utils import _get_logger, setup_logging
from shared.log_utils import logger as proxy_logger

logger = _get_logger()


def test_setup_logging_writes_message_to_file(tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"
    setup_logging(log_file)
    logger.info("hello cthulhu")

    assert "hello cthulhu" in log_file.read_text()


def test_setup_logging_uses_expected_format(tmp_path: Path) -> None:
    log_file = tmp_path / "fmt.log"
    setup_logging(log_file)
    logger.warning("formatted line")

    line = log_file.read_text().strip()
    # Format: "<iso8601-utc>Z <name> <LEVEL>: <message>"
    assert line.endswith("WARNING: formatted line")
    assert "Z " in line


def test_get_logger_returns_loguru_outside_prefect_context() -> None:
    assert _get_logger() is logger


def test_log_utils_has_no_logutil_dependency() -> None:
    import shared.log_utils as module

    source = Path(module.__file__).read_text()
    assert "logutil" not in source


def test_proxy_logger_forwards_to_loguru(tmp_path: Path) -> None:
    log_file = tmp_path / "proxy.log"
    setup_logging(log_file)
    proxy_logger.info("via proxy")

    assert "via proxy" in log_file.read_text()


def test_proxy_logger_is_cloudpicklable(tmp_path: Path) -> None:
    # Regression: Prefect cloudpickles a scheduled flow and the globals it closes
    # over. A module-global loguru logger drags its open append-mode file sink
    # into the pickle and crashes the flow run. The proxy must pickle to nothing.
    setup_logging(tmp_path / "sink.log")  # ensure an open file sink exists
    cloudpickle.loads(cloudpickle.dumps(proxy_logger))


def test_flow_like_closure_over_proxy_logger_pickles(tmp_path: Path) -> None:
    # Simulate a @flow/@task function (pickled *by value*) that logs via the
    # shared proxy: it must serialize without touching the open log file.
    setup_logging(tmp_path / "flow.log")

    def flow_fn() -> str:
        proxy_logger.info("inside flow")
        return "ok"

    flow_fn.__module__ = "__main__"  # force cloudpickle to pickle by value
    restored = cloudpickle.loads(cloudpickle.dumps(flow_fn))
    assert restored() == "ok"
