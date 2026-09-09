"""
Correlation ID and request context handling.
"""

import uuid
from contextvars import ContextVar
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store correlation ID
_correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')


def generate_correlation_id() -> str:
    """
    Generates a new unique Correlation ID.
    
    Returns:
        New UUID as string
    """
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """
    Sets correlation ID for the current request context.
    
    Args:
        correlation_id: Correlation ID to set
    """
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """
    Gets correlation ID from current context.
    If it doesn't exist, generates a new one.
    
    Returns:
        Current correlation ID
    """
    current_id = _correlation_id.get()
    if not current_id:
        current_id = generate_correlation_id()
        _correlation_id.set(current_id)
    return current_id


def reset_correlation_id() -> None:
    """
    Resets correlation ID from context (useful for testing).
    """
    _correlation_id.set('')


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to handle Correlation ID.
    
    If request has 'X-Correlation-ID' header, uses it.
    If not, generates a new one.
    Injects it into context for the entire request.
    """
    
    async def dispatch(self, request, call_next):
        # Search for correlation ID in headers
        correlation_id = request.headers.get('X-Correlation-ID')
        
        if not correlation_id:
            correlation_id = generate_correlation_id()
        
        # Set in context
        set_correlation_id(correlation_id)
        
        # Pass to next layer
        response = await call_next(request)
        
        # Add correlation ID to response
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response
