"""Kompatibilitäts-Wrapper für das fastapi_logging_manager-Paket.

Ermöglicht Imports wie::

    from fastapi_logging_manager import logger_manager, LoggerManager
"""

from .fastapi_logging_manager import LoggerManager, create_log_view_router, logger_manager

__all__ = [
    "LoggerManager",
    "logger_manager",
    "create_log_view_router",
]

