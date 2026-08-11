"""
Constantes y enumeraciones compartidas para incident-service.
"""

from enum import Enum


class IncidentStatus(str, Enum):
    """Estados válidos de un incidente."""
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class IncidentSeverity(str, Enum):
    """Niveles de severidad válidos."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Estados válidos como lista (para validaciones)
VALID_STATUSES = [status.value for status in IncidentStatus]
VALID_SEVERITIES = [severity.value for severity in IncidentSeverity]

# Event types
EVENT_TYPE_INCIDENT_CREATED = "IncidentCreated"
EVENT_TYPE_INCIDENT_STATUS_CHANGED = "IncidentStatusChanged"
EVENT_TYPE_INCIDENT_SEVERITY_CHANGED = "IncidentSeverityChanged"
EVENT_TYPE_INCIDENT_RESOLVED = "IncidentResolved"

# Event schema version
EVENT_SCHEMA_VERSION = "1.0"

# Service name
SERVICE_NAME = "incident-service"
