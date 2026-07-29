# Grounded Transcription Agent

## Scope

Phase 1 builds the local asynchronous-job foundation. Do not add a frontend, MCP server,
authentication, or transcription-provider integration until their phase is started.

## Backend rules

- Python 3.14, FastAPI, Celery, PostgreSQL, Redis, and MinIO are the local stack.
- Keep dependencies directed: Presentation -> Application -> Domain; Infrastructure implements
  Domain ports. Only the composition root may import both Application and Infrastructure.
- PostgreSQL is the source of truth for job status and results. Redis is only the Celery broker.
- Run `poetry run black .`, `poetry run isort .`, `poetry run flake8 .`,
  `poetry run mypy .`, and `poetry run pytest` before committing.

## Local commands

```bash
cp .env.example .env.local
docker compose up --build --wait
docker compose logs -f api worker
cd backend && poetry run pytest
```
