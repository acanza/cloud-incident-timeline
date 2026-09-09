"""
Utility functions for timeline service.
"""

import uuid
from datetime import datetime
from typing import Optional
from src.logger import setup_logger

logger = setup_logger(__name__)


def generate_uuid() -> str:
    """Generate a UUID v4 string."""
    return str(uuid.uuid4())


def generate_timeline_entry_id() -> str:
    """Generate a timeline entry ID."""
    return f"tl-{generate_uuid()}"


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix."""
    return datetime.utcnow().isoformat() + "Z"


def parse_iso_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse ISO format timestamp string to datetime object.

    Handles both formats:
    - 2026-07-30T08:00:00Z
    - 2026-07-30T08:00:00.000000Z
    """
    try:
        # Remove Z suffix if present
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1]

        # Try parsing with microseconds
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            # Try without microseconds
            return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        logger.error(f"Failed to parse timestamp '{timestamp_str}': {str(e)}")
        return None


def extract_queue_url_name(queue_url: str) -> str:
    """
    Extract queue name from SQS URL.

    Example: 'https://sqs.us-east-1.amazonaws.com/123456789012/queue-name' -> 'queue-name'
    """
    return queue_url.split("/")[-1]


def validate_event_structure(event: dict) -> bool:
    """
    Validate that event has required envelope fields.

    Returns:
        True if event is valid, False otherwise
    """
    required_fields = [
        "version",
        "event_id",
        "event_type",
        "source",
        "occurred_at",
        "correlation_id",
        "actor",
        "data",
    ]

    for field in required_fields:
        if field not in event:
            logger.warning(f"Event missing required field: {field}")
            return False

    return True
