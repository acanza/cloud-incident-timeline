import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that produces structured JSON logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add custom fields if provided
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        if hasattr(record, "incident_id"):
            log_data["incident_id"] = record.incident_id

        if hasattr(record, "resource_id"):
            log_data["resource_id"] = record.resource_id

        if hasattr(record, "audit_id"):
            log_data["audit_id"] = record.audit_id

        if hasattr(record, "event_id"):
            log_data["event_id"] = record.event_id

        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type

        if hasattr(record, "actor"):
            log_data["actor"] = record.actor

        if hasattr(record, "action"):
            log_data["action"] = record.action

        if hasattr(record, "source"):
            log_data["source"] = record.source

        if hasattr(record, "service"):
            log_data["service"] = record.service

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure structured logging for a logger instance.

    Args:
        name: Logger name (typically __name__)
        log_level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    if log_level is None:
        log_level = "INFO"

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create console handler with structured formatter
    handler = logging.StreamHandler(sys.stdout)
    formatter = StructuredFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context: Any
) -> None:
    """
    Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **context: Additional fields to include in the structured log
    """
    log_method = getattr(logger, level.lower(), logger.info)

    # Create a LogRecord and attach context
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper(), logging.INFO),
        "(unknown file)",
        0,
        message,
        (),
        None,
    )

    # Attach context fields to record
    for key, value in context.items():
        setattr(record, key, value)

    log_method(record)
