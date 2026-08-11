"""
Configuración de logging estructurado en formato JSON.
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
    Crea un logger con salida en formato JSON estructurado.
    
    Args:
        logger_name: Nombre del logger (típicamente __name__)
        service_name: Nombre del servicio para el contexto de logs
        log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado con formato JSON
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Eliminar handlers existentes para evitar duplicados
    logger.handlers.clear()
    
    # Handler a stdout con formato JSON
    handler = logging.StreamHandler(sys.stdout)
    
    # Formatter JSON personalizado
    json_formatter = JsonFormatterCustom(service_name=service_name)
    handler.setFormatter(json_formatter)
    
    logger.addHandler(handler)
    
    return logger


class JsonFormatterCustom(jsonlogger.JsonFormatter):
    """
    Formatter personalizado para logs JSON estructurados.
    Añade timestamp, service name, y otros campos contextuales.
    """
    
    def __init__(self, service_name: str = "incident-service", *args, **kwargs):
        self.service_name = service_name
        super().__init__(*args, **kwargs)
    
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict):
        """Añade campos personalizados al registro de log."""
        
        # Timestamp en ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Información estándar de logging
        log_record['level'] = record.levelname
        log_record['service'] = self.service_name
        log_record['message'] = record.getMessage()
        log_record['logger'] = record.name
        
        # Añadir información de exception si la hay
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        # Preservar campos personalizados que vengan en message_dict
        # (ej: correlation_id, event_id, incident_id)
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
    Registra un mensaje con contexto adicional.
    
    Args:
        logger: Logger instance
        level: Nivel de log ('info', 'warning', 'error', 'debug')
        message: Mensaje a registrar
        correlation_id: ID de correlación opcional
        event_id: ID de evento opcional
        incident_id: ID de incidente opcional
        extra_fields: Diccionario adicional de campos
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
    
    # Usa el método de log correspondiente
    log_method = getattr(logger, level.lower(), logger.info)
    
    if context:
        # Pasar contexto como diccionario extra
        log_method(message, extra=context)
    else:
        log_method(message)
