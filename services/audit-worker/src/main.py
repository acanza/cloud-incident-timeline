"""
Entry point for audit worker service.
Initializes configuration and starts the SQS consumer.
"""

import sys
from src.config import Config
from src.logger import setup_logger, log_with_context
from src.services.sqs_consumer import SQSConsumer

logger = setup_logger(__name__, Config.LOG_LEVEL)


def main():
    """
    Main entry point for audit worker.

    Workflow:
    1. Validate configuration
    2. Initialize logger
    3. Create SQS consumer
    4. Start polling and processing events
    """
    # Validate configuration on startup
    try:
        Config.validate()
        log_with_context(
            logger,
            "INFO",
            "Configuration validated successfully",
            service=Config.SERVICE_NAME,
            region=Config.AWS_REGION,
            log_level=Config.LOG_LEVEL,
            audit_table=Config.AUDIT_TABLE_NAME,
            audit_queue=Config.AUDIT_QUEUE_URL.split("/")[-1],
        )
    except ValueError as e:
        log_with_context(
            logger,
            "ERROR",
            f"Configuration error: {str(e)}",
            error=str(e),
        )
        sys.exit(1)

    try:
        # Create SQS consumer
        consumer = SQSConsumer()

        log_with_context(
            logger,
            "INFO",
            "Audit worker starting",
            service=Config.SERVICE_NAME,
        )

        # Start polling and processing
        consumer.start()

    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            f"Failed to start audit worker: {str(e)}",
            error=str(e),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
