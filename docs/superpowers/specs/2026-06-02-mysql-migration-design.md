# MySQL Migration Design

## Summary

This project will migrate from a SQLite-first setup to a MySQL-first architecture. MySQL becomes the only supported primary relational database for development, Docker, and automated tests. Existing SQLite data will not be migrated; environments will be rebuilt from schema migrations and seed data.

## Goal

Replace the current ad hoc SQLite-oriented database lifecycle with an explicit MySQL workflow based on SQLAlchemy ORM models, Alembic migrations, deterministic seeding, and MySQL-backed automated tests.

## Scope

In scope:

- Change the default runtime database from SQLite to MySQL.
- Add Alembic and create an initial MySQL baseline migration.
- Remove SQLite bootstrap behavior and runtime schema patching from application startup.
- Update Docker to provide a MySQL service and wire API and worker services to it.
- Update tests to run against a MySQL test database with session-level schema setup and per-test transaction rollback.
- Update developer documentation and startup instructions.

Out of scope:

- Migrating existing SQLite data into MySQL.
- Supporting SQLite as a secondary runtime or test backend.
- Refactoring unrelated business logic outside of what is required for MySQL compatibility.

## Current State

The current backend uses SQLAlchemy ORM with a `DATABASE_URL` defaulting to SQLite. The application boot path still performs SQLite-specific work in `backend/app/core/database.py`, including local file bootstrap and `check_same_thread` handling. Application startup in `backend/app/main.py` runs `Base.metadata.create_all()` and a runtime `ensure_runtime_columns()` routine that issues `ALTER TABLE` statements to patch schema drift in-place.

Tests also depend on SQLite by constructing temporary database files per test module. Docker does not provide MySQL today; the project relies on a local SQLite file even in the composed environment.

## Design Decisions

### 1. MySQL becomes the single primary relational database

The project will treat MySQL as the authoritative relational backend for local development, Docker, and automated tests. This removes SQLite-vs-MySQL behavior drift and matches the user request for a complete migration.

### 2. Schema management moves to Alembic

Database schema creation and evolution will be handled exclusively by Alembic migrations. The application process will no longer create or mutate schema at runtime. This removes the current split-brain model where ORM metadata, startup SQL patches, and static SQL files all partially define the database.

### 3. ORM models remain the application data contract

Business code will continue to use the existing SQLAlchemy models in `backend/app/models/entities.py`. This limits application-layer churn while still allowing a disciplined schema lifecycle through migrations.

### 4. Fresh MySQL environments are seeded, not migrated from SQLite

Because existing SQLite data does not need to be preserved, new MySQL databases will be initialized by applying migrations and then seeding baseline records. This keeps the migration path simple and avoids one-off data transfer code.

### 5. Automated tests run on MySQL with transactional isolation

Test coverage must execute against the same database dialect used in development. Tests will use a dedicated MySQL test database, apply migrations once per test session, seed deterministic baseline data, and isolate each test case with a rollback boundary.

## Target Architecture

### Runtime flow

1. MySQL starts and accepts connections.
2. Alembic migrations run to `head`.
3. API and worker processes start.
4. Application startup verifies connectivity, boots storage, and seeds baseline data only when the business tables are empty.

### Source of truth

- ORM models define application-side structure and query behavior.
- Alembic migrations define database-side schema lifecycle.
- Seed code defines baseline users, roles, permissions, categories, and demo records.

Static SQL files under `backend/database/sql/` can remain as reference artifacts if needed, but they will no longer be treated as the authoritative initialization path.

## Implementation Design

### Configuration and dependencies

`backend/pyproject.toml` will add the MySQL DBAPI dependency required by SQLAlchemy, along with Alembic. The backend configuration defaults in `backend/app/core/config.py` and `backend/.env.example` will change from a SQLite file URL to a MySQL connection string.

Expected configuration additions or updates:

- `DATABASE_URL` defaulted to a MySQL DSN.
- Optional database settings kept minimal unless required by the driver.
- Documentation for the development database name and credentials used in Docker and local setups.

### Database layer

`backend/app/core/database.py` will be simplified to:

- load settings,
- build the SQLAlchemy engine,
- configure session creation,
- expose `Base` and `get_db()`.

The following behavior will be removed:

- SQLite file copy/bootstrap logic,
- SQLite-specific implicit database file preparation,
- any schema creation behavior outside migrations.

MySQL-specific engine options may be added if needed for connection health, such as pre-ping.

### Application startup

`backend/app/main.py` will stop calling:

- `Base.metadata.create_all(bind=engine)`,
- `ensure_runtime_columns()`.

Startup will instead:

- optionally verify that the database is reachable,
- bootstrap storage,
- open a session,
- call seed logic only when the database is effectively empty.

The empty-database check should use business tables such as `users` or `roles`, not filesystem assumptions.

### Alembic migration setup

New Alembic files will be added under `backend/`, including:

