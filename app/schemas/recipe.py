"""
Schémas Pydantic pour les recettes de cuisine.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, ConfigDict


class Unit(str, Enum):
    """Enumeration for ingredient units."""
    GRAM = "g"
    KILOGRAM = "kg"
    LITER = "l"
    MILLILITER = "ml"
    TEASPOON = "c. à café"
    TABLESPOON = "c. à soupe"
    CUP = "tasse"
    PIECE = "pièce"
    PINCH = "pincée"


class DifficultyLevel(str, Enum):
    """Enumeration for recipe difficulty levels."""
    EASY = "Facile"
    MEDIUM = "Moyen"
    HARD = "Difficile"


class MealType(str, Enum):
    """Enumeration for meal types."""
    STARTER = "Entrée"
    MAIN_COURSE = "Plat principal"
    DESSERT = "Dessert"
    SIDE_DISH = "Accompagnement"
    SNACK = "En-cas"
    DRINK = "Boisson"


class Ingredient(BaseModel):
    """Schema for a single ingredient."""
    name: str = Field(..., min_length=2, max_length=100)
    quantity: float = Field(..., gt=0)
    unit: Unit


class RecipeBase(BaseModel):
    """Base schema for a recipe."""
    title: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    meal_type: List[MealType] = Field(..., min_length=1)
    tags: Optional[List[str]] = Field(None, max_items=20)
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    total_time_minutes: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1)
    ingredients: List[Ingredient] = Field(..., min_length=1)
    steps: List[str] = Field(..., min_length=1)
    main_image_url: Optional[str] = None
    additional_images_urls: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class RecipeCreate(RecipeBase):
    """Schema for creating a new recipe."""
    pass


class Step(BaseModel):
    """Schema for a recipe step."""
    order: int = Field(..., ge=1)
    description: str = Field(..., min_length=5)


class RecipeUpdate(BaseModel):
    """Schema for updating an existing recipe. All fields are optional."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    difficulty: Optional[DifficultyLevel] = None
    meal_type: Optional[MealType] = None
    servings: Optional[int] = Field(None, ge=1, le=50)
    prep_time_minutes: Optional[int] = Field(None, ge=1)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    ingredients: Optional[List[Ingredient]] = Field(None, min_length=1)
    steps: Optional[List[Step]] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    main_image_url: Optional[str] = Field(None, description="URL de l'image principale de la recette")
    additional_images: Optional[List[str]] = Field(default=[], description="URLs des images supplémentaires")

    @validator('steps')
    @classmethod
    def validate_steps_order(cls, v):
        """Valider que les étapes sont dans l'ordre correct."""
        if v is not None:
            orders = [step.order for step in v]
            expected_orders = list(range(1, len(v) + 1))
            
            if sorted(orders) != expected_orders:
                raise ValueError("Les étapes doivent être numérotées de 1 à n sans trous")
        
        return v

    @validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Valider les tags."""
        if v is not None:
            normalized_tags = list(set(tag.lower().strip() for tag in v if tag.strip()))
            return normalized_tags[:10]
        return v


class Recipe(RecipeBase):
    """Modèle complet pour une recette avec métadonnées."""
    id: str = Field(..., description="Identifiant unique de la recette")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de dernière modification")
    total_time_minutes: int = Field(..., description="Temps total (préparation + cuisson)")


class RecipeSearchFilters(BaseModel):
    """Filtres pour la recherche de recettes."""
    difficulty: Optional[DifficultyLevel] = None
    meal_type: Optional[MealType] = None
    max_prep_time: Optional[int] = Field(None, ge=1, description="Temps de préparation maximum")
    max_total_time: Optional[int] = Field(None, ge=1, description="Temps total maximum")
    tags: Optional[List[str]] = None
    ingredient: Optional[str] = Field(None, description="Recherche par ingrédient")


class RecipeList(BaseModel):
    """Modèle pour une liste paginée de recettes."""
    recipes: List[Recipe] = Field(..., description="Liste des recettes")
    total: int = Field(..., description="Nombre total de recettes")
    skip: int = Field(..., description="Nombre d'éléments ignorés")
    limit: int = Field(..., description="Nombre maximum d'éléments retournés")


class ImageURLResponse(BaseModel):
    """Modèle pour une réponse contenant une URL d'image."""
    url: str
    image_type: str
