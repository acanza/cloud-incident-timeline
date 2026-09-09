"""
Validators for audit events and records.
"""

from typing import Any, Dict, Optional
from pydantic import ValidationError as PydanticValidationError
from src.constants import (
    CONSUMABLE_EVENT_TYPES,
    EVENT_ENVELOPE_VERSION,
    EVENT_TYPE_INCIDENT_CREATED,
    EVENT_TYPE_INCIDENT_STATUS_CHANGED,
    EVENT_TYPE_INCIDENT_SEVERITY_CHANGED,
    EVENT_TYPE_INCIDENT_RESOLVED,
)
from src.models.event import (
    BaseEvent,
    IncidentCreatedEvent,
    IncidentStatusChangedEvent,
    IncidentSeverityChangedEvent,
    IncidentResolvedEvent,
)
from src.exceptions import ValidationError


class AuditEventValidator:
    """Validator for incoming domain events."""

    @staticmethod
    def validate_raw_event(event_data: Dict[str, Any]) -> None:
        """
        Validate raw event structure.

        Args:
            event_data: Raw event dictionary

        Raises:
            ValidationError: If event structure is invalid
        """
        required_fields = [
            "version",
            "event_id",
            "event_type",
            "source",
            "occurred_at",
            "correlation_id",
            "actor",
            "data",
        ]

        missing_fields = [field for field in required_fields if field not in event_data]
        if missing_fields:
            raise ValidationError(
                f"Event missing required fields: {', '.join(missing_fields)}",
                details={"missing_fields": missing_fields},
            )

        # Validate version
        if event_data.get("version") != EVENT_ENVELOPE_VERSION:
            raise ValidationError(
                f"Unsupported event version: {event_data.get('version')}. "
                f"Expected: {EVENT_ENVELOPE_VERSION}",
                details={"version": event_data.get("version")},
            )

    @staticmethod
    def is_consumable_event(event_type: str) -> bool:
        """
        Check if event type is consumable by audit worker.

        Args:
            event_type: Event type string

        Returns:
            True if event should be processed, False otherwise
        """
        return event_type in CONSUMABLE_EVENT_TYPES

    @staticmethod
    def parse_event(event_data: Dict[str, Any]) -> BaseEvent:
        """
        Parse raw event to typed event model.

        Args:
            event_data: Raw event dictionary

        Returns:
            Typed event model

        Raises:
            ValidationError: If event structure is invalid
        """
        try:
            event_type = event_data.get("event_type")

            # Route to appropriate event class based on type
            if event_type == EVENT_TYPE_INCIDENT_CREATED:
                return IncidentCreatedEvent(**event_data)
            elif event_type == EVENT_TYPE_INCIDENT_STATUS_CHANGED:
                return IncidentStatusChangedEvent(**event_data)
            elif event_type == EVENT_TYPE_INCIDENT_SEVERITY_CHANGED:
                return IncidentSeverityChangedEvent(**event_data)
            elif event_type == EVENT_TYPE_INCIDENT_RESOLVED:
                return IncidentResolvedEvent(**event_data)
            else:
                # Fallback to base event for unknown types
                return BaseEvent(**event_data)

        except PydanticValidationError as e:
            error_details = {
                "event_type": event_data.get("event_type"),
                "validation_errors": str(e),
            }
            raise ValidationError(
                f"Failed to parse event: {str(e)}",
                details=error_details,
            )
        except Exception as e:
            raise ValidationError(
                f"Unexpected error parsing event: {str(e)}",
                details={"error": str(e)},
            )


class AuditRecordValidator:
    """Validator for audit records."""

    @staticmethod
    def validate_resource_id(resource_id: Optional[str]) -> None:
        """
        Validate resource ID.

        Args:
            resource_id: Resource ID to validate

        Raises:
            ValidationError: If resource ID is invalid
        """
        if not resource_id or not isinstance(resource_id, str):
            raise ValidationError(
                "resource_id is required and must be a string",
                details={"resource_id": resource_id},
            )

        if len(resource_id.strip()) == 0:
            raise ValidationError(
                "resource_id cannot be empty",
                details={"resource_id": resource_id},
            )

    @staticmethod
    def validate_action(action: Optional[str]) -> None:
        """
        Validate action.

        Args:
            action: Action to validate

        Raises:
            ValidationError: If action is invalid
        """
        if not action or not isinstance(action, str):
            raise ValidationError(
                "action is required and must be a string",
                details={"action": action},
            )

        if len(action.strip()) == 0:
            raise ValidationError(
                "action cannot be empty",
                details={"action": action},
            )

    @staticmethod
    def validate_source_event_id(source_event_id: Optional[str]) -> None:
        """
        Validate source event ID.

        Args:
            source_event_id: Source event ID to validate

        Raises:
            ValidationError: If source event ID is invalid
        """
        if not source_event_id or not isinstance(source_event_id, str):
            raise ValidationError(
                "source_event_id is required and must be a string",
                details={"source_event_id": source_event_id},
            )

        if len(source_event_id.strip()) == 0:
            raise ValidationError(
                "source_event_id cannot be empty",
                details={"source_event_id": source_event_id},
            )
