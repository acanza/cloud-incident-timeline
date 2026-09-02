"""
Health check endpoints for timeline service.
"""

from fastapi import APIRouter
from src.config import Config
from src.schemas import HealthResponseModel

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponseModel,
    summary="Health Check",
    description="Check if the timeline service is running and healthy",
)
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        JSON response with service status and name

    Example:
        GET /health
        Response:
        {
          "status": "ok",
          "service": "timeline-service"
        }
    """
    return {
        "status": "ok",
        "service": Config.SERVICE_NAME,
    }
