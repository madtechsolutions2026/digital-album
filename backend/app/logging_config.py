"""
Logging configuration for the application.

This module sets up structured logging with JSON formatting for production
and human-readable formatting for development. It includes request ID tracking
and configurable log levels.
"""

import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger

from app.config import get_settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that includes additional fields.
    
    Formats log records as JSON with timestamp, level, logger name, message,
    and any additional fields like request_id.
    """
    
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        """
        Add custom fields to the log record.
        
        Args:
            log_record: Dictionary that will be serialized to JSON
            record: Original logging.LogRecord
            message_dict: Dictionary of additional fields from the log call
        """
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = record.created
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name (module path)
        log_record['name'] = record.name
        
        # Add request_id if present in the record
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # Add function and line number for debugging
        if record.levelno >= logging.WARNING:
            log_record['function'] = record.funcName
            log_record['line'] = record.lineno
            log_record['pathname'] = record.pathname


class RequestIdFilter(logging.Filter):
    """
    Logging filter that adds request_id to log records.
    
    This filter can be used to inject a request_id into all log records
    for request tracing across services.
    """
    
    def __init__(self, request_id: Optional[str] = None):
        """
        Initialize the filter with an optional request_id.
        
        Args:
            request_id: Optional request ID to add to all logs
        """
        super().__init__()
        self.request_id = request_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request_id to the log record if not already present.
        
        Args:
            record: The log record to filter
            
        Returns:
            True (always pass the record through)
        """
        if not hasattr(record, 'request_id'):
            record.request_id = self.request_id or 'N/A'
        return True


def setup_logging() -> None:
    """
    Configure application logging based on settings.
    
    Sets up:
    - JSON formatting for structured logs
    - Configurable log level from settings
    - Request ID tracking
    - Output to stdout for container-friendly logging
    """
    settings = get_settings()
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler that writes to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # Use JSON formatter for structured logging
    if not settings.DEBUG:
        # Production: JSON formatted logs
        formatter = CustomJsonFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={
                'levelname': 'level',
                'name': 'logger',
            }
        )
    else:
        # Development: Human-readable logs
        # Make request_id optional with a default value
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Configure third-party loggers to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # In debug mode, enable SQLAlchemy query logging
    if settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def add_request_id_to_logger(logger: logging.Logger, request_id: str) -> None:
    """
    Add a request ID filter to a logger instance.
    
    This allows all logs from this logger to include the request ID
    for correlation across log entries.
    
    Args:
        logger: Logger instance to add the filter to
        request_id: Request ID to include in logs
    """
    # Remove any existing RequestIdFilter
    for filter_obj in logger.filters[:]:
        if isinstance(filter_obj, RequestIdFilter):
            logger.removeFilter(filter_obj)
    
    # Add new filter with the request ID
    logger.addFilter(RequestIdFilter(request_id))


# Initialize logging when module is imported
try:
    setup_logging()
except Exception as e:
    # Fallback to basic logging if setup fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    logging.error(f"Failed to setup logging: {e}")
