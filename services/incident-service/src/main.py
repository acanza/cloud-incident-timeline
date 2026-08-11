"""
Incident service main entry point.
Initializes FastAPI with Phase 1 conventions.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware import Middleware
import logging

from config import settings
from logger import get_structured_logger
from context import CorrelationIdMiddleware, get_correlation_id
from utils import ValidationError
from schemas import ErrorResponseSchema

# Initialize logger
logger = get_structured_logger(
    logger_name=__name__,
    service_name=settings.service_name,
    log_level=settings.log_level
)


# Create FastAPI application
app = FastAPI(
    title="Incident Service",
    description="HTTP API for incident management",
    version="1.0.0"
)


# Register Correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)


# Exception handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handles validation errors."""
    correlation_id = get_correlation_id()
    
    logger.warning(
        f"Validation error: {exc.message}",
        extra={
            'correlation_id': correlation_id,
            'path': request.url.path,
            'method': request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.to_response().model_dump(exclude_none=True),
        headers={'X-Correlation-ID': correlation_id}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handles uncaught exceptions."""
    correlation_id = get_correlation_id()
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            'correlation_id': correlation_id,
            'path': request.url.path,
            'method': request.method,
            'exception_type': type(exc).__name__
        }
    )
    
    response = ErrorResponseSchema(
        message="Internal server error",
        details=None
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(exclude_none=True),
        headers={'X-Correlation-ID': correlation_id}
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for ALB and ECS."""
    correlation_id = get_correlation_id()
    
    logger.debug(
        "Health check requested",
        extra={'correlation_id': correlation_id}
    )
    
    return {
        "status": "ok",
        "service": settings.service_name
    }


# Startup event
@app.lifespan("startup")
async def startup_event():
    """Application startup event."""
    logger.info(
        f"{settings.service_name} started",
        extra={
            'service': settings.service_name,
            'aws_region': settings.aws_region,
            'incidents_table': settings.incidents_table_name,
            'event_bus': settings.event_bus_name
        }
    )


# Shutdown event
@app.lifespan("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info(
        f"{settings.service_name} shutting down",
        extra={'service': settings.service_name}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_config=None  # Use our custom logger
    )
