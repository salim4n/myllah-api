# Myllah API

API FastAPI avec architecture clean et moderne.

## 🏗️ Structure du projet

```
myllah/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py        # Routeur principal
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       └── health.py    # Endpoints de santé
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Configuration
│   └── schemas/
│       └── __init__.py      # Modèles Pydantic
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Tests de base
├── pyproject.toml           # Gestion dépendances avec uv
├── Dockerfile
└── README.md
```

## 🚀 Installation et démarrage

### Prérequis
- Python 3.12+
- `uv` pour la gestion des dépendances

### Installation
```bash
# Installer les dépendances
uv sync

# Activer l'environnement virtuel
source .venv/bin/activate
```

### Démarrage en développement
```bash
# Démarrer le serveur de développement
fastapi dev app/main.py

# Ou avec uvicorn directement
uvicorn app.main:app --reload
```

### Démarrage avec Docker
```bash
# Construire l'image
docker build -t myllah-api .

# Lancer le conteneur
docker run -p 8000:80 myllah-api
```

## 📚 API Documentation

Une fois l'application lancée, accédez à :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **OpenAPI JSON** : http://localhost:8000/api/v1/openapi.json

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Lancer les tests avec couverture
pytest --cov=app
```

## 🔧 Configuration

La configuration se trouve dans `app/core/config.py`. Vous pouvez créer un fichier `.env` pour les variables d'environnement :

```env
PROJECT_NAME=Myllah API
VERSION=0.1.0
API_V1_STR=/api/v1
```

## 📋 Endpoints disponibles

### Health Check
- `GET /api/v1/health/` - Vérification de santé
- `GET /api/v1/health/ready` - Vérification de disponibilité

## 🏛️ Architecture

Cette API suit les principes de l'architecture clean :

- **`app/main.py`** : Point d'entrée et configuration FastAPI
- **`app/api/`** : Couche API avec routeurs et endpoints
- **`app/core/`** : Configuration et utilitaires centraux
- **`app/schemas/`** : Modèles Pydantic pour validation
- **`tests/`** : Tests unitaires et d'intégration

## 🛠️ Développement

### Ajouter un nouvel endpoint

1. Créer un nouveau fichier dans `app/api/endpoints/`
2. Définir les modèles Pydantic dans `app/schemas/`
3. Ajouter le routeur dans `app/api/router.py`
4. Écrire les tests correspondants

### Standards de code

- Type hints obligatoires
- Modèles Pydantic pour validation
- Tests avec `pytest`
- Linting avec les outils standards Python