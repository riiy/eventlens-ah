# Repository Guidelines

## Project Structure & Module Organization

- `backend/app/`: application code. Routes are in `api/`, logic in `services/`, SQLModel tables in `models/`, schemas in `schemas/`, LLM providers in `llm/`, scoring in `scoring/`, ingestion in `ingestion/`, and Celery tasks in `workers/`.
- `backend/alembic/`: database migrations.
- `backend/tests/`: pytest suite for API, schemas, scoring, pipeline, and LLM.
- `frontend/src/`: React code. API calls are in `api/`, TanStack Query hooks in `hooks/`, pages in `pages/`, and TypeScript models in `types/`.
- `docker-compose.yml`: PostgreSQL, Redis, backend, Celery worker, and frontend stack.

## Build, Test, and Development Commands

- `rtk podman-compose up --build`: start the full local stack.
- `rtk podman-compose down`: stop local services.
- From `backend/`, `rtk uv sync` then `rtk uv pip install -e ".[dev]"`: install dependencies.
- From `backend/`, `rtk uv run uvicorn app.main:app --reload`: run the API.
- From `backend/`, `rtk uv run pytest`: run tests.
- From `backend/`, `rtk uv run ruff check .`: lint Python.
- From `frontend/`, `rtk npm install`: install dependencies.
- From `frontend/`, `rtk npm run dev`: run Vite on port 5173.
- From `frontend/`, `rtk npm run build`: type-check and build.

## Coding Style & Naming Conventions

Prefix commands with `rtk`. Backend code targets Python 3.11 with Ruff line length 100. Use `snake_case` for modules, functions, and fields; `PascalCase` for SQLModel, Pydantic, and service classes. Keep FastAPI handlers thin and delegate orchestration to `services/`.

Frontend uses TypeScript, React function components, and Ant Design. Use `PascalCase` for components and pages, `camelCase` for hooks and functions, and `useX` naming for hooks.

## Testing Guidelines

Backend tests use `pytest` and `pytest-asyncio`; async tests should use `@pytest.mark.asyncio`. Name test files `test_*.py` and keep fixtures in `backend/tests/conftest.py`. Add focused tests for scoring, schemas, APIs, ingestion logic, and LLM provider contracts. There is no frontend test runner configured; validate frontend changes with `rtk npm run build`.

## Commit & Pull Request Guidelines

History uses short imperative subjects, often with prefixes such as `feat:`, `chore:`, and `Refactor`. Prefer concise subjects, for example `feat: Add OpenAI-compatible provider`.

Pull requests should include a summary, test results, linked issues, and screenshots for UI changes. Note migrations, environment variable changes, or behavior affecting the research-tool boundary.

## Security & Domain Constraints

This project is a research tool, not a trading bot. Do not add buy/sell recommendations, trading signals, investment advice, or price forecasts. Keep API keys in `.env` and do not commit secrets.
