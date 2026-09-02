"""
Validators for events and timeline entries.
"""

import json
from typing import Optional, Tuple
from src.logger import setup_logger
from src.constants import CONSUMABLE_EVENT_TYPES, EVENT_ENVELOPE_VERSION
from src.models.event import (
    BaseEvent,
    IncidentCreatedEvent,
    IncidentStatusChangedEvent,
    IncidentSeverityChangedEvent,
    IncidentResolvedEvent,
    TimelineCommentAddedEvent,
)

logger = setup_logger(__name__)


class EventValidator:
    """Validates domain events from SQS."""

    @staticmethod
    def validate_raw_event(raw_event: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate raw event structure before parsing.

        Args:
            raw_event: Raw event dictionary from SQS

        Returns:
            Tuple of (is_valid, error_message)
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

        for field in required_fields:
            if field not in raw_event:
                error = f"Missing required event field: {field}"
                logger.warning(error)
                return False, error

        # Validate event version
        if raw_event.get("version") != EVENT_ENVELOPE_VERSION:
            error = f"Unsupported event version: {raw_event.get('version')}"
            logger.warning(error)
            return False, error

        return True, None

    @staticmethod
    def is_consumable_event(event_type: str) -> bool:
        """
        Check if this service should consume the given event type.

        Args:
            event_type: Event type string

        Returns:
            True if this service consumes this event type
        """
        return event_type in CONSUMABLE_EVENT_TYPES

    @staticmethod
    def parse_event(raw_event: dict) -> Optional[BaseEvent]:
        """
        Parse raw event dictionary into typed event model.

        Args:
            raw_event: Raw event from SQS

        Returns:
            Typed event model or None if parsing fails
        """
        try:
            event_type = raw_event.get("event_type")

            if event_type == "IncidentCreated":
                return IncidentCreatedEvent(**raw_event)
            elif event_type == "IncidentStatusChanged":
                return IncidentStatusChangedEvent(**raw_event)
            elif event_type == "IncidentSeverityChanged":
                return IncidentSeverityChangedEvent(**raw_event)
            elif event_type == "IncidentResolved":
                return IncidentResolvedEvent(**raw_event)
            elif event_type == "TimelineCommentAdded":
                return TimelineCommentAddedEvent(**raw_event)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return None

        except Exception as e:
            logger.error(
                f"Failed to parse event: {str(e)}",
                extra={
                    "event_type": raw_event.get("event_type"),
                    "event_id": raw_event.get("event_id"),
                },
            )
            return None


class TimelineEntryValidator:
    """Validates timeline entries before persisting."""

    @staticmethod
    def validate_timeline_entry(entry_dict: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate timeline entry has required fields.

        Args:
            entry_dict: Timeline entry dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = [
            "incident_id",
            "timeline_entry_id",
            "created_at",
            "message",
            "event_type",
            "source_event_id",
        ]

        for field in required_fields:
            if field not in entry_dict or not entry_dict[field]:
                error = f"Timeline entry missing required field: {field}"
                logger.warning(error)
                return False, error

        # Validate incident_id format (basic check)
        if not isinstance(entry_dict.get("incident_id"), str):
            return False, "incident_id must be a string"

        # Validate message is not empty
        message = entry_dict.get("message", "").strip()
        if not message:
            return False, "message cannot be empty"

        if len(message) > 1000:
            return False, "message cannot exceed 1000 characters"

        return True, None

    @staticmethod
    def validate_idempotency_key(source_event_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate source event ID format for idempotency.

        Args:
            source_event_id: Source event ID

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not source_event_id or not isinstance(source_event_id, str):
            return False, "source_event_id must be a non-empty string"

        if len(source_event_id) > 255:
            return False, "source_event_id cannot exceed 255 characters"

        return True, None
