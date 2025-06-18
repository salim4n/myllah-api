"""
Configuration pour les services Azure.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class AzureSettings(BaseSettings):
    """Configuration pour les services Azure."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Nom du compte de stockage Azure
    azure_storage_account_name: Optional[str] = None
    # Clé du compte de stockage Azure
    azure_storage_account_key: Optional[str] = None
    # Chaîne de connexion complète pour le stockage Azure
    azure_storage_connection_string: Optional[str] = None
    
    # Nom de la table pour les recettes
    recipes_table_name: str = "recipes"
    # Nom du conteneur pour les images
    blob_container_name: str = "recipe-images"

    @property
    def is_azure_configured(self) -> bool:
        """Vérifie si Azure est configuré."""
        return bool(self.azure_storage_connection_string)


# Instance globale des paramètres Azure
azure_settings = AzureSettings()
