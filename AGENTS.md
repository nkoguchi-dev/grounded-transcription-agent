# Grounded Transcription Agent

## Scope

Phase 1 builds the local asynchronous-job foundation. Do not add a frontend, MCP server,
authentication, or transcription-provider integration until their phase is started.

## Backend rules

- Python 3.14, FastAPI, Celery, PostgreSQL, Redis, and MinIO are the local stack.
- Keep dependencies directed: Presentation -> Application -> Domain; Infrastructure implements
  Application and Domain ports. Only the composition root may import both Application and
  Infrastructure.
- PostgreSQL is the source of truth for job status and results. Redis is only the Celery broker.
- Application use cases define transaction boundaries and depend only on abstractions such as a
  Unit of Work; they must not import SQLAlchemy types, Sessions, or concrete repositories.
- Infrastructure provides SQLAlchemy Unit of Work and Repository implementations, including
  commit/rollback and Session lifecycle management.
- Presentation must not reference the database, SQLAlchemy, concrete repositories, or database
  connection settings; it calls Application use cases. Only the composition root assembles
  Application and Infrastructure.
- Do not execute external-service calls or long-running work inside a database transaction. Persist
  asynchronous state transitions in short, independent transactions.
- Run `poetry run black .`, `poetry run isort .`, `poetry run flake8 .`,
  `poetry run mypy .`, and `poetry run pytest` before committing.

## Local commands

```bash
cp .env.example .env.local
docker compose up --build --wait
docker compose logs -f api worker
cd backend && poetry run pytest
```
