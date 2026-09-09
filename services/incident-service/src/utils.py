"""
Shared utilities: validation, error handling, etc.
"""

from typing import Optional, List
from .schemas import ErrorResponseSchema, ErrorDetailSchema
from .constants import VALID_STATUSES, VALID_SEVERITIES


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, details: Optional[List[dict]] = None):
        self.message = message
        self.details = details or []
        super().__init__(self.message)
    
    def to_response(self) -> ErrorResponseSchema:
        """Converts error to structured response."""
        error_details = [
            ErrorDetailSchema(field=d.get('field', ''), message=d.get('message', ''))
            for d in self.details
        ]
        return ErrorResponseSchema(message=self.message, details=error_details or None)


def validate_status(status: str) -> tuple[bool, Optional[str]]:
    """
    Validates that status is valid.
    
    Args:
        status: Status to validate
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if status not in VALID_STATUSES:
        return False, f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
    return True, None


def validate_severity(severity: str) -> tuple[bool, Optional[str]]:
    """
    Validates that severity is valid.
    
    Args:
        severity: Severity to validate
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if severity not in VALID_SEVERITIES:
        return False, f"Invalid severity. Must be one of: {', '.join(VALID_SEVERITIES)}"
    return True, None


def validate_create_incident_request(
    title: str,
    description: str,
    severity: str
) -> tuple[bool, Optional[ValidationError]]:
    """
    Validates create incident request.
    
    Args:
        title: Incident title
        description: Incident description
        severity: Incident severity
    
    Returns:
        Tuple (is_valid, error_object_or_none)
    """
    details = []
    
    if not title or not title.strip():
        details.append({'field': 'title', 'message': 'Title is required and cannot be empty'})
    
    if not description or not description.strip():
        details.append({'field': 'description', 'message': 'Description is required and cannot be empty'})
    
    is_valid_severity, error_msg = validate_severity(severity)
    if not is_valid_severity:
        details.append({'field': 'severity', 'message': error_msg})
    
    if details:
        return False, ValidationError("Validation error", details)
    
    return True, None


def validate_status_change(new_status: str) -> tuple[bool, Optional[ValidationError]]:
    """
    Validates status change.
    
    Args:
        new_status: New status
    
    Returns:
        Tuple (is_valid, error_object_or_none)
    """
    is_valid, error_msg = validate_status(new_status)
    
    if not is_valid:
        error = ValidationError("Validation error", [{'field': 'status', 'message': error_msg}])
        return False, error
    
    return True, None


def validate_severity_change(new_severity: str) -> tuple[bool, Optional[ValidationError]]:
    """
    Validates severity change.
    
    Args:
        new_severity: New severity
    
    Returns:
        Tuple (is_valid, error_object_or_none)
    """
    is_valid, error_msg = validate_severity(new_severity)
    
    if not is_valid:
        error = ValidationError("Validation error", [{'field': 'severity', 'message': error_msg}])
        return False, error
    
    return True, None
