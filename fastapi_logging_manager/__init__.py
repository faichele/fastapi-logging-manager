"""Public package API for fastapi_logger_manager.

Usage::

    from fastapi_logging_manager import logger_manager, LoggerManager

"""
from .logger_manager import LoggerManager, logger_manager
from .log_view_router import create_log_view_router

__all__ = [
    "LoggerManager",
    "logger_manager",
    "create_log_view_router"
]

