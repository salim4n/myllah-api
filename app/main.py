"""
Point d'entrée principal de l'application FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_application() -> FastAPI:
    """Créer et configurer l'application FastAPI."""
    app = FastAPI(
        title="Myllah API",
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Configuration CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclusion des routeurs
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
