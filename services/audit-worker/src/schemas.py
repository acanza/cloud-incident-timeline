"""
Pydantic schemas for audit worker service.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class ActorInfo(BaseModel):
    """
    Information about the actor performing an action.
    """

    user_id: str = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="User name")
    email: Optional[str] = Field(None, description="User email")

    model_config = ConfigDict(extra="allow")


class EventEnvelope(BaseModel):
    """
    Standard event envelope structure.
    """

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    version: str = Field("1.0", description="Event envelope version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    source: str = Field(..., description="Source service")
    actor: Optional[ActorInfo] = Field(None, description="Actor information")
    data: Dict[str, Any] = Field(..., description="Event payload data")

    model_config = ConfigDict(extra="allow")


class AuditRecordRequest(BaseModel):
    """
    Request model for creating an audit record.
    """

    resource_id: str = Field(..., description="ID of the audited resource")
    resource_type: str = Field("incident", description="Type of resource")
    action: str = Field(..., description="Action performed")
    actor_id: Optional[str] = Field(None, description="ID of the actor")
    actor_name: Optional[str] = Field(None, description="Name of the actor")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")

    model_config = ConfigDict(extra="allow")


class AuditRecord(BaseModel):
    """
    Audit record stored in DynamoDB.
    """

    audit_id: str = Field(..., description="Unique audit record ID")
    resource_id: str = Field(..., description="ID of the audited resource")
    resource_type: str = Field("incident", description="Type of resource")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    source_event_id: str = Field(..., description="Source event ID for idempotency")
    event_type: str = Field(..., description="Type of event that triggered this audit")
    action: str = Field(..., description="Action performed")
    actor_id: Optional[str] = Field(None, description="ID of the actor")
    actor_name: Optional[str] = Field(None, description="Name of the actor")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")

    model_config = ConfigDict(extra="allow")

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """
        Convert audit record to DynamoDB item format.

        Returns:
            Dictionary suitable for DynamoDB put_item
        """
        return {
            "audit_id": self.audit_id,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "created_at": self.created_at,
            "source_event_id": self.source_event_id,
            "event_type": self.event_type,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "details": self.details,
        }

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
            details=item.get("details"),
        )
