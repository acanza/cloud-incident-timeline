"""
Schemas Pydantic para request/response y event envelopes.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ActorSchema(BaseModel):
    """Representa al actor que desencadena una acción."""
    user_id: str = Field(..., description="ID del usuario o sistema")
    email: Optional[str] = Field(None, description="Email del usuario (opcional)")

    model_config = {"json_schema_extra": {"example": {
        "user_id": "user-001",
        "email": "user@example.com"
    }}}


class EventDataSchema(BaseModel):
    """Clase base flexible para datos de eventos."""
    class Config:
        extra = "allow"


class EventEnvelopeSchema(BaseModel):
    """Envelope estándar para todos los eventos publicados a EventBridge."""
    version: str = Field(..., description="Versión del schema de evento")
    event_id: str = Field(..., description="ID único del evento")
    event_type: str = Field(..., description="Tipo de evento (IncidentCreated, etc.)")
    source: str = Field(..., description="Servicio que emitió el evento")
    occurred_at: str = Field(..., description="Timestamp UTC cuando ocurrió el evento")
    correlation_id: str = Field(..., description="ID para trazar el flujo de la solicitud")
    actor: ActorSchema = Field(..., description="Usuario o sistema que desencadenó la acción")
    data: Dict[str, Any] = Field(..., description="Datos específicos del evento")

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
    """Detalle de un error de validación."""
    field: str = Field(..., description="Campo con error")
    message: str = Field(..., description="Mensaje de error")


class ErrorResponseSchema(BaseModel):
    """Formato estándar de respuesta de error."""
    message: str = Field(..., description="Mensaje de error principal")
    details: Optional[list[ErrorDetailSchema]] = Field(
        None,
        description="Detalles adicionales de errores (ej: validación)"
    )

    model_config = {"json_schema_extra": {"example": {
        "message": "Validation error",
        "details": [
            {"field": "severity", "message": "Must be one of: LOW, MEDIUM, HIGH, CRITICAL"}
        ]
    }}}


class IncidentSchema(BaseModel):
    """Modelo de un incidente."""
    incident_id: str = Field(..., description="ID único del incidente")
    title: str = Field(..., description="Título del incidente")
    description: str = Field(..., description="Descripción detallada")
    severity: str = Field(..., description="Severidad: LOW, MEDIUM, HIGH, CRITICAL")
    status: str = Field(..., description="Estado: OPEN, INVESTIGATING, RESOLVED, CLOSED")
    created_at: str = Field(..., description="Timestamp UTC de creación")
    updated_at: str = Field(..., description="Timestamp UTC de última actualización")

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
    """Schema para crear un nuevo incidente."""
    title: str = Field(..., min_length=1, description="Título del incidente")
    description: str = Field(..., min_length=1, description="Descripción del incidente")
    severity: str = Field(..., description="Severidad: LOW, MEDIUM, HIGH, CRITICAL")
    actor: ActorSchema = Field(..., description="Usuario que crea el incidente")

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
    """Schema para cambiar el estado de un incidente."""
    status: str = Field(..., description="Nuevo estado: OPEN, INVESTIGATING, RESOLVED, CLOSED")
    actor: ActorSchema = Field(..., description="Usuario que realiza el cambio")

    model_config = {"json_schema_extra": {"example": {
        "status": "INVESTIGATING",
        "actor": {
            "user_id": "user-001",
            "email": "user@example.com"
        }
    }}}


class UpdateSeverityRequestSchema(BaseModel):
    """Schema para cambiar la severidad de un incidente."""
    severity: str = Field(..., description="Nueva severidad: LOW, MEDIUM, HIGH, CRITICAL")
    actor: ActorSchema = Field(..., description="Usuario que realiza el cambio")

    model_config = {"json_schema_extra": {"example": {
        "severity": "CRITICAL",
        "actor": {
            "user_id": "user-001",
            "email": "user@example.com"
        }
    }}}


class HealthCheckResponseSchema(BaseModel):
    """Schema para respuesta de health check."""
    status: str = Field(..., description="Estado de salud del servicio")
    service: str = Field(..., description="Nombre del servicio")

    model_config = {"json_schema_extra": {"example": {
        "status": "ok",
        "service": "incident-service"
    }}}


class IncidentsListResponseSchema(BaseModel):
    """Schema para respuesta de lista de incidentes."""
    items: list[IncidentSchema] = Field(..., description="Lista de incidentes")

    model_config = {"json_schema_extra": {"example": {
        "items": []
    }}}
