# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EventLens AH is an AI-powered market event research system for A-share and Hong Kong stock markets. It ingests unstructured market news, extracts structured events via LLM, maps events to tradable assets, scores event alpha, and generates investment research hypotheses. This is a research tool, NOT a trading bot — it must never provide buy/sell recommendations.

**Monorepo:** `backend/` (FastAPI + SQLModel + Celery), `frontend/` (React + Vite + Ant Design + TanStack Query)

## Commands

```bash
# Backend (Python 3.11+, managed with uv)
cd backend && uv sync && uv pip install -e ".[dev]"
cd backend && uv run pytest                          # all tests
cd backend && uv run pytest tests/test_scoring.py    # single test file
cd backend && uv run ruff check .                    # lint
cd backend && uv run uvicorn app.main:app --reload   # dev server (defaults to SQLite)

# Frontend (Node 20+)
cd frontend && npm install && npm run dev            # Vite dev server on :5173
cd frontend && npm run build                         # TypeScript check + Vite build

# Docker (uses Podman)
podman-compose up --build                            # start all 5 services
podman-compose down                                  # stop all services
```

## Architecture

### Backend Layering

```
api/          FastAPI route handlers, thin — delegate to services
services/     Business logic orchestration (EventService, DocumentService, etc.)
llm/          LLM provider abstraction: BaseLLMProvider → MockLLMProvider (default), Qwen/DeepSeek stubs
scoring/      EventAlphaScorer: weighted linear model (see formula below)
models/       SQLModel ORM models (7 tables, all use `table=True` for async compat)
schemas/      Pydantic v2 request/response schemas, including LLM output validation
ingestion/    Document ingestion pipeline: fetch → dedup by SHA-256 content_hash → store
workers/      Celery async task queue (Redis broker)
db/           seed data (10 assets, 8 Chinese documents)
```

**Key constraint:** SQLModel `Field()` cannot mix `index=True` or `foreign_key=` with `sa_column=Column(...)`. Put `index=True` inside `Column()` directly. All response schemas need `model_config = {"from_attributes": True}` to validate from ORM objects.

### Scoring Formula (EventAlphaScorer)

```
alpha = 0.20*novelty + 0.20*materiality + 0.15*credibility + 0.15*urgency
      + 0.10*confidence + 0.10*tradability + 0.10*liquidity - 0.20*risk
```

All inputs [0.0, 1.0], output clamped to [0.0, 1.0]. Tradability/liquidity derived from market_scope (A_SHARE → 0.70/0.65), risk is a penalty (negative weight).

### LLM Provider Pattern

`get_llm_provider()` in `llm/factory.py` selects the provider based on `MOCK_LLM_ENABLED` and `LLM_PROVIDER` settings. The MockLLMProvider (~45KB) uses Chinese keyword matching against 9 event types and returns variant-rich structured outputs. Three LLM tasks: `extract_event`, `map_event_to_assets`, `generate_hypothesis`. All return Pydantic models defined in `schemas/llm_outputs.py`.

### Frontend Stack

- **Routing:** React Router v6, 4 routes: `/` (Dashboard), `/events` (list), `/events/:eventId` (detail with tabs), `/assets/:assetId`
- **Data fetching:** TanStack Query v5 hooks in `hooks/`, API calls in `api/`
- **UI:** Ant Design 5 with zhCN locale, dark blue theme (`colorPrimary: "#1a365d"`)
- **Vite proxy:** `/api` → backend container (`BACKEND_URL` env var). Proxy rewrites redirect `Location` headers to relative paths to prevent browser DNS errors.

### API Routes

| Prefix | File | Key endpoints |
|---|---|---|
| `/api/raw-documents/` | `api/documents.py` | CRUD, list with trailing slash |
| `/api/events/` | `api/events.py` | list, detail, extract, score, map-assets, generate-hypothesis, price-reactions |
| `/api/assets/` | `api/assets.py` | CRUD, filter by market/sector |
| `/api/ingestion/` | `api/ingestion.py` | manual ingest, run-demo |
| `/api/dashboard/` | `api/dashboard.py` | summary, top-events, recent-documents |

FastAPI routes ending in `/` require trailing slashes — the Vite proxy `configure` hook rewrites redirect `Location` headers to avoid exposing internal container hostnames to the browser.

### Database

SQLModel with async SQLAlchemy. Defaults to SQLite (`sqlite+aiosqlite:///./eventlens.db`) when `DATABASE_URL` not set — no PostgreSQL required for local dev. Content deduplication uses SHA-256 hash on document content.

### Closed-Loop Pipeline

The 7-step research pipeline runs: 信息入库 → 事件抽取 → 标的映射 → 假设生成 → 风险反证 → 打分排序 → 后续表现记录

- **Price reactions:** `EventPriceReaction` stores per-asset returns (1d/3d/5d/20d), max drawdown, volume change, benchmark/excess returns. Generate via `POST /api/events/{id}/price-reactions`.
- **hypothesis `impact_chain`:** Stored as `list[str]` in a JSON column — the mock LLM splits ` -> ` separated template strings. Schema must match: `impact_chain: list[str]` in both `HypothesisOutput` (LLM schema) and `ResearchHypothesisResponse`. Model field is `list | None`.

### Redis / Celery

Both optional. Redis cache is no-op when `REDIS_URL` is empty (lazy import to avoid import errors). Celery workers handle async tasks: `run_extraction_pipeline`, `run_demo_ingestion_task`.

## Docker Notes

Ports mapped to avoid conflicts with host services: PostgreSQL `5433:5432`, Redis `6380:6379`. Images come from a Podman mirror (`docker.m.daocloud.io`) configured in `~/.config/containers/registries.conf`. When building, images are cached locally — no Docker Hub pull needed once cached.