"""
Configuration de l'application.
"""
from typing import List

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de l'application."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignorer les variables d'environnement supplémentaires
    )
    
    PROJECT_NAME: str = "Myllah API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "API FastAPI avec architecture clean"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Base de données et services externes
    # Ajouter ici les variables d'environnement nécessaires


settings = Settings()
