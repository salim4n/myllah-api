"""
Service pour la gestion des recettes avec Azure Table Storage.
"""
from datetime import datetime, UTC
from typing import List, Optional, Tuple
import uuid
import json

from azure.data.tables import TableServiceClient, TableEntity, TableClient
from azure.core.exceptions import ResourceNotFoundError

from app.core.azure_config import azure_settings
from app.schemas.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeSearchFilters


class RecipeService:
    """Service pour la gestion des recettes avec Azure Table Storage."""
    
    def __init__(self):
        """Initialiser le service avec la connexion Azure Table Storage."""
        self.table_name = azure_settings.recipes_table_name
        self.table_client: Optional[TableClient] = None
        
        # Initialiser seulement si Azure est configuré
        if azure_settings.is_azure_configured:
            self.table_service_client = TableServiceClient.from_connection_string(
                azure_settings.azure_storage_connection_string
            )
            # Créer la table si elle n'existe pas
            self.table_service_client.create_table_if_not_exists(self.table_name)
            self.table_client = self.table_service_client.get_table_client(self.table_name)
    
    def _ensure_table_exists(self) -> None:
        """S'assurer que la table existe."""
        try:
            if self.table_client:
                self.table_client.create_table_if_not_exists(self.table_name)
        except Exception as e:
            print(f"Erreur lors de la création de la table: {e}")
    
    def _recipe_to_entity(self, recipe: Recipe) -> TableEntity:
        """Convertir une recette en entité Table Storage."""
        entity = TableEntity()
        entity["PartitionKey"] = "recipe"
        entity["RowKey"] = recipe.id
        entity["title"] = recipe.title
        entity["description"] = recipe.description or ""
        entity["difficulty"] = recipe.difficulty
        entity["meal_type"] = json.dumps([mt for mt in recipe.meal_type])
        entity["servings"] = recipe.servings
        entity["prep_time_minutes"] = recipe.prep_time_minutes
        entity["cook_time_minutes"] = recipe.cook_time_minutes or 0
        entity["total_time_minutes"] = recipe.total_time_minutes
        entity["created_at"] = recipe.created_at
        entity["updated_at"] = recipe.updated_at
        
        # Sérialiser les listes complexes en JSON
        entity["ingredients"] = json.dumps([ing.model_dump() for ing in recipe.ingredients])
        entity["steps"] = json.dumps(recipe.steps)
        entity["tags"] = json.dumps(recipe.tags or [])
        
        # Ajouter les URLs d'images
        if recipe.main_image_url:
            entity["main_image_url"] = recipe.main_image_url
        if recipe.additional_images:
            entity["additional_images"] = json.dumps(recipe.additional_images)
        
        return entity
    
    def _entity_to_recipe(self, entity: TableEntity) -> Recipe:
        """Convertir une entité Table Storage en recette."""
        from app.schemas.recipe import DifficultyLevel, MealType, Ingredient, Step
        
        # Fonction utilitaire pour parser le JSON de manière sécurisée
        def safe_json_loads(json_str, default_value):
            if not json_str:
                return default_value
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"Erreur de décodage JSON: {json_str}")
                return default_value
        
        # Désérialiser les listes JSON avec gestion des erreurs
        ingredients_data = safe_json_loads(entity.get("ingredients", "[]"), [])
        steps_data_raw = safe_json_loads(entity.get("steps", "[]"), [])
        tags_data = safe_json_loads(entity.get("tags", "[]"), [])
        
        # Convertir les étapes de dictionnaires en chaînes de caractères
        steps_data = []
        for step in steps_data_raw:
            try:
                if isinstance(step, dict):
                    # Si c'est un dictionnaire avec order et description, le convertir en chaîne
                    desc = step.get('description', '')
                    steps_data.append(desc)
                elif isinstance(step, str):
                    # Si c'est déjà une chaîne, l'utiliser directement
                    steps_data.append(step)
            except Exception as e:
                print(f"Erreur lors de la conversion d'une étape: {e}")
        
        # S'assurer qu'il y a au moins une étape (requis par le modèle)
        if not steps_data:
            steps_data = ["Aucune étape disponible"]
        
        # Créer les objets Ingredient
        ingredients = []
        for ing_data in ingredients_data:
            try:
                ingredients.append(Ingredient(**ing_data))
            except Exception as e:
                print(f"Erreur lors de la création d'un ingrédient: {e}")
        
        # Récupérer les URLs d'images
        main_image_url = entity.get("main_image_url")
        additional_images = safe_json_loads(entity.get("additional_images", "[]"), [])
        
        # Gérer la difficulté avec valeur par défaut
        difficulty_str = entity.get("difficulty", "Facile")
        try:
            difficulty = DifficultyLevel(difficulty_str.capitalize())
        except ValueError:
            print(f"Niveau de difficulté invalide: {difficulty_str}, utilisation de 'Facile'")
            difficulty = DifficultyLevel.FACILE
        
        # Gérer les types de repas
        meal_type_data = safe_json_loads(entity.get("meal_type", "[]"), [])
        meal_types = []
        for mt in meal_type_data:
            try:
                meal_types.append(MealType(mt.capitalize()))
            except ValueError:
                print(f"Type de repas invalide: {mt}")
        
        # S'assurer qu'il y a au moins un type de repas (requis par le modèle)
        if not meal_types:
            meal_types = [MealType.MAIN_COURSE]  # Valeur par défaut
        
        return Recipe(
            id=entity["RowKey"],
            title=entity["title"],
            description=entity.get("description"),
            difficulty=difficulty,
            meal_type=meal_types,
            servings=entity["servings"],
            prep_time_minutes=entity["prep_time_minutes"],
            cook_time_minutes=entity["cook_time_minutes"] if entity.get("cook_time_minutes", 0) > 0 else None,
            total_time_minutes=entity["total_time_minutes"],
            ingredients=ingredients,
            steps=steps_data,
            tags=tags_data,
            created_at=entity["created_at"],
            updated_at=entity["updated_at"],
            main_image_url=main_image_url,
            additional_images=additional_images
        )
    
    async def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        """Créer une nouvelle recette."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        recipe_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        
        # Extraire les données du modèle et supprimer les champs qui seront définis explicitement
        recipe_dict = recipe_data.model_dump()
        recipe_dict["total_time_minutes"] = self._calculate_total_time(
            recipe_data.prep_time_minutes,
            recipe_data.cook_time_minutes
        )
        
        # Supprimer les champs qui seront définis explicitement pour éviter les doublons
        for field in ["id", "created_at", "updated_at"]:
            if field in recipe_dict:
                recipe_dict.pop(field)
        
        recipe = Recipe(
            id=recipe_id,
            created_at=now,
            updated_at=now,
            **recipe_dict
        )
        
        entity = self._recipe_to_entity(recipe)
        
        try:
            self.table_client.create_entity(entity=entity)
            return recipe
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la création de la recette: {e}")
    
    async def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Récupérer une recette par son ID."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        try:
            entity = self.table_client.get_entity(partition_key="recipe", row_key=recipe_id)
            return self._entity_to_recipe(entity)
        except ResourceNotFoundError:
            return None
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la récupération de la recette: {e}")
    
    async def get_all_recipes(self, skip: int = 0, limit: int = 10) -> Tuple[List[Recipe], int]:
        """Récupérer toutes les recettes avec pagination."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        try:
            # Récupérer toutes les recettes
            entities = list(self.table_client.query_entities(query_filter="PartitionKey eq 'recipe'"))
            
            # Calculer le total
            total = len(entities)
            
            # Appliquer la pagination
            paginated_entities = entities[skip:skip + limit]
            
            # Convertir les entités en recettes
            recipes = []
            for entity in paginated_entities:
                try:
                    recipe = self._entity_to_recipe(entity)
                    recipes.append(recipe)
                except Exception as e:
                    # Log l'erreur mais continuer avec les autres recettes
                    print(f"Erreur lors de la conversion d'une recette: {e}")
            
            return recipes, total
        
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la récupération des recettes: {e}")
    
    async def update_recipe(self, recipe_id: str, recipe_update: RecipeUpdate) -> Optional[Recipe]:
        """Mettre à jour une recette existante."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        existing_recipe = await self.get_recipe(recipe_id)
        if not existing_recipe:
            return None
        
        update_data = recipe_update.model_dump(exclude_unset=True)
        
        # Mettre à jour les champs modifiés
        for field, value in update_data.items():
            setattr(existing_recipe, field, value)
        
        # Recalculer le temps total si nécessaire
        if 'prep_time_minutes' in update_data or 'cook_time_minutes' in update_data:
            existing_recipe.total_time_minutes = self._calculate_total_time(
                existing_recipe.prep_time_minutes,
                existing_recipe.cook_time_minutes
            )
        
        # Mettre à jour la date de modification
        existing_recipe.updated_at = datetime.now(UTC)
        
        entity = self._recipe_to_entity(existing_recipe)
        
        try:
            self.table_client.update_entity(entity=entity, mode="replace")
            return existing_recipe
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la mise à jour de la recette: {e}")
    
    async def delete_recipe(self, recipe_id: str) -> bool:
        """Supprimer une recette."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        try:
            self.table_client.delete_entity(partition_key="recipe", row_key=recipe_id)
            return True
        except ResourceNotFoundError:
            return False
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la suppression de la recette: {e}")
    
    async def list_recipes(
        self,
        skip: int = 0,
        limit: int = 10,
        filters: Optional[RecipeSearchFilters] = None
    ) -> List[Recipe]:
        """Lister les recettes avec pagination et filtres."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        # Construire le filtre OData
        filter_query = "PartitionKey eq 'recipe'"
        
        if filters:
            if filters.difficulty:
                filter_query += f" and difficulty eq '{filters.difficulty.value}'"
            if filters.meal_type:
                filter_query += f" and meal_type eq '{filters.meal_type.value}'"
            if filters.max_prep_time:
                filter_query += f" and prep_time_minutes le {filters.max_prep_time}"
            if filters.max_total_time:
                filter_query += f" and total_time_minutes le {filters.max_total_time}"
        
        entities = self.table_client.query_entities(
            query_filter=filter_query,
            results_per_page=limit
        )
        
        recipes = []
        count = 0
        for entity in entities:
            if count < skip:
                count += 1
                continue
            if len(recipes) >= limit:
                break
            
            recipe = self._entity_to_recipe(entity)
            
            # Filtres additionnels qui ne peuvent pas être faits avec OData
            if filters and filters.tags:
                if not any(tag in recipe.tags for tag in filters.tags):
                    continue
            
            recipes.append(recipe)
        
        return recipes
            
    async def search_recipes_by_ingredient(self, ingredient_name: str) -> List[Recipe]:
        """Rechercher des recettes par nom d'ingrédient."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        entities = self.table_client.query_entities(query_filter="PartitionKey eq 'recipe'")
        
        matching_recipes = []
        for entity in entities:
            recipe = self._entity_to_recipe(entity)
            
            # Vérifier si l'ingrédient est présent
            for ingredient in recipe.ingredients:
                if ingredient_name.lower() in ingredient.name.lower():
                    matching_recipes.append(recipe)
                    break
        
        return matching_recipes
            
    async def search_by_ingredient(self, ingredient_name: str) -> List[Recipe]:
        """Rechercher des recettes par nom d'ingrédient (alias pour search_recipes_by_ingredient)."""
        return await self.search_recipes_by_ingredient(ingredient_name)
            
    async def add_image_url(self, recipe_id: str, image_url: str, image_type: str = "main") -> Optional[Recipe]:
        """Ajouter une URL d'image à une recette."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        try:
            # Récupérer la recette existante
            entity = self.table_client.get_entity(partition_key="recipe", row_key=recipe_id)
            recipe = self._entity_to_recipe(entity)
            
            # Ajouter l'URL d'image
            if image_type == "main":
                recipe.main_image_url = image_url
            else:
                if not recipe.additional_images:
                    recipe.additional_images = []
                recipe.additional_images.append(image_url)
            
            # Mettre à jour l'entité
            updated_entity = self._recipe_to_entity(recipe)
            self.table_client.update_entity(updated_entity, mode="replace")
            
            return recipe
            
        except ResourceNotFoundError:
            return None
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'ajout de l'URL d'image: {e}")
    
    async def clear_image_urls(self, recipe_id: str) -> Optional[Recipe]:
        """Supprimer toutes les URLs d'images d'une recette."""
        if not self.table_client:
            raise RuntimeError("Azure n'est pas configuré")
        
        try:
            # Récupérer la recette existante
            entity = self.table_client.get_entity(partition_key="recipe", row_key=recipe_id)
            recipe = self._entity_to_recipe(entity)
            
            # Supprimer les URLs d'images
            recipe.main_image_url = None
            recipe.additional_images = []
            
            # Mettre à jour l'entité
            updated_entity = self._recipe_to_entity(recipe)
            self.table_client.update_entity(updated_entity, mode="replace")
            
            return recipe
            
        except ResourceNotFoundError:
            return None
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la suppression des URLs d'images: {e}")
    
    def _calculate_total_time(self, prep_time: int, cook_time: Optional[int]) -> int:
        """Calculer le temps total de préparation."""
        return prep_time + (cook_time or 0)


# Fonction factory pour l'injection de dépendances
def get_recipe_service() -> RecipeService:
    """Retourne une instance du service de recettes pour l'injection de dépendances."""
    return RecipeService()

# Pour la compatibilité avec le code existant
recipe_service = RecipeService()

