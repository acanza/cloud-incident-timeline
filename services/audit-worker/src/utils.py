"""
Utility functions for audit worker service.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional


def generate_audit_id() -> str:
    """
    Generate a unique audit record ID.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.

    Returns:
        ISO 8601 formatted timestamp with Z suffix
    """
    return datetime.utcnow().isoformat() + "Z"


def extract_actor_info(event_data: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Extract actor information from event data.

    Args:
        event_data: Event payload dictionary

    Returns:
        Dictionary with actor_id, actor_name, and actor_email
    """
    actor = event_data.get("actor", {})
    if isinstance(actor, dict):
        return {
            "actor_id": actor.get("user_id"),
            "actor_name": actor.get("name"),
            "actor_email": actor.get("email"),
        }
    return {
        "actor_id": None,
        "actor_name": None,
        "actor_email": None,
    }


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary.

    Args:
        data: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found

    Returns:
        Value at key or default
    """
    if not isinstance(data, dict):
        return default
    return data.get(key, default)


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to integer.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any) -> bool:
    """
    Safely convert a value to boolean.

    Args:
        value: Value to convert

    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)


def truncate_string(value: str, max_length: int = 500) -> str:
    """
    Truncate a string to maximum length.

    Args:
        value: String to truncate
        max_length: Maximum length

    Returns:
        Truncated string
    """
    if not isinstance(value, str):
        return str(value)[:max_length]
    return value[:max_length]
