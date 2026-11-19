import logging
from typing import Any

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from musigree.app import fastapi_app

log = logging.getLogger(__name__)
"""
The logger for this module.
"""

router = APIRouter(tags=["healthcheck"])

HEALTH_STATUS_OK = "OK"
"""Status returned once application startup has finished."""

HEALTH_STATUS_NOT_READY = "NOT_READY"
"""Status returned while application startup is still in progress."""


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = HEALTH_STATUS_OK


# Declared as FastAPI's responses type. A bare literal is inferred with Literal
# keys, and dict is invariant, so that narrower type is not accepted.
HEALTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": HealthCheck,
        "description": "Application startup has not finished",
    },
}


@router.get(
    "/health",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
    responses=HEALTH_RESPONSES,
)
def get_health(response: Response) -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used by Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).

    The response follows ``fastapi_app.health_ok``, which stays false until application
    startup finishes.

    Returns:
        HealthCheck: ``OK`` with HTTP 200 after startup, otherwise ``NOT_READY``
        with HTTP 503.
    """
    if fastapi_app.health_ok:
        return HealthCheck(status=HEALTH_STATUS_OK)

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthCheck(status=HEALTH_STATUS_NOT_READY)
