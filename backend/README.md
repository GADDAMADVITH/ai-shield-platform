# AI Shield Backend

Production foundation for the AI Shield API — FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2.

## Stack

- Python 3.12+
- FastAPI
- PostgreSQL (async via SQLAlchemy + asyncpg)
- Alembic
- Pydantic v2 / pydantic-settings

## Project layout

```text
backend/
├── app/
│   ├── api/v1/          # Versioned HTTP routes
│   ├── core/            # Config, logging, exceptions
│   ├── db/              # Engine + session skeleton
│   ├── models/          # ORM models (future)
│   ├── schemas/         # Pydantic schemas
│   ├── repositories/    # Data access (future)
│   ├── services/        # Business logic (future)
│   ├── middleware/      # CORS and other middleware
│   ├── auth/            # Auth (future)
│   ├── connectors/      # External connectors (future)
│   ├── assessment/      # Assessment engine (future)
│   ├── reports/         # Reports (future)
│   ├── utils/
│   └── main.py          # App factory + entrypoint
├── alembic/             # Migrations
├── tests/
├── .env.example
├── alembic.ini
├── pyproject.toml
└── README.md
```

## Setup

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Ensure PostgreSQL is running and `DATABASE_URL` in `.env` is correct before using the DB or Alembic. The health endpoint does not require a live database connection.

## Run

```sh
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: [http://localhost:8000/health](http://localhost:8000/health)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Tests

```sh
cd backend
source .venv/bin/activate
pytest
```

## What this foundation includes

- FastAPI app factory with lifespan hooks
- `GET /health` → `{"status":"healthy"}`
- Settings via environment / `.env` (pydantic-settings)
- Async SQLAlchemy session dependency (`get_db`) — no models yet
- Structured logging (JSON or console)
- CORS middleware
- Global exception handlers
- API versioning under `/api/v1`

## Not implemented yet

Authentication, users, projects, reports, scanning, assessment engine, and database models.
