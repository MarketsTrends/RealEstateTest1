# RealEstate MVP (FastAPI + Financial Engine + Frontend)

Backend MVP pour l'analyse de deals immobiliers, déterministe et testable offline, avec frontend React minimal.

## Prérequis

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose (pour Postgres/PostGIS local)

## Installation backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
```

## Installation frontend

```bash
cd frontend
cp .env.example .env
npm install
```

## Structure

- `app/main.py`: création FastAPI minimale + registration des routers.
- `app/api/analysis.py`: endpoint `POST /analysis`.
- `app/api/comps.py`: endpoint `GET /comps/sales`.
- `app/services/analysis_service.py`: orchestration de la réponse d'analyse.
- `app/services/comps_service.py`: orchestration comps + fallback DB.
- `app/engine/*`: logique financière pure (prêt, cashflows, métriques, scénarios, risques).
- `frontend/`: application React + Vite TypeScript, page unique Deal Analysis.

## Lancer la base Postgres/PostGIS

```bash
docker compose up -d
```

## Lancer backend + frontend

Terminal 1 (backend):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (frontend):

```bash
cd frontend
npm run dev
```

Frontend sur `http://localhost:5173`, API sur `http://localhost:8000`.

## API base URL frontend

Configurer via:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Validation financière

`POST /analysis` applique une validation stricte:

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

- Tous les tests backend sont offline.
- Si `DATABASE_URL` n'est pas défini, `/comps/sales` renvoie `available=false` avec warnings explicites.
