"""
SQS message handler for processing events from the audit queue.
Handles individual message processing, error handling, and message lifecycle.
"""

import json
from typing import Optional, Dict, Any
from pydantic import ValidationError
from src.logger import setup_logger, log_with_context
from src.config import Config
from src.context import app_context
from src.services.audit_service import AuditService
from src.exceptions import AuditWorkerException

logger = setup_logger(__name__, Config.LOG_LEVEL)


class MessageHandler:
    """
    Handles individual SQS messages.
    
    Responsibilities:
    - Parse SQS message body
    - Delegate to AuditService for event processing
    - Delete message on success
    - Handle errors and retries
    """

    def __init__(self):
        """Initialize handler with AWS clients."""
        self.sqs_client = app_context.get_sqs_client()
        self.audit_service = AuditService()
        self.queue_url = Config.AUDIT_QUEUE_URL

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Process a single SQS message.

        Workflow:
        1. Extract message ID and receipt handle
        2. Parse message body as JSON (event)
        3. Delegate to AuditService.process_event()
        4. On success: delete message from queue
        5. On duplicate: delete message (idempotent, not an error)
        6. On error: let message stay in queue for retry

        Strategy:
        - Invalid JSON → Delete (won't improve)
        - Malformed event → Delete (won't improve)
        - Validation error → Don't delete (retry)
        - Service error → Don't delete (retry)
        - Duplicates → Delete (idempotent, no error)

        Args:
            message: SQS message dictionary

        Returns:
            True if message was successfully processed and deleted
            False if message should remain in queue (will retry)
        """
        message_id = message.get("MessageId")
        receipt_handle = message.get("ReceiptHandle")
        message_body = message.get("Body")

        if not all([message_id, receipt_handle, message_body]):
            log_with_context(
                logger,
                "ERROR",
                "Invalid SQS message structure",
                message_id=message_id,
            )
            # Return True to delete malformed message (don't retry forever)
            self._delete_message(message_id, receipt_handle)
            return True

        try:
            # Parse message body as JSON event
            event = self._parse_message_body(message_body)
            if not event:
                log_with_context(
                    logger,
                    "WARNING",
                    "Failed to parse message body",
                    message_id=message_id,
                )
                # Delete malformed JSON (don't retry)
                self._delete_message(message_id, receipt_handle)
                return True

            # Process event via AuditService
            audit_record = self.audit_service.process_event(event)

            if audit_record:
                log_with_context(
                    logger,
                    "INFO",
                    "Event processed successfully, creating audit record",
                    message_id=message_id,
                    audit_id=audit_record.audit_id,
                    entity_id=audit_record.entity_id,
                    event_id=event.get("event_id"),
                    action=audit_record.action,
                )
            else:
                # Duplicate event (idempotent) or non-consumable event, still delete message
                log_with_context(
                    logger,
                    "INFO",
                    "Event was duplicate or non-consumable, skipped",
                    message_id=message_id,
                    event_id=event.get("event_id"),
                    event_type=event.get("event_type"),
                )

            # Delete message on success (including duplicates)
            self._delete_message(message_id, receipt_handle)
            return True

        except AuditWorkerException as e:
            # Service exceptions: log but don't delete (will retry)
            log_with_context(
                logger,
                "ERROR",
                f"Service error processing message: {e.message}",
                message_id=message_id,
                error_code=e.error_code,
                details=str(e.details),
            )
            return False

        except ValidationError as e:
            # Malformed event structure (Pydantic validation failed)
            # Delete message because it won't improve on retry
            log_with_context(
                logger,
                "WARNING",
                f"Event validation failed (malformed structure): {str(e)}",
                message_id=message_id,
            )
            self._delete_message(message_id, receipt_handle)
            return True

        except json.JSONDecodeError as e:
            log_with_context(
                logger,
                "WARNING",
                f"Invalid JSON in message body: {str(e)}",
                message_id=message_id,
            )
            # Delete malformed JSON
            self._delete_message(message_id, receipt_handle)
            return True

        except Exception as e:
            # Unexpected errors: log and retry
            log_with_context(
                logger,
                "ERROR",
                f"Unexpected error processing message: {str(e)}",
                message_id=message_id,
                error=str(e),
            )
            return False

    def _parse_message_body(self, body: str) -> Optional[Dict[str, Any]]:
        """
        Parse message body as JSON event.

        Args:
            body: Message body string

        Returns:
            Parsed event dictionary or None if parsing fails
        """
        try:
            event = json.loads(body)
            return event
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            return None

    def _delete_message(
        self, message_id: str, receipt_handle: str
    ) -> None:
        """
        Delete a message from the SQS queue.

        Args:
            message_id: Message ID
            receipt_handle: Receipt handle from receive_message
        """
        try:
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )
            log_with_context(
                logger,
                "DEBUG",
                "Message deleted from queue",
                message_id=message_id,
            )
        except Exception as e:
            log_with_context(
                logger,
                "WARNING",
                f"Failed to delete message: {str(e)}",
                message_id=message_id,
                error=str(e),
            )
