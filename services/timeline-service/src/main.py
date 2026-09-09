"""
FastAPI application initialization and configuration.
Sets up the HTTP API and optionally the SQS consumer.
"""

import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.config import Config
from src.logger import setup_logger
from src.exceptions import TimelineServiceException
from src.routes import health, timeline

logger = setup_logger(__name__, Config.LOG_LEVEL)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Sets up:
    - Application metadata
    - Routes (health, timeline)
    - Exception handlers
    - Logging

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Timeline Service",
        description="Event-driven microservice for incident timelines",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Validate configuration on startup
    try:
        Config.validate()
        logger.info(
            f"Configuration validated successfully",
            extra={
                "service": Config.SERVICE_NAME,
                "region": Config.AWS_REGION,
                "log_level": Config.LOG_LEVEL,
            },
        )
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)

    # Register route modules
    app.include_router(health.router)
    app.include_router(timeline.router)

    # Exception handler for custom TimelineServiceException
    @app.exception_handler(TimelineServiceException)
    async def timeline_exception_handler(
        request: Request,
        exc: TimelineServiceException,
    ):
        """
        Handle TimelineServiceException globally.

        Converts service exceptions to appropriate HTTP responses.
        """
        status_code_map = {
            "VALIDATION_ERROR": 400,
            "NOT_FOUND": 404,
            "IDEMPOTENCY_ERROR": 409,
            "EVENT_PROCESSING_ERROR": 500,
            "DYNAMODB_ERROR": 500,
            "SQS_ERROR": 500,
            "EVENTBUS_ERROR": 500,
            "SERVICE_ERROR": 500,
        }

        status_code = status_code_map.get(exc.error_code, 500)

        response_body = {
            "message": exc.message,
            "error_code": exc.error_code,
        }

        if exc.details:
            response_body["details"] = exc.details

        logger.error(
            f"Service exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "status_code": status_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status_code,
            content=response_body,
        )

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(
            f"Timeline service starting up",
            extra={
                "service": Config.SERVICE_NAME,
                "port": Config.PORT,
            },
        )

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info(
            f"Timeline service shutting down",
            extra={"service": Config.SERVICE_NAME},
        )

    return app


# Create the FastAPI application
app = create_app()


# For local development with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=Config.PORT,
        reload=False,
        log_level=Config.LOG_LEVEL.lower(),
    )
