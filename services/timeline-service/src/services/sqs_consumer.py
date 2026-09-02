"""
SQS consumer for timeline service.
Polls the timeline queue and processes events asynchronously.
"""

import time
import signal
import sys
from typing import Optional
from src.logger import setup_logger
from src.config import Config
from src.context import app_context
from src.services.message_handler import MessageHandler
from src.utils import extract_queue_url_name
from src.constants import SQS_MAX_MESSAGES, SQS_WAIT_TIME

logger = setup_logger(__name__, Config.LOG_LEVEL)


class SQSConsumer:
    """
    Polls SQS queue for events and processes them.
    
    Runs in a continuous loop:
    - Long polling with wait time
    - Receives batches of messages
    - Processes each message
    - Deletes successful messages
    - Retries failed messages
    
    Can be interrupted gracefully with Ctrl+C or SIGTERM.
    """

    def __init__(self):
        """Initialize consumer with AWS clients."""
        self.sqs_client = app_context.get_sqs_client()
        self.queue_url = Config.TIMELINE_QUEUE_URL
        self.message_handler = MessageHandler()
        self.running = True
        self.processed_count = 0
        self.failed_count = 0
        self.duplicate_count = 0

    def start(self) -> None:
        """
        Start the consumer loop.
        
        Sets up signal handlers and begins polling.
        Runs indefinitely until interrupted (Ctrl+C or SIGTERM).
        """
        logger.info(
            f"Starting SQS consumer",
            extra={
                "queue": extract_queue_url_name(self.queue_url),
                "wait_time": SQS_WAIT_TIME,
                "max_messages": SQS_MAX_MESSAGES,
            },
        )

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            self._run_polling_loop()
        except Exception as e:
            logger.error(
                f"Consumer crashed: {str(e)}",
                extra={"error": str(e)},
            )
            sys.exit(1)

    def _run_polling_loop(self) -> None:
        """
        Main polling loop.
        
        Continuously polls SQS queue until stopped.
        Uses long polling with configured wait time.
        """
        while self.running:
            try:
                # Poll SQS queue
                messages = self._receive_messages()

                if not messages:
                    # No messages, continue polling
                    continue

                # Process each message
                for message in messages:
                    if not self.running:
                        # Stop signal received, exit loop
                        break

                    self._process_single_message(message)

            except Exception as e:
                logger.error(
                    f"Error in polling loop: {str(e)}",
                    extra={"error": str(e)},
                )
                # Wait before retry to avoid spam
                time.sleep(5)

    def _receive_messages(self) -> list:
        """
        Receive messages from SQS queue.
        
        Uses long polling to reduce API calls and latency.

        Returns:
            List of SQS message dictionaries

        """
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=SQS_MAX_MESSAGES,
                WaitTimeSeconds=SQS_WAIT_TIME,
                AttributeNames=["All"],
                MessageAttributeNames=["All"],
            )

            messages = response.get("Messages", [])

            if messages:
                logger.debug(
                    f"Received {len(messages)} messages from queue",
                    extra={
                        "queue": extract_queue_url_name(self.queue_url),
                        "count": len(messages),
                    },
                )

            return messages

        except Exception as e:
            logger.error(
                f"Failed to receive messages from SQS: {str(e)}",
                extra={"error": str(e)},
            )
            # Return empty list to continue polling
            return []

    def _process_single_message(self, message: dict) -> None:
        """
        Process a single SQS message.

        Args:
            message: SQS message dictionary

        """
        message_id = message.get("MessageId", "unknown")

        try:
            # Delegate to message handler
            success = self.message_handler.process_message(message)

            if success:
                self.processed_count += 1
                logger.debug(
                    f"Message processed successfully",
                    extra={"message_id": message_id},
                )
            else:
                self.failed_count += 1
                logger.warning(
                    f"Message processing failed, will retry",
                    extra={"message_id": message_id},
                )

        except Exception as e:
            self.failed_count += 1
            logger.error(
                f"Unexpected error processing message: {str(e)}",
                extra={
                    "message_id": message_id,
                    "error": str(e),
                },
            )

    def _signal_handler(self, sig, frame):
        """
        Handle interrupt signals (Ctrl+C, SIGTERM).
        
        Gracefully shuts down the consumer.
        """
        signal_name = signal.Signals(sig).name if hasattr(signal, 'Signals') else str(sig)

        logger.info(
            f"Received signal {signal_name}, shutting down gracefully",
            extra={
                "signal": signal_name,
                "processed": self.processed_count,
                "failed": self.failed_count,
            },
        )

        self.running = False
        # Give current operations a moment to complete
        time.sleep(1)

        logger.info(
            "Consumer shutdown complete",
            extra={
                "total_processed": self.processed_count,
                "total_failed": self.failed_count,
            },
        )

        sys.exit(0)

    def get_stats(self) -> dict:
        """
        Get consumer statistics.

        Returns:
            Dictionary with processed/failed/duplicate counts

        """
        return {
            "processed": self.processed_count,
            "failed": self.failed_count,
            "running": self.running,
        }
