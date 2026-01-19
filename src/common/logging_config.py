"""
Logging Configuration Module

Provides structured logging setup for the Stage 4 pipeline.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """
    JSON-structured log formatter for production logging.
    
    Outputs logs in JSON format for easy parsing by log aggregators.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable log formatter for development.
    """
    
    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(self):
        super().__init__(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)


def setup_logging(
    level: str = "INFO",
    structured: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: If True, output JSON logs; otherwise human-readable
        log_file: Optional file path to write logs to
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Choose formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


class LoggerWithContext:
    """
    Logger wrapper that includes context in all log messages.
    """
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any] = None):
        self._logger = logger
        self._context = context or {}
    
    def with_context(self, **kwargs) -> "LoggerWithContext":
        """Create a new logger with additional context."""
        new_context = {**self._context, **kwargs}
        return LoggerWithContext(self._logger, new_context)
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        """Internal log method that adds context."""
        if self._context:
            context_str = " | ".join(f"{k}={v}" for k, v in self._context.items())
            msg = f"[{context_str}] {msg}"
        self._logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)


def get_logger(name: str) -> LoggerWithContext:
    """
    Get a logger with context support.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        LoggerWithContext instance
    """
    return LoggerWithContext(logging.getLogger(name))
