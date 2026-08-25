# TerraSense NER — Backend (FastAPI)

Initial backend for the **AI-Based Landslide Early Warning & Risk Monitoring
System**. Read-only, mock-backed endpoints that match the frontend API contract
in [`../API_ENDPOINTS.md`](../API_ENDPOINTS.md).

## Project structure

```
Server/
├── app/
│   ├── main.py                # app factory, CORS, error handling (no business logic)
│   ├── core/
│   │   ├── config.py          # pydantic-settings, env, CORS origins
│   │   └── logging.py         # logging setup
│   ├── models/                # Pydantic request/response schemas (the contract)
│   │   ├── common.py          # Coordinate, HealthResponse, ErrorResponse
│   │   ├── enums.py           # RiskStatus, DeltaDir
│   │   ├── region.py · kpi.py · risk_zone.py
│   ├── services/              # business logic + (mock) data source
│   │   ├── mock_data.py       # the only place that knows data is mocked
│   │   ├── risk.py            # band_for_score(): status derived from riskScore
│   │   └── *_service.py
│   └── api/
│       ├── router.py          # aggregates all route modules
│       └── routes/            # health, region, kpis, risk_zones
├── requirements.txt
├── .env.example
└── README.md
```

The data layer (`services/mock_data.py`) can later be replaced with
PostgreSQL/ML output without changing any schema or route.

## Setup & run (Windows PowerShell)

```powershell
cd Server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # optional; sensible defaults are built in
uvicorn app.main:app --reload --port 8000
```

macOS / Linux:

```bash
cd Server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

- API base: `http://localhost:8000/api`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Connect the frontend

Point the Vite app at this server — create `Client/.env`:

```
VITE_API_BASE_URL=http://localhost:8000/api
```

CORS already allows `http://localhost:5173`. Add more origins via
`BACKEND_CORS_ORIGINS` in `.env` (comma-separated).

## Implemented endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Backend health check |
| GET | `/api/region/meta` | Region banner + default map view |
| GET | `/api/kpis/summary` | Risk Overview KPI cards |
| GET | `/api/risk-zones` | Risk zones (`?state=` optional) |

`status` (`LOW`/`MODERATE`/`HIGH`/`CRITICAL`) is derived from `riskScore` in
`app/services/risk.py` using thresholds 0–20 / 20–40 / 40–70 / 70–100.

Not yet implemented (by design): auth, database, ML prediction, weather, and
other external services.

## Quick test

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/region/meta
curl http://localhost:8000/api/kpis/summary
curl http://localhost:8000/api/risk-zones
curl "http://localhost:8000/api/risk-zones?state=Mizoram"
```

---

## Database (Phase 1 — Neon PostgreSQL + PostGIS)

Persistence layer built with **SQLAlchemy 2.0 + GeoAlchemy2 + Alembic** on
**Neon PostgreSQL** with the **PostGIS** extension. Coordinates and GIS entities
use PostGIS `geometry` (SRID 4326 / WGS84).

### Layout

```
app/db/
├── base.py       # DeclarativeBase, naming convention, TimestampMixin
├── session.py    # lazy engine, session factory, get_db() FastAPI dependency
├── models.py     # 14 ORM models (geometry, FKs, indexes, relationships)
├── init_db.py    # dev bootstrap: CREATE EXTENSION postgis + create_all
└── seed.py       # realistic NER demo data (idempotent, --reset supported)
migrations/       # Alembic (env.py, versions/0001_initial_schema.py)
alembic.ini
```

### Tables

`users`, `districts`, `risk_zones`, `weather_data`, `terrain_data`,
`soil_moisture`, `landslide_history`, `ai_predictions`, `alerts`, `incidents`,
`roads`, `infrastructure`, `emergency_priorities`, `notifications`.

Risk `status` (`LOW | MODERATE | HIGH | CRITICAL`) is derived from `risk_score`
via `app/services/risk.py` — never hardcoded.

### Configure

Set the Neon connection string in `.env` (psycopg2 driver, SSL required):

```
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>.neon.tech/<db>?sslmode=require
```

### Migrate & seed

```powershell
# Apply migrations (creates PostGIS extension, all tables, indexes, FKs)
python -m alembic upgrade head

# Load demo data (idempotent; use --reset to wipe & reseed)
python -m app.db.seed
python -m app.db.seed --reset
```

Common Alembic commands:

```powershell
python -m alembic current                              # show applied revision
python -m alembic history                              # list migrations
python -m alembic revision --autogenerate -m "message" # create next migration
python -m alembic downgrade -1                          # roll back one revision
```

> Quick dev alternative (no versioning): `python -m app.db.init_db` enables
> PostGIS and creates all tables directly from the models. Alembic is the
> source of truth for production.

> Note: on Windows PowerShell, Alembic/seed log to **stderr**, so PowerShell may
> report a non-zero exit code even on success. Verify with `alembic current`
> or a DB query.
