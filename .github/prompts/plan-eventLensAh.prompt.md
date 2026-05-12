## Plan: EventLens AH MVP Monorepo Bootstrap

Build a runnable, dockerized MVP monorepo that ingests market documents, structures events via a validated LLM pipeline (mock-first), links assets, generates hypotheses, scores events deterministically, tracks price reactions, and serves a React dashboard. Use SQLAlchemy 2.0 + Alembic on FastAPI backend, ECharts frontend, and add a basic auth scaffold while keeping strict research-only positioning (no trading advice).

**Steps**
1. Phase 1 - Repository and runtime foundation
2. Create monorepo directories and baseline files under backend/frontend/root, including lint/test/type configs, environment templates, and startup scripts. This phase blocks all subsequent phases.
3. Add root-level docker-compose with services for backend, frontend, postgres, redis, celery worker, and optional celery beat; include healthchecks, dependency ordering, volumes for dev, and explicit commands. Depends on step 2.
4. Add backend and frontend Dockerfiles (dev-friendly, production-capable) and backend entrypoint that waits for DB then runs Alembic migrations. Depends on step 3.
5. Phase 2 - Backend core architecture and auth scaffold
6. Implement backend app bootstrap: settings, logging, dependency wiring, FastAPI app factory, API router registration, exception handlers, and health endpoint. Depends on step 2.
7. Implement basic auth scaffold: user model/migration, password hashing utility, token issuance endpoint, auth dependency for protected routes, and default local dev admin seed path. Depends on step 6 and step 11.
8. Define SQLAlchemy 2.0 models and enums for RawDocument, MarketEvent, Asset, EventAssetLink, ResearchHypothesis, EventPriceReaction, LLMRunLog, and User/Auth tables; include indexes for timestamps, market filters, content_hash, and foreign keys. Depends on step 6.
9. Create Pydantic v2 request/response schemas and strict LLM output schemas for extraction, asset mapping, and hypothesis generation; include enum-safe validation and score range constraints. Depends on step 8.
10. Configure DB session layer and Alembic environment, generate initial migration(s), and ensure startup applies schema consistently. Depends on step 8.
11. Phase 3 - Ingestion, deduplication, LLM pipeline, scoring, and async jobs
12. Implement ingestion services for manual and demo ingestion, raw document timestamp preservation, content hashing, duplicate grouping logic, and source metadata retention. Depends on step 9 and step 10.
13. Implement LLM provider abstraction with BaseLLMProvider, QwenProvider, DeepSeekProvider, and MockLLMProvider; route provider selection via config, validate every output against Pydantic schemas, and log failures to LLMRunLog without crashing flow. Depends on step 9.
14. Implement event extraction workflow service to transform RawDocument into MarketEvent with evidence chain fields and uncertainty handling; set low confidence when mapping is ambiguous. Depends on step 12 and step 13.
15. Implement asset mapping workflow that uses known asset universe and conservative confidence defaults to avoid hallucinated mappings; persist EventAssetLink records. Depends on step 14.
16. Implement hypothesis generation workflow producing impact chain, supporting/counter evidence, triggers, invalidation conditions, and risk notes. Depends on step 15.
17. Implement deterministic scorer service with required formula and explicit defaults for tradability/liquidity when unavailable, then persist event_alpha_score updates. Depends on step 14 and can run in parallel with step 16 once MarketEvent exists.
18. Configure Celery with Redis broker/result backend and task wrappers for extract/map/hypothesis/score jobs; ensure idempotent task behavior and retry policy for provider/network errors. Depends on step 12 through step 17.
19. Phase 4 - API surface and dashboard aggregation
20. Implement required routers/endpoints: raw documents, events (extract/generate-hypothesis/score and related list endpoints), assets CRUD/list/detail, ingestion manual/demo, dashboard summary/top-events/recent-documents. Depends on steps 7 through 18.
21. Add filtering/sorting/pagination for event and document listing endpoints, including market_scope, direction, event_type, score range, and date range. Depends on step 20.
22. Implement price reaction tracking endpoints and pluggable adapter interface (manual first, adapter hook for future market data providers). Depends on step 20.
23. Phase 5 - Frontend dashboard implementation (React + Vite + TS + AntD + TanStack Query + React Router + ECharts)
24. Bootstrap frontend app shell, route tree, query client, Ant Design layout/theme, auth gate scaffold, and typed API client with token handling. Depends on step 2, step 3, and backend auth/API contracts from step 20.
25. Build Dashboard page with total docs/events, high-score event cards, recent events table, event type distribution chart (ECharts), and latest ingestion status widgets. Depends on step 20.
26. Build Event List page with required columns and URL-synced filters (market_scope, direction, event_type, score range, date range), server-side pagination, and drill-down navigation. Depends on step 21.
27. Build Event Detail page sections for summary, original document evidence/timestamps/source, scores, linked assets, impact chain, hypothesis, evidence/counter-evidence, trigger/invalidation conditions, and price reaction panel. Depends on step 20 and step 22.
28. Build Asset page with basic info, related events list, and event history visual summary. Depends on step 20.
29. Phase 6 - Seed data, tests, and documentation
30. Add seed script that creates clearly marked demo data: 10 assets (A/HK), 8 raw documents, extracted events, links, hypotheses, and sample price reactions using MockLLMProvider pipeline outputs. Depends on steps 12 through 18.
31. Add backend tests for scoring formula correctness, schema validation constraints, mock extraction flow, and critical endpoint smoke tests. Depends on step 20 and step 30.
32. Add frontend tests for key route rendering and core table/chart components with mock API responses; include lint/typecheck scripts. Depends on steps 25 through 28.
33. Write comprehensive README and .env.example: project boundaries, architecture diagram text, setup/run/test commands, ingestion-source extension guide, LLM-provider extension guide, and compliance disclaimer (research tool only, not financial advice). Depends on all prior steps.
34. Run final verification matrix (compose up, migration, seed, API smoke, frontend navigation, worker task execution, tests) and document known MVP limitations. Depends on step 33.

