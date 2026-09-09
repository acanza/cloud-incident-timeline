import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Application configuration loaded from environment variables.
    """

    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # DynamoDB
    AUDIT_TABLE_NAME: str = os.getenv("AUDIT_TABLE_NAME", "")
    if not AUDIT_TABLE_NAME:
        raise ValueError("AUDIT_TABLE_NAME environment variable is required")

    # SQS
    AUDIT_QUEUE_URL: str = os.getenv("AUDIT_QUEUE_URL", "")
    if not AUDIT_QUEUE_URL:
        raise ValueError("AUDIT_QUEUE_URL environment variable is required")

    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "audit-worker")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.
        """
        required_fields = [
            "AUDIT_TABLE_NAME",
            "AUDIT_QUEUE_URL",
        ]

        missing = []
        for field in required_fields:
            if not getattr(cls, field, None):
                missing.append(field)

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
