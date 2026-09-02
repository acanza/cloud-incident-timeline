"""
Timeline endpoints for retrieving and managing incident timelines.
"""

from fastapi import APIRouter, HTTPException, status
from src.logger import setup_logger
from src.config import Config
from src.services import TimelineService
from src.schemas import (
    TimelineResponseModel,
    TimelineEntryModel,
    TimelineCommentRequestModel,
    TimelineCommentResponseModel,
    ErrorResponseModel,
)
from src.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    TimelineServiceException,
)
from src.http_responses import handle_service_exception, error_response

logger = setup_logger(__name__, Config.LOG_LEVEL)
router = APIRouter(prefix="/incidents", tags=["Timeline"])

# Initialize service
timeline_service = TimelineService()


@router.get(
    "/{incident_id}/timeline",
    response_model=TimelineResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get Incident Timeline",
    description="Retrieve the timeline of events for a specific incident",
    responses={
        200: {"description": "Timeline retrieved successfully"},
        404: {"description": "Incident not found", "model": ErrorResponseModel},
        500: {"description": "Internal server error", "model": ErrorResponseModel},
    },
)
async def get_incident_timeline(incident_id: str) -> dict:
    """
    Retrieve the timeline for a specific incident.

    The timeline contains all events that occurred for the incident,
    ordered chronologically from oldest to newest.

    Args:
        incident_id: ID of the incident

    Returns:
        JSON response with incident_id and list of timeline entries

    Raises:
        HTTPException: If incident not found or other errors occur

    Example:
        GET /incidents/inc-001/timeline

        Response:
        {
          "incident_id": "inc-001",
          "entries": [
            {
              "incident_id": "inc-001",
              "timeline_entry_id": "tl-001",
              "created_at": "2026-07-30T08:00:00Z",
              "message": "Incident created with HIGH severity and OPEN status.",
              "event_type": "IncidentCreated",
              "source_event_id": "evt-001"
            }
          ]
        }
    """
    try:
        # Validate incident_id format
        if not incident_id or not isinstance(incident_id, str):
            raise ValidationError(
                "incident_id must be a non-empty string",
                details={"field": "incident_id"},
            )

        # Get timeline entries
        entries = timeline_service.get_timeline(incident_id)

        logger.info(
            f"Retrieved timeline for incident",
            extra={
                "incident_id": incident_id,
                "entry_count": len(entries),
            },
        )

        # Convert to response format
        entry_dicts = [
            TimelineEntryModel(
                incident_id=entry.incident_id,
                timeline_entry_id=entry.timeline_entry_id,
                created_at=entry.created_at,
                message=entry.message,
                event_type=entry.event_type,
                source_event_id=entry.source_event_id,
            ).model_dump()
            for entry in entries
        ]

        return {
            "incident_id": incident_id,
            "entries": entry_dicts,
        }

    except ValidationError as e:
        raise handle_service_exception(e)

    except TimelineServiceException as e:
        raise handle_service_exception(e)

    except Exception as e:
        logger.error(
            f"Unexpected error retrieving timeline: {str(e)}",
            extra={
                "incident_id": incident_id,
                "error": str(e),
            },
        )
        raise error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve timeline",
            error_code="INTERNAL_ERROR",
        )


@router.post(
    "/{incident_id}/timeline/comments",
    response_model=TimelineCommentResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Add Timeline Comment",
    description="Add a comment to an incident's timeline",
    responses={
        201: {"description": "Comment added successfully"},
        400: {"description": "Invalid request", "model": ErrorResponseModel},
        404: {"description": "Incident not found", "model": ErrorResponseModel},
        500: {"description": "Internal server error", "model": ErrorResponseModel},
    },
)
async def add_timeline_comment(
    incident_id: str,
    request: TimelineCommentRequestModel,
) -> dict:
    """
    Add a comment to an incident's timeline.

    Creates a manual timeline entry from a user comment.
    This is useful for adding notes, status updates, or context to the timeline.

    Args:
        incident_id: ID of the incident
        request: Comment request with comment text and optional user_id

    Returns:
        JSON response with created timeline entry

    Raises:
        HTTPException: If validation fails or service error occurs

    Example:
        POST /incidents/inc-001/timeline/comments

        Request:
        {
          "comment": "Backend team is investigating database metrics",
          "user_id": "user-123"
        }

        Response (201):
        {
          "timeline_entry_id": "tl-003",
          "incident_id": "inc-001",
          "message": "Comment: Backend team is investigating database metrics",
          "created_at": "2026-07-30T08:40:00Z"
        }
    """
    try:
        # Validate incident_id format
        if not incident_id or not isinstance(incident_id, str):
            raise ValidationError(
                "incident_id must be a non-empty string",
                details={"field": "incident_id"},
            )

        # Create comment entry
        entry = timeline_service.create_comment_entry(
            incident_id=incident_id,
            comment=request.comment,
            user_id=request.user_id,
        )

        logger.info(
            f"Comment added to timeline",
            extra={
                "incident_id": incident_id,
                "timeline_entry_id": entry.timeline_entry_id,
                "user_id": request.user_id,
            },
        )

        return {
            "timeline_entry_id": entry.timeline_entry_id,
            "incident_id": entry.incident_id,
            "message": entry.message,
            "created_at": entry.created_at,
        }

    except ValidationError as e:
        raise handle_service_exception(e)

    except TimelineServiceException as e:
        raise handle_service_exception(e)

    except Exception as e:
        logger.error(
            f"Unexpected error adding comment: {str(e)}",
            extra={
                "incident_id": incident_id,
                "error": str(e),
            },
        )
        raise error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to add comment",
            error_code="INTERNAL_ERROR",
        )
