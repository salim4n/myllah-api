"""
Service pour la gestion des images avec Azure Blob Storage.
"""
import uuid
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
from io import BytesIO

from app.core.azure_config import azure_settings


class ImageService:
    """Service pour gérer les images dans Azure Blob Storage."""
    
    def __init__(self):
        """Initialiser le service avec la connexion Azure Blob Storage."""
        self.container_name = azure_settings.blob_container_name
        self.blob_service_client: Optional[BlobServiceClient] = None
        
        # Initialiser seulement si Azure est configuré
        if azure_settings.is_azure_configured:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                azure_settings.azure_storage_connection_string
            )
            # Créer le conteneur s'il n'existe pas
            try:
                self.blob_service_client.create_container(self.container_name, public_access="blob")
            except Exception:
                # Le conteneur existe déjà ou erreur de permissions
                pass
    
    async def upload_image(
        self,
        file: UploadFile,
        recipe_id: str,
        image_type: str = "additional"
    ) -> str:
        """
        Uploader une image pour une recette.
        
        Args:
            file: Fichier image à uploader
            recipe_id: ID de la recette
            image_type: Type d'image ("main" ou "additional")
            
        Returns:
            URL de l'image uploadée
        """
        if not self.blob_service_client:
            raise RuntimeError("Azure n'est pas configuré")
            
        if not self._is_valid_image_file(file.filename):
            raise HTTPException(status_code=400, detail="Type de fichier non supporté")
        
        # Générer un nom unique pour le blob
        file_extension = file.filename.split('.')[-1].lower()
        unique_id = str(uuid.uuid4())[:8]
        blob_name = f"recipes/{recipe_id}/{image_type}_{unique_id}.{file_extension}"
        
        try:
            # Lire le contenu du fichier
            content = await file.read()
            
            # Créer le blob client et uploader
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(content, overwrite=True)
            
            return blob_client.url
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'upload de l'image: {str(e)}"
            )
    
    async def delete_image(self, image_url: str) -> bool:
        """
        Supprimer une image par son URL.
        
        Args:
            image_url: URL de l'image à supprimer
            
        Returns:
            True si supprimée avec succès, False sinon
        """
        if not self.blob_service_client:
            raise RuntimeError("Azure n'est pas configuré")
            
        try:
            blob_name = self._extract_blob_name_from_url(image_url)
            if not blob_name:
                return False
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            return True
            
        except ResourceNotFoundError:
            return False
        except Exception as e:
            print(f"Erreur lors de la suppression de l'image: {e}")
            return False
    
    async def list_recipe_images(self, recipe_id: str) -> List[str]:
        """
        Lister toutes les images d'une recette.
        
        Args:
            recipe_id: ID de la recette
            
        Returns:
            Liste des URLs des images
        """
        if not self.blob_service_client:
            raise RuntimeError("Azure n'est pas configuré")
            
        try:
            blob_prefix = f"recipes/{recipe_id}/"
            blobs = self.blob_service_client.get_container_client(
                self.container_name
            ).list_blobs(name_starts_with=blob_prefix)
            
            image_urls = []
            for blob in blobs:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob.name
                )
                image_urls.append(blob_client.url)
            
            return image_urls
            
        except Exception as e:
            print(f"Erreur lors de la récupération des images: {e}")
            return []
    
    async def delete_all_recipe_images(self, recipe_id: str) -> int:
        """
        Supprimer toutes les images d'une recette.
        
        Args:
            recipe_id: ID de la recette
            
        Returns:
            Nombre d'images supprimées
        """
        if not self.blob_service_client:
            raise RuntimeError("Azure n'est pas configuré")
            
        try:
            image_urls = await self.list_recipe_images(recipe_id)
            deleted_count = 0
            
            for image_url in image_urls:
                if await self.delete_image(image_url):
                    deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            print(f"Erreur lors de la suppression des images: {e}")
            return 0
    
    def _is_valid_image_file(self, filename: Optional[str]) -> bool:
        """Vérifier si le fichier est une image valide."""
        if not filename:
            return False
        
        allowed_extensions = {'jpg', 'jpeg', 'png', 'webp'}
        file_extension = filename.split('.')[-1].lower()
        return file_extension in allowed_extensions
    
    def _extract_blob_name_from_url(self, image_url: str) -> Optional[str]:
        """Extraire le nom du blob de l'URL."""
        try:
            # L'URL a le format: https://account.blob.core.windows.net/container/blob_name
            parts = image_url.split('/')
            if len(parts) >= 2:
                # Récupérer tout après le nom du conteneur
                container_index = -1
                for i, part in enumerate(parts):
                    if part == self.container_name:
                        container_index = i
                        break
                
                if container_index != -1 and container_index + 1 < len(parts):
                    return '/'.join(parts[container_index + 1:])
            
            return None
        except Exception:
            return None


# Fonction factory pour l'injection de dépendances
def get_image_service() -> ImageService:
    """Retourne une instance du service d'images pour l'injection de dépendances."""
    return ImageService()

# Pour la compatibilité avec le code existant
image_service = ImageService()
