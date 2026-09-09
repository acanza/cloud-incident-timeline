"""
Business logic service for timeline operations.
Orchestrates validation, transformation, and persistence of timeline entries.
"""

from typing import Optional
from src.logger import setup_logger
from src.config import Config
from src.models.timeline import TimelineEntry
from src.models.event import BaseEvent
from src.models.validators import EventValidator, TimelineEntryValidator
from src.models.transformer import EventTransformer
from src.services.timeline_repository import TimelineRepository
from src.exceptions import (
    ValidationError,
    EventProcessingError,
    IdempotencyError,
    ResourceNotFoundError,
)
from src.utils import generate_timeline_entry_id, get_utc_timestamp

logger = setup_logger(__name__, Config.LOG_LEVEL)


class TimelineService:
    """
    Business logic service for timeline operations.
    
    Responsibilities:
    - Validate domain events
    - Transform events to timeline messages
    - Check idempotency
    - Persist timeline entries
    """

    def __init__(self):
        """Initialize service with repository."""
        self.repository = TimelineRepository()

    def process_event(self, raw_event: dict) -> Optional[TimelineEntry]:
        """
        Process a raw event from SQS and create a timeline entry if valid.

        Workflow:
        1. Validate raw event structure
        2. Check if event type is consumable
        3. Parse event to typed model
        4. Extract incident_id and source_event_id
        5. Check idempotency (duplicate prevention)
        6. Transform event to human-readable message
        7. Create and persist timeline entry
        8. Return created entry

        Args:
            raw_event: Raw event dictionary from SQS

        Returns:
            Created TimelineEntry if successful, None if skipped (e.g., duplicate)

        Raises:
            ValidationError: If event structure is invalid
            EventProcessingError: If processing fails
            IdempotencyError: If event already processed but with issues
        """
        try:
            # Step 1: Validate raw event structure
            is_valid, error = EventValidator.validate_raw_event(raw_event)
            if not is_valid:
                logger.warning(f"Invalid event structure: {error}")
                raise ValidationError(f"Invalid event structure: {error}")

            # Step 2: Check if consumable event type
            event_type = raw_event.get("event_type")
            if not EventValidator.is_consumable_event(event_type):
                logger.info(
                    f"Event type not consumable by this service",
                    extra={"event_type": event_type},
                )
                return None

            # Step 3: Parse event to typed model
            event = EventValidator.parse_event(raw_event)
            if not event:
                raise EventProcessingError(
                    f"Failed to parse event",
                    event_id=raw_event.get("event_id"),
                    event_type=event_type,
                )

            # Step 4: Extract incident_id and source_event_id
            incident_id = event.data.incident_id
            source_event_id = event.event_id

            if not incident_id:
                raise ValidationError(
                    "Event data missing incident_id",
                    details={"event_type": event_type},
                )

            # Step 5: Check idempotency
            already_exists = self.repository.entry_exists_by_source_event(
                incident_id, source_event_id
            )

            if already_exists:
                logger.info(
                    f"Timeline entry already exists for this event (idempotent skip)",
                    extra={
                        "incident_id": incident_id,
                        "source_event_id": source_event_id,
                    },
                )
                # Return None to indicate this was a duplicate (not an error)
                return None

            # Step 6: Transform event to human-readable message
            message = EventTransformer.transform_event(event)
            if not message:
                raise EventProcessingError(
                    f"Failed to transform event to timeline message",
                    event_id=source_event_id,
                    event_type=event_type,
                )

            # Step 7: Create timeline entry
            timeline_entry = TimelineEntry(
                incident_id=incident_id,
                timeline_entry_id=generate_timeline_entry_id(),
                created_at=get_utc_timestamp(),
                message=message,
                event_type=event_type,
                source_event_id=source_event_id,
            )

            # Validate timeline entry before persisting
            is_valid, error = TimelineEntryValidator.validate_timeline_entry(
                timeline_entry.model_dump()
            )
            if not is_valid:
                raise ValidationError(
                    f"Invalid timeline entry: {error}",
                    details={"incident_id": incident_id},
                )

            # Step 8: Persist timeline entry
            self.repository.create_entry(timeline_entry)

            logger.info(
                f"Successfully processed event and created timeline entry",
                extra={
                    "incident_id": incident_id,
                    "event_type": event_type,
                    "timeline_entry_id": timeline_entry.timeline_entry_id,
                    "correlation_id": event.correlation_id,
                },
            )

            return timeline_entry

        except (ValidationError, EventProcessingError, IdempotencyError):
            # Re-raise custom exceptions as-is
            raise

        except Exception as e:
            error_msg = f"Unexpected error processing event: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "event_type": raw_event.get("event_type"),
                    "event_id": raw_event.get("event_id"),
                    "error": str(e),
                },
            )
            raise EventProcessingError(
                error_msg,
                event_id=raw_event.get("event_id"),
                event_type=raw_event.get("event_type"),
            )

    def get_timeline(self, incident_id: str) -> list:
        """
        Retrieve the timeline for a specific incident.

        Args:
            incident_id: Incident ID

        Returns:
            List of timeline entries sorted chronologically

        Raises:
            ResourceNotFoundError: If incident has no timeline entries (optional check)
        """
        try:
            entries = self.repository.get_entries_by_incident(incident_id)

            logger.info(
                f"Retrieved timeline for incident",
                extra={
                    "incident_id": incident_id,
                    "entry_count": len(entries),
                },
            )

            return entries

        except Exception as e:
            error_msg = f"Failed to retrieve timeline: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "incident_id": incident_id,
                    "error": str(e),
                },
            )
            raise

    def create_comment_entry(
        self,
        incident_id: str,
        comment: str,
        user_id: Optional[str] = None,
    ) -> TimelineEntry:
        """
        Create a manual timeline entry from a user comment.

        Used when timeline-service exposes endpoint for adding comments.

        Args:
            incident_id: Incident ID
            comment: User's comment text
            user_id: User who created the comment

        Returns:
            Created TimelineEntry

        Raises:
            ValidationError: If inputs are invalid
            EventProcessingError: If persistence fails
        """
        try:
            # Validate inputs
            if not incident_id or not incident_id.strip():
                raise ValidationError(
                    "incident_id is required",
                    details={"field": "incident_id"},
                )

            if not comment or not comment.strip():
                raise ValidationError(
                    "comment is required",
                    details={"field": "comment"},
                )

            if len(comment) > 1000:
                raise ValidationError(
                    "comment cannot exceed 1000 characters",
                    details={"field": "comment", "max_length": 1000},
                )

            # Create timeline entry from comment
            timeline_entry = TimelineEntry(
                incident_id=incident_id,
                timeline_entry_id=generate_timeline_entry_id(),
                created_at=get_utc_timestamp(),
                message=f"Comment: {comment}",
                event_type="ManualComment",
                source_event_id=generate_timeline_entry_id(),  # Use entry ID as idempotency key
            )

            # Persist
            self.repository.create_entry(timeline_entry)

            logger.info(
                f"Created manual comment timeline entry",
                extra={
                    "incident_id": incident_id,
                    "timeline_entry_id": timeline_entry.timeline_entry_id,
                    "user_id": user_id,
                },
            )

            return timeline_entry

        except ValidationError:
            raise

        except Exception as e:
            error_msg = f"Failed to create comment entry: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "incident_id": incident_id,
                    "error": str(e),
                },
            )
            raise EventProcessingError(error_msg)