- `backend/alembic.ini`,
- `backend/alembic/env.py`,
- `backend/alembic/script.py.mako`,
- `backend/alembic/versions/<timestamp>_mysql_baseline.py`.

The initial migration will represent the current desired schema directly rather than replaying historical SQLite drift. This baseline must include the columns that runtime patching currently tries to add, so the runtime patching path can be deleted safely.

### ORM and schema compatibility review

The migration work must verify that existing ORM column definitions behave correctly on MySQL, especially:

- `JSON` fields,
- `DateTime(timezone=True)` behavior,
- boolean fields,
- string lengths and indexed columns,
- foreign key constraints and unique constraints.

If model adjustments are necessary for MySQL compatibility, they should be made in the ORM models and reflected in the baseline migration rather than patched in startup code.

### Seed behavior

`backend/app/core/seed.py` remains the seed entry point, but it will now operate in a migration-first world. Seed execution must stay idempotent: safe to call on every startup, while only creating baseline records when required.

The seed strategy is:

- schema exists before the app boots,
- startup invokes seed,
- seed checks for baseline presence,
- missing baseline records are created,
- otherwise no duplicate demo data is inserted.

## Docker Design

`docker-compose.yml` will add a `mysql` service and make API and worker depend on it. The compose environment will no longer point `DATABASE_URL` at a SQLite path.

The MySQL service should define:

- database name,
- application user and password,
- root password,
- persistent volume,
- health check.

API and worker startup must wait on MySQL health and use a MySQL `DATABASE_URL`. If the API container currently installs the backend package and then directly launches `uvicorn`, the compose command should also run `alembic upgrade head` before the server starts, or the project should document an explicit migration command that must be run first. The preferred design is to run migrations automatically in the container startup path so a fresh environment becomes operable with one compose command.

## Test Design

Tests will move from temporary SQLite files to a dedicated MySQL test database such as `advanced_marketplace_test`.

### Test database lifecycle

- Create or reset the test database once per test session.
- Run `alembic upgrade head` once per session.
- Seed baseline records once per session.
- For each test function, open a transaction boundary and roll it back at the end of the test.

### Test isolation mechanism

The recommended implementation is:

- create a single engine for the test database,
- create a dedicated connection per test,
- begin an outer transaction,
- bind a session to that connection,
- let the application use that test-bound session,
- roll back the outer transaction after the test completes.

This approach keeps the test suite MySQL-native while avoiding full schema rebuild cost on every case.

### Application injection for tests

Tests should override the FastAPI database dependency so each `TestClient` instance uses the transactional test session instead of the normal runtime session factory.

### Why SQLite is removed from tests

SQLite-based tests would continue to hide MySQL-specific behavior around JSON handling, constraints, defaults, and SQL dialect differences. A complete migration requires production-parity database testing.

## File Impact

Expected modifications:

- `backend/pyproject.toml`
- `backend/.env.example`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/main.py`
- `backend/app/core/seed.py` if seed idempotency needs tightening
- `backend/tests/...` shared fixtures and integration tests
- `docker-compose.yml`
- `Makefile`
- `README.md`

Expected additions:

- `backend/alembic.ini`
- `backend/alembic/`
- migration version files
- test fixture helpers for MySQL setup and dependency override

Expected removals or deprecations:

- SQLite bootstrap logic,
- runtime schema patching,
- SQLite-first startup instructions.

## Risks

### ORM-to-MySQL type mismatch

`JSON`, timezone-aware timestamps, and booleans may not behave identically to SQLite. The migration must verify that generated DDL and runtime serialization match application expectations.

### Duplicate or partial seed data

If empty-database detection is too naive, startup could either skip required seed data or create duplicates. Seed idempotency must be verified explicitly.

### Test transaction leakage

If test sessions are not properly bound to rollback-controlled connections, state may leak between tests. Fixture design and dependency overrides need careful verification.

### Startup ordering in Docker

If migrations do not run before API startup, the app may boot against a missing or incomplete schema. Compose startup sequencing must enforce migration completion.

### Existing documentation drift

The current `README.md` contains merge-conflict markers and outdated SQLite-first guidance. Documentation updates must correct both the database migration and the pre-existing doc inconsistency.

## Verification Strategy

The migration is considered successful when all of the following are true:

1. A fresh MySQL database can be brought to the latest schema with `alembic upgrade head`.
2. The API boots without calling `create_all()` or runtime schema patching.
3. Seeded demo accounts can log in successfully against MySQL.
4. Docker can bring up MySQL, API, worker, frontend, and supporting services in a clean environment.
5. Backend integration tests pass against the MySQL test database with transactional rollback isolation.
6. Developer documentation accurately describes the new MySQL-first workflow.

## Rollout Notes

This migration intentionally prefers a clean break over dual-backend compatibility. The repository may retain historical SQLite files for reference during the transition, but they are no longer part of the supported runtime architecture after the change lands.
