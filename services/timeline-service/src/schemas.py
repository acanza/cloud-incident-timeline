"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ActorModel(BaseModel):
    """Actor information in events."""

    user_id: str
    email: Optional[str] = None


class EventEnvelopeModel(BaseModel):
    """Event envelope structure from EventBridge/SQS."""

    version: str
    event_id: str
    event_type: str
    source: str
    occurred_at: str
    correlation_id: str
    actor: ActorModel
    data: Dict[str, Any]


class TimelineEntryModel(BaseModel):
    """Timeline entry data model."""

    incident_id: str
    timeline_entry_id: str
    created_at: str
    message: str
    event_type: str
    source_event_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc-001",
                "timeline_entry_id": "tl-001",
                "created_at": "2026-07-30T08:00:00Z",
                "message": "Incident created with HIGH severity and OPEN status.",
                "event_type": "IncidentCreated",
                "source_event_id": "evt-001",
            }
        }


class TimelineResponseModel(BaseModel):
    """Response containing timeline entries for an incident."""

    incident_id: str
    entries: List[TimelineEntryModel] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc-001",
                "entries": [
                    {
                        "incident_id": "inc-001",
                        "timeline_entry_id": "tl-001",
                        "created_at": "2026-07-30T08:00:00Z",
                        "message": "Incident created with HIGH severity and OPEN status.",
                        "event_type": "IncidentCreated",
                        "source_event_id": "evt-001",
                    }
                ],
            }
        }


class HealthResponseModel(BaseModel):
    """Health check response."""

    status: str
    service: str

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "service": "timeline-service",
            }
        }


class ErrorResponseModel(BaseModel):
    """Error response."""

    message: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Validation error",
                "details": {
                    "field": "incident_id",
                    "reason": "Invalid format",
                },
            }
        }


class TimelineCommentRequestModel(BaseModel):
    """Request body for adding a timeline comment."""

    comment: str = Field(..., min_length=1, max_length=1000)
    user_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "comment": "Backend team is investigating database metrics",
                "user_id": "user-123",
            }
        }


class TimelineCommentResponseModel(BaseModel):
    """Response for created timeline comment."""

    timeline_entry_id: str
    incident_id: str
    message: str
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "timeline_entry_id": "tl-003",
                "incident_id": "inc-001",
                "message": "Backend team is investigating database metrics",
                "created_at": "2026-07-30T08:40:00Z",
            }
        }
