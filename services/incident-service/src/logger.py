"""
Structured JSON logging configuration.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional
from pythonjsonlogger import jsonlogger


def get_structured_logger(
    logger_name: str,
    service_name: str = "incident-service",
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Creates a logger with structured JSON output.
    
    Args:
        logger_name: Logger name (typically __name__)
        service_name: Service name for logging context
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configured with JSON format
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Handler to stdout with JSON format
    handler = logging.StreamHandler(sys.stdout)
    
    # Custom JSON formatter
    json_formatter = JsonFormatterCustom(service_name=service_name)
    handler.setFormatter(json_formatter)
    
    logger.addHandler(handler)
    
    return logger


class JsonFormatterCustom(jsonlogger.JsonFormatter):
    """
    Custom formatter for structured JSON logs.
    Adds timestamp, service name, and other contextual fields.
    """
    
    def __init__(self, service_name: str = "incident-service", *args, **kwargs):
        self.service_name = service_name
        super().__init__(*args, **kwargs)
    
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict):
        """Adds custom fields to log record."""
        
        # Timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Standard logging information
        log_record['level'] = record.levelname
        log_record['service'] = self.service_name
        log_record['message'] = record.getMessage()
        log_record['logger'] = record.name
        
        # Add exception information if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        # Preserve custom fields from message_dict
        # (e.g., correlation_id, event_id, incident_id)
        if message_dict:
            log_record.update(message_dict)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    correlation_id: Optional[str] = None,
    event_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    extra_fields: Optional[dict] = None
) -> None:
    """
    Logs a message with additional context.
    
    Args:
        logger: Logger instance
        level: Log level ('info', 'warning', 'error', 'debug')
        message: Message to log
        correlation_id: Optional correlation ID
        event_id: Optional event ID
        incident_id: Optional incident ID
        extra_fields: Additional fields dictionary
    """
    context = {}
    
    if correlation_id:
        context['correlation_id'] = correlation_id
    if event_id:
        context['event_id'] = event_id
    if incident_id:
        context['incident_id'] = incident_id
    if extra_fields:
        context.update(extra_fields)
    
    # Use the corresponding log method
    log_method = getattr(logger, level.lower(), logger.info)
    
    if context:
        # Pass context as extra dictionary
        log_method(message, extra=context)
    else:
        log_method(message)
