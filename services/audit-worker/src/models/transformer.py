"""
Event to audit record transformation.
"""

from typing import Dict, Any, Optional
from src.constants import (
    EVENT_TYPE_INCIDENT_CREATED,
    EVENT_TYPE_INCIDENT_STATUS_CHANGED,
    EVENT_TYPE_INCIDENT_SEVERITY_CHANGED,
    EVENT_TYPE_INCIDENT_RESOLVED,
    AUDIT_ACTION_CREATED,
    AUDIT_ACTION_STATUS_CHANGED,
    AUDIT_ACTION_SEVERITY_CHANGED,
    AUDIT_ACTION_RESOLVED,
)
from src.models.event import BaseEvent


class AuditTransformer:
    """Transforms domain events into audit records."""

    @staticmethod
    def event_to_audit_details(event: BaseEvent) -> Dict[str, Any]:
        """
        Transform event into audit record details.

        Args:
            event: Domain event

        Returns:
            Dictionary with audit details
        """
        event_type = event.event_type

        if event_type == EVENT_TYPE_INCIDENT_CREATED:
            return AuditTransformer._incident_created_details(event)
        elif event_type == EVENT_TYPE_INCIDENT_STATUS_CHANGED:
            return AuditTransformer._incident_status_changed_details(event)
        elif event_type == EVENT_TYPE_INCIDENT_SEVERITY_CHANGED:
            return AuditTransformer._incident_severity_changed_details(event)
        elif event_type == EVENT_TYPE_INCIDENT_RESOLVED:
            return AuditTransformer._incident_resolved_details(event)
        else:
            # Generic details for unknown event types
            return {
                "event_type": event_type,
                "data": event.data,
            }

    @staticmethod
    def _incident_created_details(event: BaseEvent) -> Dict[str, Any]:
        """Extract details from IncidentCreated event."""
        data = event.data
        return {
            "incident_id": getattr(data, "incident_id", None),
            "title": getattr(data, "title", None),
            "description": getattr(data, "description", None),
            "severity": getattr(data, "severity", None),
            "status": getattr(data, "status", None),
            "event_type": event.event_type,
        }

    @staticmethod
    def _incident_status_changed_details(event: BaseEvent) -> Dict[str, Any]:
        """Extract details from IncidentStatusChanged event."""
        data = event.data
        return {
            "incident_id": getattr(data, "incident_id", None),
            "previous_status": getattr(data, "previous_status", None),
            "new_status": getattr(data, "new_status", None),
            "event_type": event.event_type,
        }

    @staticmethod
    def _incident_severity_changed_details(event: BaseEvent) -> Dict[str, Any]:
        """Extract details from IncidentSeverityChanged event."""
        data = event.data
        return {
            "incident_id": getattr(data, "incident_id", None),
            "previous_severity": getattr(data, "previous_severity", None),
            "new_severity": getattr(data, "new_severity", None),
            "event_type": event.event_type,
        }

    @staticmethod
    def _incident_resolved_details(event: BaseEvent) -> Dict[str, Any]:
        """Extract details from IncidentResolved event."""
        data = event.data
        return {
            "incident_id": getattr(data, "incident_id", None),
            "resolution_summary": getattr(data, "resolution_summary", None),
            "event_type": event.event_type,
        }

    @staticmethod
    def get_action_for_event_type(event_type: str) -> str:
        """
        Map event type to audit action.

        Args:
            event_type: Event type string

        Returns:
            Audit action string
        """
        action_map = {
            EVENT_TYPE_INCIDENT_CREATED: AUDIT_ACTION_CREATED,
            EVENT_TYPE_INCIDENT_STATUS_CHANGED: AUDIT_ACTION_STATUS_CHANGED,
            EVENT_TYPE_INCIDENT_SEVERITY_CHANGED: AUDIT_ACTION_SEVERITY_CHANGED,
            EVENT_TYPE_INCIDENT_RESOLVED: AUDIT_ACTION_RESOLVED,
        }
        return action_map.get(event_type, "UNKNOWN")

    @staticmethod
    def get_entity_id_from_event(event: BaseEvent) -> Optional[str]:
        """
        Extract entity ID (incident_id) from event data.

        Args:
            event: Domain event

        Returns:
            Entity ID or None
        """
        return getattr(event.data, "incident_id", None)

    @staticmethod
    def get_human_readable_description(event: BaseEvent) -> str:
        """
        Generate human-readable description for audit record.

        Args:
            event: Domain event

        Returns:
            Descriptive string
        """
        event_type = event.event_type
        actor_name = event.actor.name or event.actor.user_id
        data = event.data

        if event_type == EVENT_TYPE_INCIDENT_CREATED:
            severity = getattr(data, "severity", "UNKNOWN")
            status = getattr(data, "status", "UNKNOWN")
            return f"Incident created by {actor_name} with severity {severity} and status {status}"

        elif event_type == EVENT_TYPE_INCIDENT_STATUS_CHANGED:
            prev = getattr(data, "previous_status", "UNKNOWN")
            new = getattr(data, "new_status", "UNKNOWN")
            return f"Incident status changed by {actor_name} from {prev} to {new}"

        elif event_type == EVENT_TYPE_INCIDENT_SEVERITY_CHANGED:
            prev = getattr(data, "previous_severity", "UNKNOWN")
            new = getattr(data, "new_severity", "UNKNOWN")
            return f"Incident severity changed by {actor_name} from {prev} to {new}"

        elif event_type == EVENT_TYPE_INCIDENT_RESOLVED:
            summary = getattr(data, "resolution_summary", "")
            if summary:
                return f"Incident resolved by {actor_name}: {summary}"
            else:
                return f"Incident resolved by {actor_name}"

        else:
            return f"Action performed by {actor_name}: {event_type}"
