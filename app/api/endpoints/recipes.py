"""
API endpoints for recipes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File

from app.schemas.recipe import (
    Recipe,
    RecipeCreate,
    RecipeUpdate,
    RecipeList,
    ImageURLResponse
)
from app.services.recipe_service import get_recipe_service, RecipeService
from app.services.image_service import get_image_service, ImageService

router = APIRouter()


@router.post(
    "/",
    response_model=Recipe,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle recette",
    description="Ajouter une nouvelle recette à la base de données"
)
async def create_recipe(
    recipe: RecipeCreate,
    service: RecipeService = Depends(get_recipe_service)
) -> Recipe:
    """Créer une nouvelle recette."""
    try:
        return await service.create_recipe(recipe)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{recipe_id}",
    response_model=Recipe,
    summary="Récupérer une recette par ID",
    description="Obtenir les détails complets d'une recette par son ID"
)
async def get_recipe(
    recipe_id: str,
    service: RecipeService = Depends(get_recipe_service)
) -> Recipe:
    """Récupérer une recette par son ID."""
    recipe = await service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    return recipe


@router.get(
    "/",
    response_model=RecipeList,
    summary="Lister les recettes",
    description="Récupérer une liste paginée de recettes"
)
async def get_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: RecipeService = Depends(get_recipe_service)
) -> RecipeList:
    """Lister les recettes avec pagination."""
    recipes, total = await service.get_all_recipes(skip=skip, limit=limit)
    return RecipeList(
        recipes=recipes,
        total=total,
        skip=skip,
        limit=limit
    )


@router.patch(
    "/{recipe_id}",
    response_model=Recipe,
    summary="Mettre à jour une recette",
    description="Mettre à jour une recette existante"
)
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    service: RecipeService = Depends(get_recipe_service)
) -> Recipe:
    """Mettre à jour une recette."""
    updated_recipe = await service.update_recipe(recipe_id, recipe_update)
    if not updated_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    return updated_recipe


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une recette",
    description="Supprimer une recette par son ID"
)
async def delete_recipe(
    recipe_id: str,
    service: RecipeService = Depends(get_recipe_service)
) -> None:
    """Supprimer une recette."""
    success = await service.delete_recipe(recipe_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )


@router.post(
    "/{recipe_id}/images/main",
    response_model=ImageURLResponse,
    summary="Uploader l'image principale d'une recette",
    description="Uploader ou remplacer l'image principale d'une recette"
)
async def upload_recipe_image(
    recipe_id: str,
    file: UploadFile = File(...),
    image_type: str = "main",
    recipe_service: RecipeService = Depends(get_recipe_service),
    image_service: ImageService = Depends(get_image_service)
) -> ImageURLResponse:
    """Uploader l'image principale d'une recette."""
    recipe = await recipe_service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    try:
        image_url = await image_service.upload_image(
            file=file,
            recipe_id=recipe_id,
            image_type=image_type
        )
        updated_recipe = await recipe_service.add_image_url(
            recipe_id=recipe_id,
            image_url=image_url,
            image_type=image_type
        )
        return ImageURLResponse(url=image_url, image_type=image_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{recipe_id}/images/additional",
    response_model=ImageURLResponse,
    summary="Ajouter une image additionnelle à une recette",
    description="Ajouter une nouvelle image à la galerie d'une recette"
)
async def upload_additional_recipe_image(
    recipe_id: str,
    file: UploadFile = File(...),
    image_type: str = "additional",
    recipe_service: RecipeService = Depends(get_recipe_service),
    image_service: ImageService = Depends(get_image_service)
) -> ImageURLResponse:
    """Ajouter une image additionnelle à une recette."""
    recipe = await recipe_service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    try:
        image_url = await image_service.upload_image(
            file=file,
            recipe_id=recipe_id,
            image_type=image_type
        )
        updated_recipe = await recipe_service.add_image_url(
            recipe_id=recipe_id,
            image_url=image_url,
            image_type=image_type
        )
        return ImageURLResponse(url=image_url, image_type=image_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{recipe_id}/images",
    response_model=List[ImageURLResponse],
    summary="Lister les images d'une recette",
    description="Obtenir les URLs de toutes les images (principale et additionnelles) d'une recette"
)
async def get_recipe_images(
    recipe_id: str,
    service: RecipeService = Depends(get_recipe_service)
) -> List[ImageURLResponse]:
    """Lister toutes les images d'une recette."""
    recipe = await service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    images = []
    if recipe.main_image_url:
        images.append(ImageURLResponse(url=recipe.main_image_url, image_type="main"))
    for url in recipe.additional_images_urls:
        images.append(ImageURLResponse(url=url, image_type="additional"))

    return images


@router.delete(
    "/{recipe_id}/images",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer toutes les images d'une recette",
    description="Supprimer l'image principale et toutes les images additionnelles d'une recette"
)
async def delete_recipe_images(
    recipe_id: str,
    recipe_service: RecipeService = Depends(get_recipe_service),
    image_service: ImageService = Depends(get_image_service)
) -> None:
    """Supprimer toutes les images d'une recette."""
    recipe = await recipe_service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if recipe.main_image_url:
        try:
            await image_service.delete_image(recipe.main_image_url)
        except Exception as e:
            print(f"Error deleting main image {recipe.main_image_url}: {e}")

    for url in recipe.additional_images_urls:
        try:
            await image_service.delete_image(url)
        except Exception as e:
            print(f"Error deleting additional image {url}: {e}")

    await recipe_service.clear_image_urls(recipe_id)
    return None
