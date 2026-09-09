"""
Event data models for domain events consumed from SQS.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class ActorInfo(BaseModel):
    """Information about who triggered the action."""

    user_id: str
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-001",
                "email": "user@example.com",
            }
        }


class BaseEvent(BaseModel):
    """
    Base event envelope structure.
    
    All domain events from EventBridge follow this structure.
    """

    version: str = Field(..., description="Event schema version")
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Domain event type")
    source: str = Field(..., description="Service that emitted the event")
    occurred_at: str = Field(..., description="UTC timestamp when event occurred")
    correlation_id: str = Field(
        ..., description="ID for tracing request flow across services"
    )
    actor: ActorInfo = Field(..., description="Who or what triggered this action")
    data: Dict[str, Any] = Field(..., description="Event-specific payload")

    class Config:
        json_schema_extra = {
            "example": {
                "version": "1.0",
                "event_id": "evt-001",
                "event_type": "IncidentCreated",
                "source": "incident-service",
                "occurred_at": "2026-07-30T08:00:00Z",
                "correlation_id": "corr-001",
                "actor": {
                    "user_id": "user-001",
                    "email": "user@example.com",
                },
                "data": {"incident_id": "inc-001"},
            }
        }


class IncidentCreatedEventData(BaseModel):
    """Data payload for IncidentCreated event."""

    incident_id: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc-001",
                "title": "API latency spike",
                "description": "Response times exceeding SLA",
                "severity": "HIGH",
                "status": "OPEN",
            }
        }


class IncidentStatusChangedEventData(BaseModel):
    """Data payload for IncidentStatusChanged event."""

    incident_id: str
    previous_status: str
    new_status: str

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc-001",
                "previous_status": "OPEN",
                "new_status": "INVESTIGATING",
            }
        }


class IncidentSeverityChangedEventData(BaseModel):
    """Data payload for IncidentSeverityChanged event."""

    incident_id: str
    previous_severity: str
    new_severity: str

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc-001",
                "previous_severity": "MEDIUM",
                "new_severity": "HIGH",
            }
        }


class IncidentResolvedEventData(BaseModel):
    """Data payload for IncidentResolved event."""

    incident_id: str
    resolution_summary: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc-001",
                "resolution_summary": "Database indexes were optimized.",
            }
        }


class TimelineCommentAddedEventData(BaseModel):
    """Data payload for TimelineCommentAdded event."""

    incident_id: str
    timeline_entry_id: str
    comment: str

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc-001",
                "timeline_entry_id": "tl-003",
                "comment": "Backend team is investigating database metrics",
            }
        }


class IncidentCreatedEvent(BaseEvent):
    """IncidentCreated domain event."""

    event_type: str = Field(
        default="IncidentCreated", description="Always IncidentCreated"
    )
    data: IncidentCreatedEventData


class IncidentStatusChangedEvent(BaseEvent):
    """IncidentStatusChanged domain event."""

    event_type: str = Field(
        default="IncidentStatusChanged", description="Always IncidentStatusChanged"
    )
    data: IncidentStatusChangedEventData


class IncidentSeverityChangedEvent(BaseEvent):
    """IncidentSeverityChanged domain event."""

    event_type: str = Field(
        default="IncidentSeverityChanged", description="Always IncidentSeverityChanged"
    )
    data: IncidentSeverityChangedEventData


class IncidentResolvedEvent(BaseEvent):
    """IncidentResolved domain event."""

    event_type: str = Field(
        default="IncidentResolved", description="Always IncidentResolved"
    )
    data: IncidentResolvedEventData


class TimelineCommentAddedEvent(BaseEvent):
    """TimelineCommentAdded domain event."""

    event_type: str = Field(
        default="TimelineCommentAdded", description="Always TimelineCommentAdded"
    )
    data: TimelineCommentAddedEventData
