"""Incident service business logic."""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from models.incident import Incident
from constants import (
    IncidentStatus, IncidentSeverity,
    EVENT_TYPE_INCIDENT_CREATED,
    EVENT_TYPE_INCIDENT_STATUS_CHANGED,
    EVENT_TYPE_INCIDENT_SEVERITY_CHANGED,
    EVENT_TYPE_INCIDENT_RESOLVED
)


class IncidentService:
    """Service for managing incidents."""
    
    def __init__(self):
        """Initialize incident service with in-memory storage.
        
        NOTE: This is temporary. Will be replaced with DynamoDB integration in Phase 3.
        """
        self.incidents: dict[str, Incident] = {}
    
    def create_incident(
        self,
        title: str,
        description: str,
        severity: str
    ) -> Tuple[Incident, str]:
        """Create a new incident.
        
        Args:
            title: Incident title
            description: Incident description
            severity: Incident severity
        
        Returns:
            Tuple of (incident, event_type)
        """
        incident_id = f"inc-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat() + 'Z'
        
        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN.value,
            created_at=now,
            updated_at=now
        )
        
        # Store in memory (will be DynamoDB in Phase 3)
        self.incidents[incident_id] = incident
        
        return incident, EVENT_TYPE_INCIDENT_CREATED
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID.
        
        Args:
            incident_id: Incident identifier
        
        Returns:
            Incident or None if not found
        """
        return self.incidents.get(incident_id)
    
    def list_incidents(self) -> List[Incident]:
        """List all incidents.
        
        Returns:
            List of incidents
        """
        return list(self.incidents.values())
    
    def update_incident_status(
        self,
        incident_id: str,
        new_status: str
    ) -> Tuple[Optional[Incident], Optional[str]]:
        """Update incident status.
        
        Args:
            incident_id: Incident identifier
            new_status: New status
        
        Returns:
            Tuple of (incident, event_type) or (None, None) if not found
        """
        incident = self.get_incident(incident_id)
        if not incident:
            return None, None
        
        # Check if status actually changed
        if incident.status == new_status:
            return incident, None
        
        # Update status
        now = datetime.utcnow().isoformat() + 'Z'
        incident.update_status(new_status, now)
        
        # Determine event type
        if new_status == IncidentStatus.RESOLVED.value:
            event_type = EVENT_TYPE_INCIDENT_RESOLVED
        else:
            event_type = EVENT_TYPE_INCIDENT_STATUS_CHANGED
        
        return incident, event_type
    
    def update_incident_severity(
        self,
        incident_id: str,
        new_severity: str
    ) -> Tuple[Optional[Incident], Optional[str]]:
        """Update incident severity.
        
        Args:
            incident_id: Incident identifier
            new_severity: New severity level
        
        Returns:
            Tuple of (incident, event_type) or (None, None) if not found
        """
        incident = self.get_incident(incident_id)
        if not incident:
            return None, None
        
        # Check if severity actually changed
        if incident.severity == new_severity:
            return incident, None
        
        # Update severity
        now = datetime.utcnow().isoformat() + 'Z'
        incident.update_severity(new_severity, now)
        
        return incident, EVENT_TYPE_INCIDENT_SEVERITY_CHANGED


# Global incident service instance
incident_service = IncidentService()
