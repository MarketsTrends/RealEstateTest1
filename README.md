# RealEstate MVP (FastAPI + Financial Engine + Frontend)

Backend MVP pour l'analyse de deals immobiliers, déterministe et testable offline, avec frontend React minimal.

## Prérequis

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose (pour Postgres/PostGIS local)
- Dépendances système WeasyPrint (Cairo/Pango/Fontconfig) si non présentes sur votre OS

## Installation backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
# optional AI memo
# export OPENAI_API_KEY=...
# export OPENAI_MODEL=gpt-4.1-mini
```

## Installation frontend

```bash
cd frontend
cp .env.example .env
npm install
```

## Scope comps MVP (3B)

- **Zone couverte**: Paris (scope limité volontaire)
- **Source visée**: fichier local DVF / DVF-like CSV
- **Objectif**: rendre `/comps/sales` utile en local pour une zone restreinte, sans pipeline national.

## Structure

- `app/api/reports.py`: endpoint `POST /report/pdf`.
- `app/db/comps_repo.py`: requêtes PostGIS comps + stats.
- `app/services/comps_service.py`: fallback propre si DB indisponible.
- `db/init/001_sales_transactions.sql`: schéma + indexes table comps.
- `scripts/import_comps.py`: import CSV DVF-like filtré Paris.
- `frontend/`: application React + Vite TypeScript, section comps simple.

## Lancer la base Postgres/PostGIS

```bash
docker compose up -d
```

> Le dossier `db/init/` est monté automatiquement pour créer la table `sales_transactions` et ses index.

## Importer des comps (Paris)

## Comps identifier strategy

- `transaction_id` est conservé comme champ métier/source (peut apparaître sur plusieurs lignes DVF).
- La clé technique stockée est `record_id` (clé primaire).
- Priorité d'identification:
  1. `source` est file-aware (`dvf:<nom_fichier_source>`)
  2. `record_id = "<source>:<source_row_id>"` quand `source_row_id` existe
  3. sinon hash stable des champs (`source|transaction_id|date|lat|lon|price`)
- L'upsert de l'import est fait sur `record_id` pour préserver l'unicité au niveau ligne et par fichier source.

Préparez un CSV local DVF-like contenant au minimum des colonnes compatibles avec:
- transaction id (`transaction_id` ou `id_mutation`)
- date (`sold_at` ou `date_mutation`)
- prix (`price_eur` ou `valeur_fonciere`)
- latitude/longitude (`lat`/`lon` ou `latitude`/`longitude`)
- code postal (`postal_code` ou `code_postal`)

Puis lancez:

```bash
python scripts/import_comps.py --csv /path/to/dvf_like.csv --database-url "$DATABASE_URL" --truncate
```

Le script:
- normalise les champs,
- filtre Paris,
- upsert dans `sales_transactions`.

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

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## AI Investment Memo

- Endpoint: `POST /memo`
- Input: même payload que `/analysis`
- Output: JSON structuré:
  - `summary`
  - `investment_view` (`strong|balanced|cautious|weak`)
  - `key_strengths[]`
  - `key_risks[]`
  - `sensitivity_points[]`
  - `next_checks[]`
  - `disclaimer`

Règle produit: l'IA n'effectue **aucun calcul**.
Tous les nombres viennent strictement de la sortie déterministe backend.

Si `OPENAI_API_KEY` est absent: `/memo` renvoie `503` avec un message explicite.

## Export PDF

- Endpoint: `POST /report/pdf`
- Input: même payload que `/analysis`
- Output: `application/pdf`
- Nom suggéré: `deal-analysis-report.pdf`

## Frontend comps behavior

- Ajoutez manuellement `lat/lon` dans le formulaire.
- Après analyse, le frontend appelle `/comps/sales` et affiche:
  - disponibilité,
  - médiane €/m²,
  - nombre de comps,
  - intervalle quartiles (p25/p75),
  - tableau réduit de transactions comparables.

Si `lat/lon` absents ou DB indisponible, une section placeholder/warning est affichée.

## Hypothèses MVP

- Calculs pré-tax uniquement.
- Projections annuelles avec hypothèses plates (loyer, vacance, OPEX constants au sein d'un scénario).
- Pas d'inflation détaillée, pas de fiscalité, pas de capex récurrent modélisé.
- PDF: pas de comps ni visualisations avancées.
- Memo IA: synthèse explicative uniquement, pas de recalcul, pas de promesse de performance.
- Comps: pas de couverture nationale, uniquement Paris dans cette étape.

## Exécuter les tests

```bash
pytest
```

## Notes

- Tous les tests backend sont offline.
- Si `DATABASE_URL` n'est pas défini, `/comps/sales` renvoie `available=false` avec warnings explicites.
