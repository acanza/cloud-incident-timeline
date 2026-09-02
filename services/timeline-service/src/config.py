import os
from typing import Optional


class Config:
    """
    Application configuration loaded from environment variables.
    """

    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # DynamoDB
    TIMELINE_TABLE_NAME: str = os.getenv("TIMELINE_TABLE_NAME", "")
    if not TIMELINE_TABLE_NAME:
        raise ValueError("TIMELINE_TABLE_NAME environment variable is required")

    # SQS
    TIMELINE_QUEUE_URL: str = os.getenv("TIMELINE_QUEUE_URL", "")
    if not TIMELINE_QUEUE_URL:
        raise ValueError("TIMELINE_QUEUE_URL environment variable is required")

    # EventBridge (optional, required only for comment creation)
    EVENT_BUS_NAME: Optional[str] = os.getenv("EVENT_BUS_NAME")

    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "timeline-service")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", 80))

    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.
        """
        required_fields = [
            "TIMELINE_TABLE_NAME",
            "TIMELINE_QUEUE_URL",
        ]

        missing = []
        for field in required_fields:
            if not getattr(cls, field, None):
                missing.append(field)

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
