"""Incident API endpoints."""

from fastapi import APIRouter, status, HTTPException
from typing import Optional

from ..context import get_correlation_id
from ..logger import get_structured_logger
from ..schemas import (
    CreateIncidentRequestSchema,
    UpdateStatusRequestSchema,
    UpdateSeverityRequestSchema,
    IncidentSchema,
    IncidentsListResponseSchema
)
from ..utils import (
    ValidationError,
    validate_create_incident_request,
    validate_status_change,
    validate_severity_change
)
from ..services.incident_service import incident_service
from ..services.event_publisher import event_publisher
from ..constants import SERVICE_NAME


logger = get_structured_logger(__name__, service_name=SERVICE_NAME)

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Incident not found"},
        500: {"description": "Internal server error"}
    }
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=IncidentSchema,
    summary="Create a new incident"
)
async def create_incident(request: CreateIncidentRequestSchema) -> IncidentSchema:
    """
    Create a new incident.
    
    This endpoint:
    1. Validates the request
    2. Creates an incident in storage
    3. Publishes IncidentCreated event
    4. Returns the created incident
    """
    correlation_id = get_correlation_id()
    
    # Validate request
    is_valid, error = validate_create_incident_request(
        request.title,
        request.description,
        request.severity
    )
    if not is_valid:
        logger.warning(
            "Invalid create incident request",
            extra={
                'correlation_id': correlation_id,
                'errors': error.details if error else []
            }
        )
        raise error
    
    try:
        # Create incident
        incident, event_type = incident_service.create_incident(
            title=request.title,
            description=request.description,
            severity=request.severity
        )
        
        # Publish event
        event_publisher.publish_event(
            event_type=event_type,
            event_data={
                "incident_id": incident.incident_id,
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity,
                "status": incident.status
            },
            actor_user_id=request.actor.user_id,
            actor_email=request.actor.email
        )
        
        logger.info(
            "Incident created",
            extra={
                'correlation_id': correlation_id,
                'incident_id': incident.incident_id,
                'severity': incident.severity
            }
        )
        
        return IncidentSchema(**incident.to_dict())
    
    except Exception as e:
        logger.error(
            f"Error creating incident: {str(e)}",
            extra={
                'correlation_id': correlation_id,
                'exception_type': type(e).__name__
            }
        )
        raise


@router.get(
    "",
    response_model=IncidentsListResponseSchema,
    summary="List all incidents"
)
async def list_incidents() -> IncidentsListResponseSchema:
    """
    List all incidents.
    
    Returns a list of all incidents in the system.
    """
    correlation_id = get_correlation_id()
    
    try:
        incidents = incident_service.list_incidents()
        
        logger.debug(
            "Listed incidents",
            extra={
                'correlation_id': correlation_id,
                'count': len(incidents)
            }
        )
        
        incident_schemas = [
            IncidentSchema(**incident.to_dict())
            for incident in incidents
        ]
        
        return IncidentsListResponseSchema(items=incident_schemas)
    
    except Exception as e:
        logger.error(
            f"Error listing incidents: {str(e)}",
            extra={
                'correlation_id': correlation_id,
                'exception_type': type(e).__name__
            }
        )
        raise


