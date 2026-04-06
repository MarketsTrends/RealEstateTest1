# RealEstate MVP (FastAPI + Financial Engine)

Backend MVP pour l'analyse de deals immobiliers, déterministe et testable offline.

## Prérequis

- Python 3.12+
- Docker + Docker Compose (pour Postgres/PostGIS local)

## Installation locale

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
```

## Lancer la base Postgres/PostGIS

```bash
docker compose up -d
```

## Lancer l'API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /health`
- `GET /version`
- `POST /analysis`
- `GET /comps/sales`

## Exécuter les tests

```bash
pytest
```

## Lint/type checks

```bash
ruff check .
mypy app
```

## Notes

- Tous les tests sont offline.
- Si `DATABASE_URL` n'est pas défini, `/comps/sales` renvoie `available=false` avec warnings explicites.
