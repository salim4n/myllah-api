"""
Endpoints de santé de l'application.
"""
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Modèle de réponse pour le health check."""
    status: str
    message: str


router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Vérifier l'état de santé de l'API"
)
def health_check() -> HealthResponse:
    """Endpoint de vérification de santé."""
    return HealthResponse(
        status="healthy",
        message="L'API fonctionne correctement"
    )


@router.get(
    "/ready",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Vérifier si l'API est prête à recevoir du trafic"
)
def readiness_check() -> Dict[str, Any]:
    """Endpoint de vérification de disponibilité."""
    return {
        "status": "ready",
        "message": "L'API est prête à recevoir du trafic",
        "version": "0.1.0"
    }
