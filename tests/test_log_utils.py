"""Tests for the shared logging module."""

from pathlib import Path

from shared.log_utils import get_logger, logger, setup_logging


def test_setup_logging_writes_message_to_file(tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"
    setup_logging(log_file)
    logger.info("hello cthulhu")
    logger.complete()

    assert "hello cthulhu" in log_file.read_text()


def test_setup_logging_uses_expected_format(tmp_path: Path) -> None:
    log_file = tmp_path / "fmt.log"
    setup_logging(log_file)
    logger.warning("formatted line")
    logger.complete()

    line = log_file.read_text().strip()
    # Format: "<iso8601-utc>Z <name> <LEVEL>: <message>"
    assert line.endswith("WARNING: formatted line")
    assert "Z " in line


def test_get_logger_returns_loguru_outside_prefect_context() -> None:
    assert get_logger() is logger


def test_log_utils_has_no_logutil_dependency() -> None:
    import shared.log_utils as module

    source = Path(module.__file__).read_text()
    assert "logutil" not in source
