from __future__ import annotations

from importlib.resources import files
from logging.handlers import RotatingFileHandler

from fastapi_logging_manager import logger_manager

def test_template_is_packaged() -> None:
    path = files("fastapi_logging_manager").joinpath("templates", "log_viewer.html")
    assert path.is_file(), "Expected templates/log_viewer.html to be packaged inside fastapi_logging_manager"
    # tiny sanity check: file isn't empty
    assert path.read_text(encoding="utf-8").strip().startswith("<!DOCTYPE html>")


def _remove_logger(name: str) -> None:
    logger = logger_manager._loggers.pop(name)
    logger_manager._loggers_with_logfiles.pop(name, None)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_automatic_log_rotation(tmp_path) -> None:
    name = "test.automatic_rotation"
    original_directory = logger_manager.log_directory
    logger_manager.log_directory = str(tmp_path)
    try:
        logger = logger_manager.get_logger(
            name,
            to_console=False,
            to_file=True,
            file_name="automatic.log",
            rotation_enabled=True,
            max_bytes=32,
            backup_count=2,
        )
        assert isinstance(logger.handlers[0], RotatingFileHandler)
        logger.info("x" * 100)
        logger.handlers[0].flush()

        assert (tmp_path / "automatic.log.1").exists()
    finally:
        _remove_logger(name)
        logger_manager.log_directory = original_directory


def test_manual_log_rotation(tmp_path) -> None:
    name = "test.manual_rotation"
    original_directory = logger_manager.log_directory
    logger_manager.log_directory = str(tmp_path)
    try:
        logger = logger_manager.get_logger(
            name,
            to_console=False,
            to_file=True,
            file_name="manual.log",
            rotation_enabled=False,
            backup_count=2,
        )
        logger.info("before rotation")
        logger.handlers[0].flush()

        assert logger_manager.rotate_logger(name) is True
        assert (tmp_path / "manual.log.1").exists()
        assert logger_manager.rotation_status(name)["enabled"] is False
    finally:
        _remove_logger(name)
        logger_manager.log_directory = original_directory
