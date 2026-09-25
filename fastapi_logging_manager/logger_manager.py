"""Reusable LoggerManager implementation.

This module provides a singleton-style :class:`LoggerManager` that can be used
across projects to obtain consistently configured :mod:`logging` loggers.

Environment variables (optional):

- ``FASTAPI_LOGGER_LOG_DIR`` (default: ``"logs"``)
- ``FASTAPI_LOGGER_LEVEL`` (default: ``"INFO"``)
- ``FASTAPI_LOGGER_TO_CONSOLE`` (default: ``"true"``)
- ``FASTAPI_LOGGER_TO_FILE`` (default: ``false``)
- ``FASTAPI_LOGGER_ROTATION_ENABLED`` (default: ``false``)
- ``FASTAPI_LOGGER_MAX_BYTES`` (default: ``10485760``)
- ``FASTAPI_LOGGER_BACKUP_COUNT`` (default: ``5``)
- ``FASTAPI_LOGGER_FORMAT`` (default:
  ``"%(asctime)s - %(name)s - %(levelname)s - %(message)s"``)

These provide *default* behaviour; each call to :meth:`get_logger` can
override them explicitly via arguments.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional, Union


def _get_bool_env(var_name: str, default: bool) -> bool:
    value = os.getenv(var_name)
    if value is None:
        return default
    value_lower = value.strip().lower()
    return value_lower in {"1", "true", "yes", "y", "on"}


class LoggerManager:
    """Utility class for unified logger configuration.

    Implemented as a process-wide singleton. Use the module-level
    :data:`logger_manager` instance instead of instantiating this class
    directly in most applications.
    """

    _instance: Optional["LoggerManager"] = None
    _loggers: Dict[str, logging.Logger] = {}
    _loggers_with_logfiles: Dict[str, logging.Logger] = {}

    def __new__(cls) -> "LoggerManager":
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialise default configuration from environment variables."""

        self.default_format: str = os.getenv(
            "FASTAPI_LOGGER_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        # Log directory (created lazily on first file logger request)
        self.log_directory: str = os.getenv("FASTAPI_LOGGER_LOG_DIR", "logs")

        level_env = os.getenv("FASTAPI_LOGGER_LEVEL", "INFO").upper()
        self.default_level: int = getattr(logging, level_env, logging.INFO)

        self.default_to_console: bool = _get_bool_env(
            "FASTAPI_LOGGER_TO_CONSOLE", True
        )
        self.default_to_file: bool = _get_bool_env("FASTAPI_LOGGER_TO_FILE", False)
        self.default_rotation_enabled: bool = _get_bool_env(
            "FASTAPI_LOGGER_ROTATION_ENABLED", False
        )
        self.default_max_bytes: int = self._get_positive_int_env(
            "FASTAPI_LOGGER_MAX_BYTES", 10 * 1024 * 1024
        )
        self.default_backup_count: int = self._get_non_negative_int_env(
            "FASTAPI_LOGGER_BACKUP_COUNT", 5
        )

    @staticmethod
    def _get_positive_int_env(var_name: str, default: int) -> int:
        value = os.getenv(var_name)
        if value is None:
            return default
        try:
            parsed = int(value)
        except ValueError:
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _get_non_negative_int_env(var_name: str, default: int) -> int:
        value = os.getenv(var_name)
        if value is None:
            return default
        try:
            parsed = int(value)
        except ValueError:
            return default
        return parsed if parsed >= 0 else default

    def _ensure_log_dir(self) -> None:
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory, exist_ok=True)

    @property
    def logger_names(self) -> list[str]:
        return list(self._loggers.keys())

    @property
    def loggers_with_logfiles(self) -> list[str]:
        return list(self._loggers_with_logfiles.keys())

    def get_logger(
        self,
        name: str,
        level: Union[int, str, None] = None,
        to_console: Optional[bool] = None,
        to_file: Optional[bool] = None,
        file_name: Optional[str] = None,
        format_str: Optional[str] = None,
        rotation_enabled: Optional[bool] = None,
        max_bytes: Optional[int] = None,
        backup_count: Optional[int] = None,
    ) -> logging.Logger:
        """Return a configured :class:`logging.Logger`.

        If a logger with the given ``name`` already exists, it is returned as-is
        (handlers are not recreated). Otherwise, a new logger with handlers
        configured according to the provided arguments and environment defaults
        is created.

        Parameters
        ----------
        name:
            Name of the logger (usually ``__name__``).
        level:
            Log level as :class:`int` or :class:`str`. If ``None``, the
            environment default is used.
        to_console:
            Whether to attach a :class:`logging.StreamHandler` to ``sys.stdout``.
            If ``None``, the environment default is used.
        to_file:
            Whether to attach a :class:`logging.FileHandler`. If ``None``, the
            environment default is used.
        file_name:
            Name of the log file. If omitted, it defaults to
            ``"<last-segment-of-name>.log"``.
        format_str:
            Optional logging format string. If omitted, the environment default
            is used.
        rotation_enabled:
            Enable automatic size-based rotation. If ``None``, the environment
            default is used. Manual rotation is available for every file logger.
        max_bytes:
            Maximum file size before automatic rotation. Must be positive when
            rotation is enabled.
        backup_count:
            Number of rotated files to retain.

        Returns
        -------
        logging.Logger
            Configured logger instance.
        """

        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.propagate = False

        if level is None:
            log_level = self.default_level
        elif isinstance(level, str):
            log_level = getattr(logging, level.upper(), self.default_level)
        else:
            log_level = level
        logger.setLevel(log_level)

        if format_str is None:
            format_str = self.default_format
        formatter = logging.Formatter(format_str)

        # Resolve booleans from args or fall back to defaults
        if to_console is None:
            to_console = self.default_to_console
        if to_file is None:
            to_file = self.default_to_file

        if not logger.handlers:
            if to_console:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

            if to_file:
                if file_name is None:
                    file_name = f"{name.split('.')[-1]}.log"
                self._ensure_log_dir()
                file_path = os.path.join(self.log_directory, file_name)
                if rotation_enabled is None:
                    rotation_enabled = self.default_rotation_enabled
                if max_bytes is None:
                    max_bytes = self.default_max_bytes
                if backup_count is None:
                    backup_count = self.default_backup_count
                if max_bytes < 0:
                    raise ValueError("max_bytes must not be negative")
                if rotation_enabled and max_bytes == 0:
                    raise ValueError("max_bytes must be greater than zero when rotation is enabled")
                if backup_count < 0:
                    raise ValueError("backup_count must not be negative")
                file_handler = RotatingFileHandler(
                    file_path,
                    maxBytes=max_bytes if rotation_enabled else 0,
                    backupCount=backup_count,
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

                self._loggers_with_logfiles[name] = logger

        self._loggers[name] = logger
        return logger

    def rotate_logger(self, name: str) -> bool:
        """Rotate all file handlers belonging to a registered logger.

        Returns ``True`` when at least one file handler was rotated and ``False``
        when the logger is unknown or has no file handler.
        """

        logger = self._loggers.get(name)
        if logger is None:
            return False

        rotated = False
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.doRollover()
                rotated = True
        return rotated

    def rotate_all_loggers(self) -> list[str]:
        """Manually rotate every registered logger that writes to a file."""

        rotated_loggers = [
            name for name in self._loggers_with_logfiles if self.rotate_logger(name)
        ]
        return rotated_loggers

    def rotation_status(self, name: str) -> dict[str, object]:
        """Return rotation settings for a registered logger."""

        logger = self._loggers.get(name)
        if logger is None:
            raise KeyError(f"Unknown logger: {name}")

        handlers = [
            handler
            for handler in logger.handlers
            if isinstance(handler, RotatingFileHandler)
        ]
        if not handlers:
            return {"logger": name, "enabled": False, "handlers": []}

        return {
            "logger": name,
            "enabled": any(handler.maxBytes > 0 for handler in handlers),
            "handlers": [
                {
                    "file": handler.baseFilename,
                    "max_bytes": handler.maxBytes,
                    "backup_count": handler.backupCount,
                }
                for handler in handlers
            ],
        }

    def configure_all_loggers(self, level: Union[int, str] = logging.INFO) -> None:
        """Configure the root logger level for the current process."""
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        logging.basicConfig(level=level)

    # Convenience helpers mirroring the original project-specific API ------------

    def get_app_logger(self) -> logging.Logger:
        """Return a predefined application logger.

        Uses the name ``"app"`` and always logs to both console and file
        (``app.log``), irrespective of the environment defaults.
        """

        return self.get_logger(
            "app",
            to_console=True,
            to_file=True,
            file_name="app.log",
        )

    def get_db_logger(self) -> logging.Logger:
        """Return a predefined database logger (``db.log``)."""

        return self.get_logger(
            "db",
            to_console=True,
            to_file=True,
            file_name="database.log",
        )

    def get_api_logger(self) -> logging.Logger:
        """Return a predefined API logger (``api.log``)."""

        return self.get_logger(
            "api",
            to_console=True,
            to_file=True,
            file_name="api.log",
        )

    def get_task_logger(self, name: str, to_file: bool = True) -> logging.Logger:
        """Return a logger for background tasks.

        Parameters
        ----------
        name:
            Logical task name, used to form the log file name
            ``"task_<name>.log"``.
        to_file:
            Whether to log to a dedicated file in addition to the console.
        """

        return self.get_logger(
            "task",
            to_console=True,
            to_file=to_file,
            file_name=f"task_{name}.log",
        )


# Public singleton instance -----------------------------------------------------

logger_manager = LoggerManager()
