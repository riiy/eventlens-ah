# EventLens AH

AI-powered event research system for A-share and Hong Kong stock markets.

## System Boundaries

EventLens AH is a **research tool**, NOT an auto-trading bot. It does NOT provide:
- Buy/sell recommendations
- Trading signals
- Investment advice
- Price predictions or forecasts

It DOES provide:
- Structured extraction of market events from unstructured information
- Asset-to-event mapping with evidence chains
- Research hypotheses with supporting and counter evidence
- Risk analysis and invalidation conditions
- Event scoring based on multi-dimensional factors
- Post-event price reaction tracking

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Dashboard │ Event List │ Event Detail │ Asset Detail    │
│  Ant Design │ Recharts │ TanStack Query │ React Router  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────┐
│                  Backend (FastAPI)                       │
│  API Routes │ Services │ Ingestion │ Scoring │ LLM      │
│  Pydantic v2 │ SQLModel │ Celery Workers                │
└──────┬───────────────┬──────────────┬───────────────────┘
       │               │              │
┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
│  PostgreSQL │ │    Redis    │ │   Celery   │
│  (pgvector) │ │   (Cache)   │ │  (Tasks)   │
└─────────────┘ └─────────────┘ └────────────┘
```

### Data Flow

```
External Sources → Ingestion Pipeline → RawDocument
                                        ↓ (dedup by content_hash)
                                  LLM Extraction
                                        ↓
                                   MarketEvent
                                   ↓         ↘
                            Asset Mapping    Scoring
                            ↓                 ↓
                       EventAssetLink    MarketEvent (scored)
                            ↓
                      LLM Hypothesis
                            ↓
                    ResearchHypothesis
                            ↓
                    Price Reaction Tracking
```

## Tech Stack

| Layer    | Technology |
|----------|-----------|
| Backend  | Python 3.11+, FastAPI, SQLModel, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 (pgvector-ready) |
| Cache    | Redis 7 |
| Tasks    | Celery with Redis broker |
| LLM      | Mock (default), Qwen, DeepSeek (pluggable) |
| Frontend | React 18, TypeScript, Vite, Ant Design 5 |
| Charts   | Recharts |
| Infra    | Docker, docker-compose |

## Quick Start

### Prerequisites

- Docker and docker-compose
- Python 3.11+ (for local development without Docker)
- Node.js 20+ (for frontend development)

### Run with Docker

```bash
# Clone repository
git clone <repo-url>
cd eventlens-ah

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Backend API** on http://localhost:8000
- **Celery Worker** (background tasks)
- **Frontend** on http://localhost:5173

On first startup, the database is automatically migrated and seeded with demo data.

### Access the Application

- **Frontend Dashboard**: http://localhost:5173
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Run Demo Data

Click the "Run Demo Ingestion" button on the dashboard, or use the API:

```bash
curl -X POST http://localhost:8000/api/ingestion/run-demo
```

This ingests 8 sample market documents across A-share and HK markets, extracts events, maps assets, generates hypotheses, and computes scores.

## Local Development

### Backend

```bash
cd backend
pip install -e ".[dev]"

# Start PostgreSQL and Redis (via Docker)
docker compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

## Environment Variables

See `.env.example` for all available variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Async PostgreSQL connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `MOCK_LLM_ENABLED` | Use mock LLM (no API key needed) | `true` |
| `LLM_PROVIDER` | LLM provider: mock/qwen/deepseek | `mock` |
| `QWEN_API_KEY` | Qwen API key | (optional) |
| `DEEPSEEK_API_KEY` | DeepSeek API key | (optional) |
| `SEED_ON_STARTUP` | Auto-seed database on startup | `false` |

## API Endpoints

### Raw Documents
- `POST /api/raw-documents` - Ingest a document
- `GET /api/raw-documents` - List documents (paginated, filterable)
- `GET /api/raw-documents/{id}` - Get single document

### Events
- `GET /api/events` - List events (paginated, filterable, sortable)
- `GET /api/events/{id}` - Get single event with full details
- `POST /api/events/extract` - Extract events from document IDs
- `POST /api/events/{id}/generate-hypothesis` - Generate research hypothesis
- `POST /api/events/{id}/score` - Re-score an event
- `GET /api/events/{id}/assets` - Get linked assets
- `GET /api/events/{id}/hypotheses` - Get hypotheses
- `GET /api/events/{id}/price-reactions` - Get price reactions

### Assets
- `GET /api/assets` - List assets
- `POST /api/assets` - Create asset
- `GET /api/assets/{id}` - Get single asset

### Ingestion
- `POST /api/ingestion/manual` - Manually ingest a document
- `POST /api/ingestion/run-demo` - Run full demo ingestion pipeline

### Dashboard
- `GET /api/dashboard/summary` - Dashboard statistics
- `GET /api/dashboard/top-events` - Top events by alpha score
- `GET /api/dashboard/recent-documents` - Recent documents

## Scoring Formula

```
event_alpha_score =
    0.20 × novelty_score +
    0.20 × materiality_score +
    0.15 × credibility_score +
    0.15 × urgency_score +
    0.10 × confidence_score +
    0.10 × tradability_score +
    0.10 × liquidity_score -
    0.20 × risk_score
```

The score is clamped to [0.0, 1.0].

## Adding a New Ingestion Source

1. Create a new class in `backend/app/ingestion/sources.py` extending `BaseIngestionSource`
2. Implement the `fetch()` method returning a list of document dicts
3. Register the source in the ingestion pipeline

Example:
```python
class RSSIngestionSource(BaseIngestionSource):
    async def fetch(self) -> list[dict]:
        # Fetch from RSS feed, return list of document dicts
        ...
```

## Adding a New LLM Provider

1. Create a new class in `backend/app/llm/` extending `BaseLLMProvider`
2. Implement `extract_event()`, `map_event_to_assets()`, `generate_hypothesis()`
3. Add the provider to `backend/app/llm/factory.py`
4. Set `LLM_PROVIDER=your_provider` in `.env`

All LLM outputs must conform to the Pydantic schemas in `backend/app/schemas/llm_outputs.py`.

## Project Structure

```
eventlens-ah/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── core/                # Config, database, Redis
│   │   ├── db/                  # Session, seed data
│   │   ├── models/              # SQLModel ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── api/                 # API route handlers
│   │   ├── services/            # Business logic services
│   │   ├── llm/                 # LLM provider abstraction
│   │   ├── scoring/             # Event scoring
│   │   ├── ingestion/           # Document ingestion pipeline
│   │   └── workers/             # Celery async tasks
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Test suite
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client + endpoint functions
│   │   ├── components/          # Shared UI components
│   │   ├── hooks/               # TanStack Query hooks
│   │   ├── pages/               # Page-level components
│   │   ├── types/               # TypeScript type definitions
│   │   └── App.tsx              # Root component
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Compliance Disclaimer

**EventLens AH is a research tool only.** It does not provide financial advice, investment recommendations, or trading signals. All extracted events, hypotheses, scores, and asset mappings are generated by automated systems (including LLMs) and may contain errors, omissions, or biases. Users should independently verify all information before making any investment decisions. Past performance and historical patterns do not guarantee future results.

The demo data included in this project is entirely fictional and for demonstration purposes only. Any resemblance to real market events is coincidental.