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

## Structure (refactor)

- `app/main.py`: création FastAPI minimale + registration des routers.
- `app/api/analysis.py`: endpoint `POST /analysis`.
- `app/api/comps.py`: endpoint `GET /comps/sales`.
- `app/services/analysis_service.py`: orchestration de la réponse d'analyse.
- `app/services/comps_service.py`: orchestration comps + fallback DB.
- `app/engine/*`: logique financière pure (prêt, cashflows, métriques, scénarios, risques).

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

## Validation financière

`POST /analysis` applique désormais une validation stricte:

- `loan_amount_eur + down_payment_eur == purchase_price_eur` (tolérance 0.01)
- sinon: erreur de validation HTTP 422 avec message explicite.

## DPE (optionnel)

`property.dpe_class` est optionnel et accepte `A|B|C|D|E|F|G`.

Flags risques DPE:

- `G` -> `DPE_G_REGULATORY_RISK` (high)
- `F` -> `DPE_F_REGULATORY_RISK` (medium)

## Scénarios

- `base`
- `optimistic`
- `prudent`

Les scénarios appliquent des deltas lisibles sur loyer, vacance, taux, appréciation,
**et désormais dépenses d'exploitation** (+ stress de sale cost).

## Hypothèses MVP

- Calculs pré-tax uniquement.
- Projections annuelles avec hypothèses plates (loyer, vacance, OPEX constants au sein d'un scénario).
- Pas d'inflation détaillée, pas de fiscalité, pas de capex récurrent modélisé.

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