**Relevant files**
- /data/eventlens-ah/docker-compose.yml — compose orchestration for backend/frontend/postgres/redis/worker/beat and health wiring.
- /data/eventlens-ah/.env.example — shared environment contract for local stack.
- /data/eventlens-ah/README.md — architecture, setup, extension paths, compliance text.
- /data/eventlens-ah/backend/pyproject.toml — dependencies, ruff/pytest config, scripts.
- /data/eventlens-ah/backend/Dockerfile — backend container build/runtime.
- /data/eventlens-ah/backend/alembic.ini — migration config entry.
- /data/eventlens-ah/backend/alembic/env.py — migration environment with SQLAlchemy metadata binding.
- /data/eventlens-ah/backend/alembic/versions/* — initial schema migration(s).
- /data/eventlens-ah/backend/app/main.py — FastAPI app bootstrap.
- /data/eventlens-ah/backend/app/core/config.py — Pydantic settings and provider/auth options.
- /data/eventlens-ah/backend/app/core/security.py — password hashing and JWT utilities.
- /data/eventlens-ah/backend/app/core/celery_app.py — Celery app config.
- /data/eventlens-ah/backend/app/db/session.py — SQLAlchemy engine/session factory.
- /data/eventlens-ah/backend/app/models/*.py — ORM models and enums for domain + auth.
- /data/eventlens-ah/backend/app/schemas/*.py — API DTOs and strict LLM output schemas.
- /data/eventlens-ah/backend/app/api/*.py — route modules for required endpoints.
- /data/eventlens-ah/backend/app/services/ingestion.py — dedup/content-hash ingest logic.
- /data/eventlens-ah/backend/app/services/event_pipeline.py — extraction/map/hypothesis orchestration.
- /data/eventlens-ah/backend/app/services/scoring.py — deterministic alpha score calculator.
- /data/eventlens-ah/backend/app/llm/base.py — BaseLLMProvider interface.
- /data/eventlens-ah/backend/app/llm/qwen.py — Qwen provider implementation scaffold.
- /data/eventlens-ah/backend/app/llm/deepseek.py — DeepSeek provider implementation scaffold.
- /data/eventlens-ah/backend/app/llm/mock.py — local deterministic mock outputs for full offline run.
- /data/eventlens-ah/backend/app/workers/tasks.py — Celery task entrypoints.
- /data/eventlens-ah/backend/app/tests/* — scoring/schema/pipeline/API tests.
- /data/eventlens-ah/backend/app/scripts/seed_demo.py — demo data loader.
- /data/eventlens-ah/frontend/package.json — frontend dependencies/scripts.
- /data/eventlens-ah/frontend/Dockerfile — frontend container build/runtime.
- /data/eventlens-ah/frontend/src/main.tsx — app bootstrap and providers.
- /data/eventlens-ah/frontend/src/routes/index.tsx — router definitions and auth guards.
- /data/eventlens-ah/frontend/src/api/client.ts — typed HTTP client and auth headers.
- /data/eventlens-ah/frontend/src/api/*.ts — domain API wrappers.
- /data/eventlens-ah/frontend/src/hooks/*.ts — TanStack Query hooks.
- /data/eventlens-ah/frontend/src/types/*.ts — domain and response typing.
- /data/eventlens-ah/frontend/src/pages/DashboardPage.tsx — KPI and chart dashboard.
- /data/eventlens-ah/frontend/src/pages/EventListPage.tsx — filterable event table.
- /data/eventlens-ah/frontend/src/pages/EventDetailPage.tsx — evidence and hypothesis detail view.
- /data/eventlens-ah/frontend/src/pages/AssetPage.tsx — asset profile and related events.
- /data/eventlens-ah/frontend/src/components/* — reusable cards/tables/score tags/evidence widgets.

**Verification**
1. Run docker stack and verify all services healthy: postgres/redis/backend/frontend/celery worker (and beat if enabled).
2. Confirm Alembic migration auto-applies on backend startup and tables/indexes exist.
3. Execute seed script and verify counts (10 assets, 8 raw documents, generated events/hypotheses/links/reactions).
4. Call ingestion demo endpoint and verify deduplication behavior by re-submitting same content (same content_hash grouped as duplicate).
5. Trigger extract/hypothesis/score endpoints on an event and verify strict schema validation and persisted LLMRunLog entries for successes/failures.
6. Verify dashboard endpoints return summary/top/recent payloads consumed by frontend widgets.
7. Validate event list filters (market_scope, direction, event_type, score/date ranges) affect results as expected.
8. Validate frontend routes render correctly behind auth scaffold (login -> dashboard -> detail pages).
9. Run backend tests (pytest) covering scoring formula, schema validation, mock extraction flow; run frontend tests/lint/typecheck.
10. Confirm all user-facing copy avoids buy/sell recommendations and includes research-only framing.

**Decisions**
- ORM: SQLAlchemy 2.0 chosen (explicit model/schema separation).
- Chart library: ECharts chosen for dashboard/event visuals.
- Auth: Include a basic local auth scaffold in MVP.
- Vector support: pgvector-ready schema design only; vector features optional and disabled by default.
- Market data: manual price reaction entry first; adapter interface included for future plug-ins.
- Scope boundaries: includes ingestion, structuring, scoring, dashboard, seed data, and tests; excludes live trading execution, portfolio management, and direct investment advice.

**Further Considerations**
1. Auth mechanism recommendation: use JWT bearer tokens for simplicity now, with future path to OIDC if needed.
2. Celery beat is optional in MVP; include service but keep disabled by default unless scheduled ingestion is desired.
3. Keep provider implementations for Qwen/DeepSeek scaffolded with graceful missing-key behavior so MockLLM remains default runnable path.