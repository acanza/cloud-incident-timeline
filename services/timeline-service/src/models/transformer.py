"""
Event transformers convert domain events to human-readable timeline messages.
"""

from typing import Optional
from src.logger import setup_logger
from src.models.event import (
    BaseEvent,
    IncidentCreatedEvent,
    IncidentStatusChangedEvent,
    IncidentSeverityChangedEvent,
    IncidentResolvedEvent,
    TimelineCommentAddedEvent,
)

logger = setup_logger(__name__)


class EventTransformer:
    """Transforms domain events into human-readable timeline messages."""

    @staticmethod
    def transform_incident_created(event: IncidentCreatedEvent) -> str:
        """
        Transform IncidentCreated event to timeline message.

        Example output:
        "Incident created with HIGH severity and OPEN status."
        """
        severity = event.data.severity
        status = event.data.status
        return f"Incident created with {severity} severity and {status} status."

    @staticmethod
    def transform_status_changed(event: IncidentStatusChangedEvent) -> str:
        """
        Transform IncidentStatusChanged event to timeline message.

        Example output:
        "Status changed from OPEN to INVESTIGATING."
        """
        prev_status = event.data.previous_status
        new_status = event.data.new_status
        return f"Status changed from {prev_status} to {new_status}."

    @staticmethod
    def transform_severity_changed(event: IncidentSeverityChangedEvent) -> str:
        """
        Transform IncidentSeverityChanged event to timeline message.

        Example output:
        "Severity changed from MEDIUM to HIGH."
        """
        prev_severity = event.data.previous_severity
        new_severity = event.data.new_severity
        return f"Severity changed from {prev_severity} to {new_severity}."

    @staticmethod
    def transform_incident_resolved(event: IncidentResolvedEvent) -> str:
        """
        Transform IncidentResolved event to timeline message.

        If resolution_summary is present:
        "Incident resolved. Resolution: Database indexes were optimized."

        If resolution_summary is missing:
        "Incident resolved."
        """
        base_message = "Incident resolved"

        resolution = event.data.resolution_summary
        if resolution and resolution.strip():
            return f"{base_message}. Resolution: {resolution}"

        return f"{base_message}."

    @staticmethod
    def transform_timeline_comment_added(event: TimelineCommentAddedEvent) -> str:
        """
        Transform TimelineCommentAdded event to timeline message.

        Example output:
        "Comment: Backend team is investigating database metrics"
        """
        comment = event.data.comment
        return f"Comment: {comment}"

    @staticmethod
    def transform_event(event: BaseEvent) -> Optional[str]:
        """
        Transform any domain event to a human-readable message.

        Args:
            event: Domain event

        Returns:
            Human-readable message or None if event type is not handled
        """
        try:
            if isinstance(event, IncidentCreatedEvent):
                return EventTransformer.transform_incident_created(event)

            elif isinstance(event, IncidentStatusChangedEvent):
                return EventTransformer.transform_status_changed(event)

            elif isinstance(event, IncidentSeverityChangedEvent):
                return EventTransformer.transform_severity_changed(event)

            elif isinstance(event, IncidentResolvedEvent):
                return EventTransformer.transform_incident_resolved(event)

            elif isinstance(event, TimelineCommentAddedEvent):
                return EventTransformer.transform_timeline_comment_added(event)

            else:
                logger.warning(
                    f"No transformer for event type: {event.event_type}",
                    extra={"event_id": event.event_id},
                )
                return None

        except Exception as e:
            logger.error(
                f"Failed to transform event: {str(e)}",
                extra={
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                },
            )
            return None
