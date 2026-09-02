"""
Custom exceptions and error handling for timeline service.
"""

from typing import Optional, Dict, Any


class TimelineServiceException(Exception):
    """Base exception for timeline service."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or "SERVICE_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to error response dictionary."""
        response = {
            "message": self.message,
            "error_code": self.error_code,
        }
        if self.details:
            response["details"] = self.details
        return response


class ValidationError(TimelineServiceException):
    """Raised when validation of input fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class EventProcessingError(TimelineServiceException):
    """Raised when event processing fails."""

    def __init__(
        self,
        message: str,
        event_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ):
        details = {}
        if event_id:
            details["event_id"] = event_id
        if event_type:
            details["event_type"] = event_type

        super().__init__(
            message, error_code="EVENT_PROCESSING_ERROR", details=details
        )


class DynamoDBError(TimelineServiceException):
    """Raised when DynamoDB operation fails."""

    def __init__(
        self,
        message: str,
        resource: Optional[str] = None,
    ):
        details = {}
        if resource:
            details["resource"] = resource

        super().__init__(message, error_code="DYNAMODB_ERROR", details=details)


class SQSError(TimelineServiceException):
    """Raised when SQS operation fails."""

    def __init__(
        self,
        message: str,
        queue_url: Optional[str] = None,
    ):
        details = {}
        if queue_url:
            details["queue"] = queue_url.split("/")[-1]  # Extract queue name

        super().__init__(message, error_code="SQS_ERROR", details=details)


class ResourceNotFoundError(TimelineServiceException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
    ):
        message = f"{resource_type} not found: {resource_id}"
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
        }
        super().__init__(message, error_code="NOT_FOUND", details=details)


class IdempotencyError(TimelineServiceException):
    """Raised when idempotency check fails."""

    def __init__(
        self,
        message: str,
        source_event_id: Optional[str] = None,
    ):
        details = {}
        if source_event_id:
            details["source_event_id"] = source_event_id

        super().__init__(
            message, error_code="IDEMPOTENCY_ERROR", details=details
        )


class EventBusError(TimelineServiceException):
    """Raised when EventBridge operation fails."""

    def __init__(
        self,
        message: str,
        event_bus_name: Optional[str] = None,
    ):
        details = {}
        if event_bus_name:
            details["event_bus"] = event_bus_name

        super().__init__(message, error_code="EVENTBUS_ERROR", details=details)