@router.get(
    "/{incident_id}",
    response_model=IncidentSchema,
    summary="Get incident by ID"
)
async def get_incident(incident_id: str) -> IncidentSchema:
    """
    Get a specific incident by its ID.
    
    Returns the incident details or 404 if not found.
    """
    correlation_id = get_correlation_id()
    
    try:
        incident = incident_service.get_incident(incident_id)
        
        if not incident:
            logger.warning(
                "Incident not found",
                extra={
                    'correlation_id': correlation_id,
                    'incident_id': incident_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        logger.debug(
            "Retrieved incident",
            extra={
                'correlation_id': correlation_id,
                'incident_id': incident_id
            }
        )
        
        return IncidentSchema(**incident.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving incident: {str(e)}",
            extra={
                'correlation_id': correlation_id,
                'incident_id': incident_id,
                'exception_type': type(e).__name__
            }
        )
        raise


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentSchema,
    summary="Update incident status"
)
async def update_incident_status(
    incident_id: str,
    request: UpdateStatusRequestSchema
) -> IncidentSchema:
    """
    Update the status of an incident.
    
    This endpoint:
    1. Validates the new status
    2. Updates the incident status
    3. Publishes appropriate event (IncidentStatusChanged or IncidentResolved)
    4. Returns the updated incident
    """
    correlation_id = get_correlation_id()
    
    # Validate request
    is_valid, error = validate_status_change(request.status)
    if not is_valid:
        logger.warning(
            "Invalid status change request",
            extra={
                'correlation_id': correlation_id,
                'incident_id': incident_id,
                'errors': error.details if error else []
            }
        )
        raise error
    
    try:
        incident, event_type = incident_service.update_incident_status(
            incident_id,
            request.status
        )
        
        if not incident:
            logger.warning(
                "Incident not found for status update",
                extra={
                    'correlation_id': correlation_id,
                    'incident_id': incident_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        # Only publish event if status actually changed
        if event_type:
            event_publisher.publish_event(
                event_type=event_type,
                event_data={
                    "incident_id": incident.incident_id,
                    "old_status": None,  # TODO: Track previous status in Phase 3
                    "new_status": incident.status
                },
                actor_user_id=request.actor.user_id,
                actor_email=request.actor.email
            )
            
            logger.info(
                "Incident status updated",
                extra={
                    'correlation_id': correlation_id,
                    'incident_id': incident_id,
                    'event_type': event_type,
                    'new_status': incident.status
                }
            )
        
        return IncidentSchema(**incident.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating incident status: {str(e)}",
            extra={
                'correlation_id': correlation_id,
                'incident_id': incident_id,
                'exception_type': type(e).__name__
            }
        )
        raise


@router.patch(
    "/{incident_id}/severity",
    response_model=IncidentSchema,
    summary="Update incident severity"
)
async def update_incident_severity(
    incident_id: str,
    request: UpdateSeverityRequestSchema
) -> IncidentSchema:
    """
    Update the severity of an incident.
    
    This endpoint:
    1. Validates the new severity
    2. Updates the incident severity
    3. Publishes IncidentSeverityChanged event
    4. Returns the updated incident
    """
    correlation_id = get_correlation_id()
    
    # Validate request
    is_valid, error = validate_severity_change(request.severity)
    if not is_valid:
        logger.warning(
            "Invalid severity change request",
            extra={
                'correlation_id': correlation_id,
                'incident_id': incident_id,
                'errors': error.details if error else []
            }
        )
        raise error
    
    try:
        incident, event_type = incident_service.update_incident_severity(
            incident_id,
            request.severity
        )
        
        if not incident:
            logger.warning(
                "Incident not found for severity update",
                extra={
                    'correlation_id': correlation_id,
                    'incident_id': incident_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        # Only publish event if severity actually changed
        if event_type:
            event_publisher.publish_event(
                event_type=event_type,
                event_data={
                    "incident_id": incident.incident_id,
                    "old_severity": None,  # TODO: Track previous severity in Phase 3
                    "new_severity": incident.severity
                },
                actor_user_id=request.actor.user_id,
                actor_email=request.actor.email
            )
            
            logger.info(
                "Incident severity updated",
                extra={
                    'correlation_id': correlation_id,
                    'incident_id': incident_id,
                    'event_type': event_type,
                    'new_severity': incident.severity
                }
            )
        
        return IncidentSchema(**incident.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating incident severity: {str(e)}",
            extra={
                'correlation_id': correlation_id,
                'incident_id': incident_id,
                'exception_type': type(e).__name__
            }
        )
        raise
