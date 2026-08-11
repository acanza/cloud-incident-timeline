"""Incident data model."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from constants import IncidentStatus, IncidentSeverity


@dataclass
class Incident:
    """Incident domain model."""
    
    incident_id: str
    title: str
    description: str
    severity: str
    status: str
    created_at: str
    updated_at: str
    
    def __post_init__(self):
        """Validate incident on creation."""
        # Validate status
        valid_statuses = [s.value for s in IncidentStatus]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")
        
        # Validate severity
        valid_severities = [s.value for s in IncidentSeverity]
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}")
    
    def to_dict(self) -> dict:
        """Convert incident to dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Incident':
        """Create incident from dictionary."""
        return Incident(
            incident_id=data.get('incident_id'),
            title=data.get('title'),
            description=data.get('description'),
            severity=data.get('severity'),
            status=data.get('status'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def update_status(self, new_status: str, updated_at: str) -> None:
        """Update incident status."""
        valid_statuses = [s.value for s in IncidentStatus]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        
        self.status = new_status
        self.updated_at = updated_at
    
    def update_severity(self, new_severity: str, updated_at: str) -> None:
        """Update incident severity."""
        valid_severities = [s.value for s in IncidentSeverity]
        if new_severity not in valid_severities:
            raise ValueError(f"Invalid severity: {new_severity}")
        
        self.severity = new_severity
        self.updated_at = updated_at
