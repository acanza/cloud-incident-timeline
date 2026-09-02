"""
Timeline entry data model for DynamoDB persistence.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TimelineEntry(BaseModel):
    """
    Represents a single timeline entry in DynamoDB.
    
    Partition key: incident_id
    Sort key: created_at#timeline_entry_id
    """

    incident_id: str = Field(..., description="Incident ID")
    timeline_entry_id: str = Field(..., description="Unique timeline entry ID")
    created_at: str = Field(..., description="ISO timestamp when entry was created")
    message: str = Field(..., description="Human-readable timeline message")
    event_type: str = Field(..., description="Original event type that created this entry")
    source_event_id: str = Field(
        ..., description="Event ID for idempotency checking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc-001",
                "timeline_entry_id": "tl-1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
                "created_at": "2026-07-30T08:00:00Z",
                "message": "Incident created with HIGH severity and OPEN status.",
                "event_type": "IncidentCreated",
                "source_event_id": "evt-001",
            }
        }

    def to_dynamodb_item(self) -> dict:
        """
        Convert to DynamoDB item format.

        Returns:
            Dictionary suitable for DynamoDB put_item operation
        """
        return {
            "incident_id": self.incident_id,
            "created_at__timeline_entry_id": f"{self.created_at}#{self.timeline_entry_id}",
            "created_at": self.created_at,
            "timeline_entry_id": self.timeline_entry_id,
            "message": self.message,
            "event_type": self.event_type,
            "source_event_id": self.source_event_id,
        }

    @staticmethod
    def from_dynamodb_item(item: dict) -> "TimelineEntry":
        """
        Create TimelineEntry from DynamoDB item.

        Args:
            item: DynamoDB item dictionary

        Returns:
            TimelineEntry instance
        """
        return TimelineEntry(
            incident_id=item.get("incident_id"),
            timeline_entry_id=item.get("timeline_entry_id"),
            created_at=item.get("created_at"),
            message=item.get("message"),
            event_type=item.get("event_type"),
            source_event_id=item.get("source_event_id"),
        )
