"""
Event data models for domain events consumed from SQS.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict


class ActorInfo(BaseModel):
    """Information about who triggered the action."""

    user_id: str = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="User name")
    email: Optional[str] = Field(None, description="User email")

    model_config = ConfigDict(extra="allow")


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
    correlation_id: str = Field(..., description="ID for tracing request flow across services")
    actor: ActorInfo = Field(..., description="Who or what triggered this action")
    data: Dict[str, Any] = Field(..., description="Event-specific payload")

    model_config = ConfigDict(extra="allow")


class IncidentCreatedEventData(BaseModel):
    """Data payload for IncidentCreated event."""

    incident_id: str = Field(..., description="Incident ID")
    title: str = Field(..., description="Incident title")
    description: Optional[str] = Field(None, description="Incident description")
    severity: str = Field(..., description="Incident severity (LOW, MEDIUM, HIGH, CRITICAL)")
    status: str = Field(..., description="Incident status")

    model_config = ConfigDict(extra="allow")


class IncidentStatusChangedEventData(BaseModel):
    """Data payload for IncidentStatusChanged event."""

    incident_id: str = Field(..., description="Incident ID")
    previous_status: str = Field(..., description="Previous status")
    new_status: str = Field(..., description="New status")

    model_config = ConfigDict(extra="allow")


class IncidentSeverityChangedEventData(BaseModel):
    """Data payload for IncidentSeverityChanged event."""

    incident_id: str = Field(..., description="Incident ID")
    previous_severity: str = Field(..., description="Previous severity")
    new_severity: str = Field(..., description="New severity")

    model_config = ConfigDict(extra="allow")


class IncidentResolvedEventData(BaseModel):
    """Data payload for IncidentResolved event."""

    incident_id: str = Field(..., description="Incident ID")
    resolution_summary: Optional[str] = Field(None, description="Resolution summary")

    model_config = ConfigDict(extra="allow")


# Typed event classes
class IncidentCreatedEvent(BaseEvent):
    """IncidentCreated domain event."""

    data: IncidentCreatedEventData


class IncidentStatusChangedEvent(BaseEvent):
    """IncidentStatusChanged domain event."""

    data: IncidentStatusChangedEventData


class IncidentSeverityChangedEvent(BaseEvent):
    """IncidentSeverityChanged domain event."""

    data: IncidentSeverityChangedEventData


class IncidentResolvedEvent(BaseEvent):
    """IncidentResolved domain event."""

    data: IncidentResolvedEventData
