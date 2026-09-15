"""Incident service business logic."""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from ..models.incident import Incident
from ..logger import get_structured_logger
from .incident_repository import IncidentRepository
from ..constants import (
    IncidentStatus, IncidentSeverity,
    EVENT_TYPE_INCIDENT_CREATED,
    EVENT_TYPE_INCIDENT_STATUS_CHANGED,
    EVENT_TYPE_INCIDENT_SEVERITY_CHANGED,
    EVENT_TYPE_INCIDENT_RESOLVED
)

logger = get_structured_logger(__name__, service_name="incident-service")


class IncidentService:
    """Service for managing incidents."""
    
    def __init__(self):
        """Initialize incident service with DynamoDB storage."""
        try:
            self.repository = IncidentRepository()
            logger.info("Incident service initialized with DynamoDB repository")
        except Exception as e:
            logger.error(
                f"Failed to initialize incident service: {str(e)}",
                extra={'exception_type': type(e).__name__}
            )
            raise
    
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
        event_id = f"evt-{uuid.uuid4().hex[:12]}"
        
        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN.value,
            created_at=now,
            updated_at=now
        )
        
        # Persist to DynamoDB
        if not self.repository.create_incident(incident):
            logger.error(
                "Failed to create incident in repository",
                extra={'incident_id': incident_id}
            )
            raise Exception(f"Failed to persist incident {incident_id}")
        
        # Create timeline event
        if not self.repository.create_timeline_event(
            incident_id=incident_id,
            event_id=event_id,
            event_type=EVENT_TYPE_INCIDENT_CREATED,
            event_data={
                "incident_id": incident_id,
                "title": title,
                "description": description,
                "severity": severity,
                "status": IncidentStatus.OPEN.value
            },
            created_at=now
        ):
            logger.warning(
                "Failed to create timeline event",
                extra={
                    'incident_id': incident_id,
                    'event_type': EVENT_TYPE_INCIDENT_CREATED
                }
            )
        
        return incident, EVENT_TYPE_INCIDENT_CREATED
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID.
        
        Args:
            incident_id: Incident identifier
        
        Returns:
            Incident or None if not found
        """
        return self.repository.get_incident(incident_id)
    
    def list_incidents(self) -> List[Incident]:
        """List all incidents.
        
        Returns:
            List of incidents
        """
        return self.repository.list_incidents()
    
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
        
        # Update in DynamoDB
        if not self.repository.update_incident_status(incident_id, new_status):
            logger.error(
                "Failed to update incident status",
                extra={
                    'incident_id': incident_id,
                    'new_status': new_status
                }
            )
            return None, None
        
        # Update local object
        now = datetime.utcnow().isoformat() + 'Z'
        incident.update_status(new_status, now)
        
        # Create timeline event
        event_id = f"evt-{uuid.uuid4().hex[:12]}"
        if new_status == IncidentStatus.RESOLVED.value:
            event_type = EVENT_TYPE_INCIDENT_RESOLVED
        else:
            event_type = EVENT_TYPE_INCIDENT_STATUS_CHANGED
        
        self.repository.create_timeline_event(
            incident_id=incident_id,
            event_id=event_id,
            event_type=event_type,
            event_data={
                "incident_id": incident_id,
                "old_status": incident.status,
                "new_status": new_status
            },
            created_at=now
        )
        
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
        
        # Update in DynamoDB
        if not self.repository.update_incident_severity(incident_id, new_severity):
            logger.error(
                "Failed to update incident severity",
                extra={
                    'incident_id': incident_id,
                    'new_severity': new_severity
                }
            )
            return None, None
        
        # Update local object
        now = datetime.utcnow().isoformat() + 'Z'
        incident.update_severity(new_severity, now)
        
        # Create timeline event
        event_id = f"evt-{uuid.uuid4().hex[:12]}"
        self.repository.create_timeline_event(
            incident_id=incident_id,
            event_id=event_id,
            event_type=EVENT_TYPE_INCIDENT_SEVERITY_CHANGED,
            event_data={
                "incident_id": incident_id,
                "old_severity": incident.severity,
                "new_severity": new_severity
            },
            created_at=now
        )
        
        return incident, EVENT_TYPE_INCIDENT_SEVERITY_CHANGED


# Global incident service instance
incident_service = IncidentService()
