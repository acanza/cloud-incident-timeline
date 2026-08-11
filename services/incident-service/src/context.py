"""
Manejo de Correlation ID y contexto de solicitud.
"""

import uuid
from contextvars import ContextVar
from typing import Optional

# Variable contextual para almacenar el correlation ID
_correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')


def generate_correlation_id() -> str:
    """
    Genera un nuevo Correlation ID único.
    
    Returns:
        Nuevo UUID como string
    """
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """
    Establece el Correlation ID para el contexto actual de la solicitud.
    
    Args:
        correlation_id: ID de correlación a establecer
    """
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """
    Obtiene el Correlation ID del contexto actual.
    Si no existe, genera uno nuevo.
    
    Returns:
        Correlation ID actual
    """
    current_id = _correlation_id.get()
    if not current_id:
        current_id = generate_correlation_id()
        _correlation_id.set(current_id)
    return current_id


def reset_correlation_id() -> None:
    """
    Resetea el Correlation ID del contexto (útil para testing).
    """
    _correlation_id.set('')


class CorrelationIdMiddleware:
    """
    Middleware de FastAPI para manejar Correlation ID.
    
    Si el request trae un header 'X-Correlation-ID', lo usa.
    Si no, genera uno nuevo.
    Lo inyecta en el contexto para toda la solicitud.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request, call_next):
        # Buscar correlation ID en headers
        correlation_id = request.headers.get('X-Correlation-ID')
        
        if not correlation_id:
            correlation_id = generate_correlation_id()
        
        # Establecer en contexto
        set_correlation_id(correlation_id)
        
        # Pasar a la siguiente capa
        response = await call_next(request)
        
        # Añadir correlation ID a la respuesta
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response
