"""
HTTP response utilities for consistent API responses.
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from src.exceptions import TimelineServiceException
from src.logger import setup_logger

logger = setup_logger(__name__)


def error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> HTTPException:
    """
    Create an HTTP error response.

    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Application error code
        details: Additional error details

    Returns:
        HTTPException to raise in FastAPI handler
    """
    response_body = {"message": message}

    if error_code:
        response_body["error_code"] = error_code

    if details:
        response_body["details"] = details

    logger.warning(
        f"HTTP error {status_code}: {message}",
        extra={"error_code": error_code, "details": details},
    )

    return HTTPException(status_code=status_code, detail=response_body)


def handle_service_exception(exc: TimelineServiceException) -> HTTPException:
    """
    Convert TimelineServiceException to HTTPException.

    Args:
        exc: TimelineServiceException instance

    Returns:
        HTTPException with appropriate status code
    """
    # Map error codes to HTTP status codes
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

    return error_response(
        status_code=status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details if exc.details else None,
    )


def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a successful response body.

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Response dictionary
    """
    response = {}

    if message:
        response["message"] = message

    if data:
        response.update(data)

    return response
