"""
Core audit record model.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
from src.utils import generate_audit_id, get_current_timestamp


class AuditRecord(BaseModel):
    """
    Core audit record model.
    
    Represents a single audit entry in the system.
    """

    audit_id: str = Field(..., description="Unique audit record ID")
    resource_id: str = Field(..., description="ID of the audited resource (e.g., incident_id)")
    resource_type: str = Field("incident", description="Type of resource")
    created_at: str = Field(..., description="ISO 8601 timestamp when audit was created")
    source_event_id: str = Field(..., description="Source event ID for idempotency")
    event_type: str = Field(..., description="Type of event that triggered this audit")
    action: str = Field(..., description="Action performed (CREATED, STATUS_CHANGED, etc.)")
    actor_id: Optional[str] = Field(None, description="ID of the actor who performed the action")
    actor_name: Optional[str] = Field(None, description="Name of the actor")
    actor_email: Optional[str] = Field(None, description="Email of the actor")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional audit details")

    model_config = ConfigDict(extra="allow")

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """
        Convert audit record to DynamoDB item format.

        Returns:
            Dictionary suitable for DynamoDB put_item
        """
        item = {
            "audit_id": self.audit_id,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "created_at": self.created_at,
            "source_event_id": self.source_event_id,
            "event_type": self.event_type,
            "action": self.action,
        }

        # Add optional fields if present
        if self.actor_id is not None:
            item["actor_id"] = self.actor_id
        if self.actor_name is not None:
            item["actor_name"] = self.actor_name
        if self.actor_email is not None:
            item["actor_email"] = self.actor_email
        if self.details is not None:
            item["details"] = self.details

        return item

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "AuditRecord":
        """
        Convert DynamoDB item to AuditRecord.

        Args:
            item: DynamoDB item dictionary

        Returns:
            AuditRecord instance
        """
        return cls(
            audit_id=item.get("audit_id", ""),
            resource_id=item.get("resource_id", ""),
            resource_type=item.get("resource_type", "incident"),
            created_at=item.get("created_at", ""),
            source_event_id=item.get("source_event_id", ""),
            event_type=item.get("event_type", ""),
            action=item.get("action", ""),
            actor_id=item.get("actor_id"),
            actor_name=item.get("actor_name"),
            actor_email=item.get("actor_email"),
            details=item.get("details"),
        )

    @classmethod
    def create(
        cls,
        resource_id: str,
        source_event_id: str,
        event_type: str,
        action: str,
        resource_type: str = "incident",
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        actor_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> "AuditRecord":
        """
        Factory method to create a new AuditRecord.

        Args:
            resource_id: ID of the audited resource
            source_event_id: Source event ID for idempotency
            event_type: Type of event
            action: Action performed
            resource_type: Type of resource (default: incident)
            actor_id: ID of the actor
            actor_name: Name of the actor
            actor_email: Email of the actor
            details: Additional details

        Returns:
            New AuditRecord instance
        """
        return cls(
            audit_id=generate_audit_id(),
            resource_id=resource_id,
            resource_type=resource_type,
            created_at=get_current_timestamp(),
            source_event_id=source_event_id,
            event_type=event_type,
            action=action,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_email=actor_email,
            details=details,
        )
