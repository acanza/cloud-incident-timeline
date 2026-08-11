"""
Pydantic schemas for request/response and event envelopes.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ActorSchema(BaseModel):
    """Represents the actor that triggers an action."""
    user_id: str = Field(..., description="User or system ID")
    email: Optional[str] = Field(None, description="User email (optional)")

    model_config = {"json_schema_extra": {"example": {
        "user_id": "user-001",
        "email": "user@example.com"
    }}}


class EventDataSchema(BaseModel):
    """Flexible base class for event data."""
    class Config:
        extra = "allow"


class EventEnvelopeSchema(BaseModel):
    """Standard envelope for all events published to EventBridge."""
    version: str = Field(..., description="Event schema version")
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type (IncidentCreated, etc.)")
    source: str = Field(..., description="Service that emitted the event")
    occurred_at: str = Field(..., description="UTC timestamp when the event occurred")
    correlation_id: str = Field(..., description="ID to trace the request flow")
    actor: ActorSchema = Field(..., description="User or system that triggered the action")
    data: Dict[str, Any] = Field(..., description="Event-specific data")

    model_config = {"json_schema_extra": {"example": {
        "version": "1.0",
        "event_id": "evt-001",
        "event_type": "IncidentCreated",
        "source": "incident-service",
        "occurred_at": "2026-07-30T08:00:00Z",
        "correlation_id": "corr-001",
        "actor": {
            "user_id": "user-001",
            "email": "user@example.com"
        },
        "data": {"incident_id": "inc-001", "severity": "HIGH"}
    }}}


class ErrorDetailSchema(BaseModel):
    """Error validation detail."""
    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")


class ErrorResponseSchema(BaseModel):
    """Standard error response format."""
    message: str = Field(..., description="Main error message")
    details: Optional[list[ErrorDetailSchema]] = Field(
        None,
        description="Additional error details (e.g., validation)"
    )

    model_config = {"json_schema_extra": {"example": {
        "message": "Validation error",
        "details": [
            {"field": "severity", "message": "Must be one of: LOW, MEDIUM, HIGH, CRITICAL"}
        ]
    }}}


class IncidentSchema(BaseModel):
    """Incident model."""
    incident_id: str = Field(..., description="Unique incident identifier")
    title: str = Field(..., description="Incident title")
    description: str = Field(..., description="Detailed description")
    severity: str = Field(..., description="Severity: LOW, MEDIUM, HIGH, CRITICAL")
    status: str = Field(..., description="Status: OPEN, INVESTIGATING, RESOLVED, CLOSED")
    created_at: str = Field(..., description="UTC creation timestamp")
    updated_at: str = Field(..., description="UTC last update timestamp")

    model_config = {"json_schema_extra": {"example": {
        "incident_id": "inc-001",
        "title": "API latency spike",
        "description": "The public API is responding slowly",
        "severity": "HIGH",
        "status": "OPEN",
        "created_at": "2026-07-30T08:00:00Z",
        "updated_at": "2026-07-30T08:00:00Z"
    }}}


class CreateIncidentRequestSchema(BaseModel):
    """Schema for creating a new incident."""
    title: str = Field(..., min_length=1, description="Incident title")
    description: str = Field(..., min_length=1, description="Incident description")
    severity: str = Field(..., description="Severity: LOW, MEDIUM, HIGH, CRITICAL")
    actor: ActorSchema = Field(..., description="User that creates the incident")

    model_config = {"json_schema_extra": {"example": {
        "title": "API latency spike",
        "description": "The public API is responding slowly",
        "severity": "HIGH",
        "actor": {
            "user_id": "user-001",
            "email": "user@example.com"
        }
    }}}


class UpdateStatusRequestSchema(BaseModel):
    """Schema for changing incident status."""
    status: str = Field(..., description="New status: OPEN, INVESTIGATING, RESOLVED, CLOSED")
    actor: ActorSchema = Field(..., description="User that makes the change")

    model_config = {"json_schema_extra": {"example": {
        "status": "INVESTIGATING",
        "actor": {
            "user_id": "user-001",
            "email": "user@example.com"
        }
    }}}


class UpdateSeverityRequestSchema(BaseModel):
    """Schema for changing incident severity."""
    severity: str = Field(..., description="New severity: LOW, MEDIUM, HIGH, CRITICAL")
    actor: ActorSchema = Field(..., description="User that makes the change")

    model_config = {"json_schema_extra": {"example": {
        "severity": "CRITICAL",
        "actor": {
            "user_id": "user-001",
            "email": "user@example.com"
        }
    }}}


class HealthCheckResponseSchema(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")

    model_config = {"json_schema_extra": {"example": {
        "status": "ok",
        "service": "incident-service"
    }}}


class IncidentsListResponseSchema(BaseModel):
    """Schema for incident list response."""
    items: list[IncidentSchema] = Field(..., description="List of incidents")

    model_config = {"json_schema_extra": {"example": {
        "items": []
    }}}
