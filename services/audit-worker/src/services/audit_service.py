"""
Business logic for processing audit events.
Orchestrates event validation, transformation, and persistence.
"""

from typing import Optional, List, Dict, Any
from src.logger import setup_logger, log_with_context
from src.config import Config
from src.models.audit import AuditRecord
from src.models.event import BaseEvent
from src.models.validators import AuditEventValidator, AuditRecordValidator
from src.models.transformer import AuditTransformer
from src.services.audit_repository import AuditRepository
from src.exceptions import ValidationError, EventProcessingError, IdempotencyError

logger = setup_logger(__name__, Config.LOG_LEVEL)


class AuditService:
    """
    Business logic service for audit processing.
    
    Orchestrates the full pipeline:
    1. Validate event structure
    2. Check if event type is consumable
    3. Parse to typed model
    4. Extract resource_id and source_event_id
    5. Check idempotency
    6. Transform to audit record details
    7. Create AuditRecord
    8. Validate record
    9. Persist via repository
    """

    def __init__(self):
        """Initialize service with repository."""
        self.repository = AuditRepository()

    def process_event(self, event_data: Dict[str, Any]) -> Optional[AuditRecord]:
        """
        Process a domain event and create an audit record if applicable.

        Pipeline:
        - Validate event structure
        - Check if event type is consumable
        - Parse to typed event
        - Extract incident_id (resource_id) and event_id
        - Check idempotency (prevent duplicates)
        - Transform event to audit details
        - Create and validate AuditRecord
        - Persist to DynamoDB

        Args:
            event_data: Raw event dictionary from SQS

        Returns:
            AuditRecord if successfully created, None if duplicate (idempotent)

        Raises:
            ValidationError: If event validation fails
            EventProcessingError: If event processing fails
            IdempotencyError: If idempotency check fails (non-recoverable)
        """
        try:
            # Step 1: Validate raw event structure
            AuditEventValidator.validate_raw_event(event_data)
            log_with_context(
                logger,
                "DEBUG",
                "Raw event structure validated",
                event_type=event_data.get("event_type"),
            )

            # Step 2: Check if event type is consumable
            event_type = event_data.get("event_type")
            if not AuditEventValidator.is_consumable_event(event_type):
                log_with_context(
                    logger,
                    "INFO",
                    f"Event type not consumable by audit worker (skipping)",
                    event_type=event_type,
                    event_id=event_data.get("event_id"),
                )
                return None

            # Step 3: Parse to typed event model
            event: BaseEvent = AuditEventValidator.parse_event(event_data)
            log_with_context(
                logger,
                "DEBUG",
                "Event parsed to typed model",
                event_type=event.event_type,
                event_id=event.event_id,
            )

            # Step 4: Extract entity_id and source_event_id
            entity_id = AuditTransformer.get_entity_id_from_event(event)
            source_event_id = event.event_id

            if not entity_id:
                raise ValidationError(
                    "Could not extract entity_id (incident_id) from event",
                    details={
                        "event_type": event_type,
                        "event_id": event.event_id,
                    },
                )

            log_with_context(
                logger,
                "DEBUG",
                "Extracted entity_id and source_event_id",
                entity_id=entity_id,
                source_event_id=source_event_id,
            )

            # Step 5: Check idempotency (prevent duplicates)
            if self.repository.record_exists_by_source_event(
                entity_id, source_event_id
            ):
                log_with_context(
                    logger,
                    "INFO",
                    "Audit record already exists (idempotent duplicate)",
                    entity_id=entity_id,
                    source_event_id=source_event_id,
                )
                return None  # Return None, not error (idempotent is OK)

            # Step 6: Transform event to audit details
            audit_details = AuditTransformer.event_to_audit_details(event)
            audit_action = AuditTransformer.get_action_for_event_type(event_type)

            log_with_context(
                logger,
                "DEBUG",
                "Event transformed to audit details",
                entity_id=entity_id,
                action=audit_action,
            )

            # Step 7: Create AuditRecord
            audit_record = AuditRecord.create(
                entity_id=entity_id,
                source_event_id=source_event_id,
                event_type=event_type,
                action=audit_action,
                resource_type="incident",
                actor_id=event.actor.user_id,
                actor_name=event.actor.name,
                actor_email=event.actor.email,
                details=audit_details,
            )

            log_with_context(
                logger,
                "DEBUG",
                "AuditRecord created",
                audit_id=audit_record.audit_id,
                entity_id=entity_id,
            )

            # Step 8: Validate record
            AuditRecordValidator.validate_resource_id(audit_record.entity_id)
            AuditRecordValidator.validate_action(audit_record.action)
            AuditRecordValidator.validate_source_event_id(
                audit_record.source_event_id
            )

            log_with_context(
                logger,
                "DEBUG",
                "AuditRecord validation passed",
                audit_id=audit_record.audit_id,
            )

            # Step 9: Persist to DynamoDB
            self.repository.create_audit_record(audit_record)

            log_with_context(
                logger,
                "INFO",
                "Audit record processed and persisted successfully",
                audit_id=audit_record.audit_id,
                entity_id=entity_id,
                event_id=event.event_id,
            )

            return audit_record

        except (ValidationError, EventProcessingError, IdempotencyError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error processing event: {str(e)}"
            log_with_context(
                logger,
                "ERROR",
                error_msg,
                event_type=event_data.get("event_type"),
                event_id=event_data.get("event_id"),
                error=str(e),
            )
            raise EventProcessingError(
                error_msg,
                event_id=event_data.get("event_id"),
                event_type=event_data.get("event_type"),
            )

    def get_audit_trail(self, entity_id: str) -> List[AuditRecord]:
        """
        Retrieve the complete audit trail for an entity.

        Args:
            entity_id: Entity ID (e.g., incident_id)

        Returns:
            List of AuditRecord instances, sorted chronologically

        Raises:
            ValidationError: If entity_id is invalid
            EventProcessingError: If retrieval fails
        """
        try:
            # Validate input
            AuditRecordValidator.validate_resource_id(entity_id)

            # Query repository
            records = self.repository.get_records_by_entity(entity_id)

            log_with_context(
                logger,
                "INFO",
                f"Retrieved audit trail with {len(records)} entries",
                entity_id=entity_id,
            )

            return records

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to retrieve audit trail: {str(e)}"
            log_with_context(
                logger,
                "ERROR",
                error_msg,
                resource_id=resource_id,
                error=str(e),
            )
            raise EventProcessingError(error_msg)

    def get_audit_record_count(self, entity_id: str) -> int:
        """
        Get total audit records for an entity.

        Args:
            entity_id: Entity ID (e.g., incident_id)

        Returns:
            Count of records

        Raises:
            ValidationError: If entity_id is invalid
            EventProcessingError: If count fails
        """
        try:
            # Validate input
            AuditRecordValidator.validate_resource_id(entity_id)

            # Query repository
            count = self.repository.get_record_count(entity_id)

            log_with_context(
                logger,
                "DEBUG",
                f"Audit record count retrieved",
                entity_id=entity_id,
                count=count,
            )

            return count

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to count audit records: {str(e)}"
            log_with_context(
                logger,
                "ERROR",
                error_msg,
                entity_id=entity_id,
                error=str(e),
            )
            raise EventProcessingError(error_msg)
