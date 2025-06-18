"""
Routeur principal de l'API.
"""
from fastapi import APIRouter

from app.api.endpoints import health, recipes, agent

api_router = APIRouter()

# Inclusion des endpoints
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
