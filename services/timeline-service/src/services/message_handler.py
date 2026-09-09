"""
SQS message handler for processing events from the timeline queue.
Handles individual message processing, error handling, and message lifecycle.
"""

import json
from typing import Optional, Dict, Any
from src.logger import setup_logger
from src.config import Config
from src.context import app_context
from src.services.timeline_service import TimelineService
from src.exceptions import TimelineServiceException
from src.utils import extract_queue_url_name

logger = setup_logger(__name__, Config.LOG_LEVEL)


class MessageHandler:
    """
    Handles individual SQS messages.
    
    Responsibilities:
    - Parse SQS message body
    - Delegate to TimelineService for event processing
    - Delete message on success
    - Handle errors and retries
    """

    def __init__(self):
        """Initialize handler with AWS clients."""
        self.sqs_client = app_context.get_sqs_client()
        self.timeline_service = TimelineService()
        self.queue_url = Config.TIMELINE_QUEUE_URL

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Process a single SQS message.

        Workflow:
        1. Extract message ID and receipt handle
        2. Parse message body as JSON (event)
        3. Delegate to TimelineService.process_event()
        4. On success: delete message from queue
        5. On duplicate: delete message (idempotent, not an error)
        6. On error: let message stay in queue for retry

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
            logger.error(
                "Invalid SQS message structure",
                extra={
                    "message_id": message_id,
                    "has_receipt": bool(receipt_handle),
                    "has_body": bool(message_body),
                },
            )
            # Return True to delete malformed message (don't retry forever)
            self._delete_message(message_id, receipt_handle)
            return True

        try:
            # Parse message body as JSON event
            event = self._parse_message_body(message_body)
            if not event:
                logger.warning(
                    "Failed to parse message body",
                    extra={"message_id": message_id},
                )
                # Delete malformed JSON (don't retry)
                self._delete_message(message_id, receipt_handle)
                return True

            # Process event via TimelineService
            timeline_entry = self.timeline_service.process_event(event)

            if timeline_entry:
                logger.info(
                    "Event processed successfully, creating timeline entry",
                    extra={
                        "message_id": message_id,
                        "incident_id": timeline_entry.incident_id,
                        "event_id": event.get("event_id"),
                    },
                )
            else:
                # Duplicate event (idempotent), still delete message
                logger.info(
                    "Event was duplicate, skipped",
                    extra={
                        "message_id": message_id,
                        "event_id": event.get("event_id"),
                    },
                )

            # Delete message on success (including duplicates)
            self._delete_message(message_id, receipt_handle)
            return True

        except TimelineServiceException as e:
            # Service exceptions: log but don't delete (will retry)
            logger.error(
                f"Service error processing message: {e.message}",
                extra={
                    "message_id": message_id,
                    "error_code": e.error_code,
                    "details": e.details,
                },
            )
            return False

        except json.JSONDecodeError as e:
            logger.warning(
                f"Invalid JSON in message body: {str(e)}",
                extra={"message_id": message_id},
            )
            # Delete malformed JSON
            self._delete_message(message_id, receipt_handle)
            return True

        except Exception as e:
            # Unexpected errors: log and retry
            logger.error(
                f"Unexpected error processing message: {str(e)}",
                extra={
                    "message_id": message_id,
                    "error": str(e),
                },
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

            # Validate it's a dictionary with expected event fields
            if not isinstance(event, dict):
                logger.warning("Message body is not a JSON object")
                return None

            return event

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {str(e)}")
            return None

    def _delete_message(self, message_id: str, receipt_handle: str) -> bool:
        """
        Delete a message from the SQS queue.

        Args:
            message_id: SQS message ID
            receipt_handle: SQS receipt handle

        Returns:
            True if deletion successful, False otherwise

        """
        try:
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )

            logger.debug(
                "Message deleted from queue",
                extra={
                    "message_id": message_id,
                    "queue": extract_queue_url_name(self.queue_url),
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to delete message from queue: {str(e)}",
                extra={
                    "message_id": message_id,
                    "error": str(e),
                },
            )
            return False
