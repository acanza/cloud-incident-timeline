"""
Application context and AWS clients initialization.
"""

import boto3
from typing import Optional
from src.config import Config
from src.logger import setup_logger

logger = setup_logger(__name__, Config.LOG_LEVEL)


class AppContext:
    """
    Singleton context holding AWS clients and application state.
    """

    _instance: Optional["AppContext"] = None
    _initialized: bool = False

    def __new__(cls) -> "AppContext":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            # Initialize AWS clients
            self.dynamodb = boto3.resource(
                "dynamodb",
                region_name=Config.AWS_REGION,
            )
            self.sqs = boto3.client(
                "sqs",
                region_name=Config.AWS_REGION,
            )
            self.eventbridge = boto3.client(
                "events",
                region_name=Config.AWS_REGION,
            )

            # Initialize table reference
            self.timeline_table = self.dynamodb.Table(Config.TIMELINE_TABLE_NAME)

            logger.info(
                f"AppContext initialized. Service: {Config.SERVICE_NAME}, "
                f"Region: {Config.AWS_REGION}"
            )

            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize AppContext: {str(e)}")
            raise

    def get_dynamodb(self):
        """Get DynamoDB resource."""
        return self.dynamodb

    def get_sqs_client(self):
        """Get SQS client."""
        return self.sqs

    def get_eventbridge_client(self):
        """Get EventBridge client."""
        return self.eventbridge

    def get_timeline_table(self):
        """Get timeline DynamoDB table."""
        return self.timeline_table


# Global context instance
app_context = AppContext()
