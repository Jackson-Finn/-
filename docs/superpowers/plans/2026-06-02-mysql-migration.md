# MySQL Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the backend runtime, Docker environment, and automated tests from SQLite to a MySQL-first workflow managed by Alembic.

**Architecture:** Keep the existing SQLAlchemy ORM models as the application data contract, add Alembic as the only schema lifecycle tool, remove runtime schema mutation from app startup, and run integration tests against a dedicated MySQL test database with per-test transaction rollback.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, Alembic, PyMySQL, MySQL 8, pytest, Docker Compose

---

### Task 1: Flip Backend Defaults to MySQL

**Files:**
- Create: `backend/tests/test_settings_mysql.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Write the failing configuration test**

```python
# backend/tests/test_settings_mysql.py
from app.core.config import Settings


def test_default_database_url_is_mysql():
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("mysql+pymysql://")
```

- [ ] **Step 2: Run the test to verify it fails for the right reason**

Run:

```bash
cd backend && pytest -q tests/test_settings_mysql.py::test_default_database_url_is_mysql
```

Expected:
- FAIL because `settings.database_url` currently starts with `sqlite:///`

- [ ] **Step 3: Add the MySQL and Alembic dependencies**

```toml
# backend/pyproject.toml
[project]
dependencies = [
  "alembic>=1.14.0",
  "celery>=5.4.0",
  "email-validator>=2.2.0",
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "minio>=7.2.0",
  "opensearch-py>=2.6.0",
  "passlib[bcrypt]>=1.7.4",
  "pillow>=11.1.0",
  "pydantic-settings>=2.6.0",
  "pyjwt>=2.9.0",
  "pymysql>=1.1.1",
  "python-multipart>=0.0.9",
  "redis>=5.2.0",
  "sqlalchemy>=2.0.36",
  "uvicorn[standard]>=0.32.0",
]
```

- [ ] **Step 4: Change the default backend configuration to a MySQL DSN**

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    app_name: str = "Advanced Marketplace API"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api"
    secret_key: str = "advanced-marketplace-dev-secret-key-2026"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = (
        "mysql+pymysql://marketplace:marketplace@127.0.0.1:3306/"
        "advanced_marketplace?charset=utf8mb4"
    )
    redis_url: str = "redis://redis:6379/0"
```

```dotenv
# backend/.env.example
DATABASE_URL=mysql+pymysql://marketplace:marketplace@127.0.0.1:3306/advanced_marketplace?charset=utf8mb4
REDIS_URL=redis://127.0.0.1:6379/0
STORAGE_BACKEND=local
MINIO_ENDPOINT=127.0.0.1:9000
OPENSEARCH_URL=http://127.0.0.1:9200
```

- [ ] **Step 5: Re-run the configuration test**

Run:

```bash
cd backend && pytest -q tests/test_settings_mysql.py::test_default_database_url_is_mysql
```

Expected:
- PASS

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/app/core/config.py backend/.env.example backend/tests/test_settings_mysql.py
git commit -m "chore: switch backend defaults to MySQL"
```

### Task 2: Add a MySQL Test Harness and Dependency Override

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_mysql_harness.py`
- Modify: `backend/tests/test_api_smoke.py`

- [ ] **Step 1: Write a failing integration test that requires a shared MySQL client fixture**

```python
# backend/tests/test_mysql_harness.py
def test_mysql_client_health(mysql_client):
    response = mysql_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the test to verify the fixture is missing**

Run:

```bash
cd backend && pytest -q tests/test_mysql_harness.py::test_mysql_client_health
```

Expected:
- FAIL with `fixture 'mysql_client' not found`

- [ ] **Step 3: Implement the session-scoped MySQL test database reset and client override**

```python
# backend/tests/conftest.py
import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault(
    "TEST_DATABASE_ADMIN_URL",
    "mysql+pymysql://root:root@127.0.0.1:3306/mysql?charset=utf8mb4",
)
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "mysql+pymysql://marketplace:marketplace@127.0.0.1:3306/advanced_marketplace_test?charset=utf8mb4",
)


@pytest.fixture(scope="session")
def mysql_database_url() -> str:
    return os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
def mysql_admin_url() -> str:
    return os.environ["TEST_DATABASE_ADMIN_URL"]


@pytest.fixture(scope="session")
def mysql_engine(mysql_admin_url: str, mysql_database_url: str):
    admin_engine = create_engine(mysql_admin_url, isolation_level="AUTOCOMMIT", future=True)
    database_name = make_url(mysql_database_url).database
    assert database_name, "TEST_DATABASE_URL must include a database name"

    with admin_engine.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS `{database_name}`"))
        connection.execute(
            text(
                f"CREATE DATABASE `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )

    engine = create_engine(mysql_database_url, future=True)
    yield engine
    engine.dispose()
    admin_engine.dispose()


@pytest.fixture()
def mysql_client(mysql_engine) -> Generator[TestClient, None, None]:
    from app.core.database import Base, get_db
    from app.main import app

    Base.metadata.create_all(bind=mysql_engine)

    TestingSessionLocal = sessionmaker(
        bind=mysql_engine,
        autocommit=False,
        autoflush=False,
        future=True,
    )

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
```

- [ ] **Step 4: Re-run the harness test**

Run:

```bash
cd backend && pytest -q tests/test_mysql_harness.py::test_mysql_client_health
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_mysql_harness.py
git commit -m "test: add initial MySQL integration harness"
```

### Task 3: Introduce Alembic and Replace Test Schema Creation with Migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/20260602_01_mysql_baseline.py`
- Create: `backend/tests/test_alembic_schema.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Write the failing schema test**

```python
# backend/tests/test_alembic_schema.py
from sqlalchemy import inspect


def test_alembic_upgrade_creates_core_tables(mysql_engine):
    inspector = inspect(mysql_engine)
    table_names = set(inspector.get_table_names())
    assert {"alembic_version", "users", "products", "orders", "reports"}.issubset(table_names)
```

- [ ] **Step 2: Run the schema test to verify it fails**

Run:

```bash
cd backend && pytest -q tests/test_alembic_schema.py::test_alembic_upgrade_creates_core_tables
```

Expected:
- FAIL because the raw test database does not contain migrated tables yet

- [ ] **Step 3: Add Alembic configuration wired to the existing SQLAlchemy metadata**

```python
# backend/alembic/env.py
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.database import Base
from app.models import entities  # noqa: F401

config = context.config
settings = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

```ini
# backend/alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = mysql+pymysql://marketplace:marketplace@127.0.0.1:3306/advanced_marketplace?charset=utf8mb4

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

- [ ] **Step 4: Generate the baseline migration from the current model set and review it**

Run:

```bash
cd backend && alembic revision --autogenerate -m "create mysql baseline"
```

Expected:
- A new file appears under `backend/alembic/versions/`
- The `upgrade()` function contains `op.create_table(...)` calls for the current schema, including:
  - `users.presence_status`
  - `reviews.review_type`
  - `reviews.seller_id`
  - `notifications.action_target`
  - `admin_notification_broadcasts.action_target`

- [ ] **Step 5: Normalize the generated migration for MySQL**

```python
# backend/alembic/versions/20260602_01_mysql_baseline.py
def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("presence_status", sa.String(length=32), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        mysql_charset="utf8mb4",
    )
```

The full migration should keep the autogenerated table set, but review and correct:
- MySQL charset and collation declarations where needed
- index names
- JSON column definitions
- foreign keys and unique constraints

- [ ] **Step 6: Update the test harness to run migrations instead of `Base.metadata.create_all()`**

```python
# backend/tests/conftest.py
from alembic import command
from alembic.config import Config

@pytest.fixture(scope="session")
def mysql_engine(mysql_admin_url: str, mysql_database_url: str):
    admin_engine = create_engine(mysql_admin_url, isolation_level="AUTOCOMMIT", future=True)
    database_name = make_url(mysql_database_url).database
    with admin_engine.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS `{database_name}`"))
        connection.execute(
            text(
                f"CREATE DATABASE `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )

    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", mysql_database_url)
    command.upgrade(alembic_config, "head")

    engine = create_engine(mysql_database_url, future=True)
    yield engine
```

- [ ] **Step 7: Re-run the schema test**

Run:

```bash
cd backend && pytest -q tests/test_alembic_schema.py::test_alembic_upgrade_creates_core_tables
```

Expected:
- PASS

- [ ] **Step 8: Commit**

```bash
git add backend/alembic.ini backend/alembic backend/tests/conftest.py backend/tests/test_alembic_schema.py
git commit -m "feat: add Alembic-managed MySQL schema"
```

### Task 4: Remove Runtime Schema Mutation and SQLite Bootstrap Logic

**Files:**
- Create: `backend/tests/test_runtime_bootstrap.py`
- Modify: `backend/app/core/database.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/core/seed.py`

- [ ] **Step 1: Write the failing startup regression test**

```python
# backend/tests/test_runtime_bootstrap.py
from fastapi.testclient import TestClient


def test_app_startup_does_not_call_create_all(monkeypatch, mysql_client):
    from app.core.database import Base
    from app.main import app

    def fail_create_all(*args, **kwargs):
        raise AssertionError("create_all should not be called during startup")

    monkeypatch.setattr(Base.metadata, "create_all", fail_create_all)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
```

- [ ] **Step 2: Run the regression test to verify it fails**

Run:

```bash
cd backend && pytest -q tests/test_runtime_bootstrap.py::test_app_startup_does_not_call_create_all
```

Expected:
- FAIL because the current lifespan still calls `Base.metadata.create_all(...)`

- [ ] **Step 3: Simplify the database module to pure engine/session setup**

```python
# backend/app/core/database.py
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Remove runtime schema patching from app startup and make seeding explicitly empty-db aware**

```python
# backend/app/main.py
@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        get_storage_service().bootstrap()
    except Exception as exc:
        print(f"[storage] bootstrap skipped: {exc}")

    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()
    yield
```

```python
# backend/app/core/seed.py
def seed_defaults(db) -> None:
    if db.query(User).first():
        return

    permission_specs = [
        ("product.audit", "Audit products"),
        ("report.review", "Review reports"),
        ("appeal.review", "Review appeals"),
        ("recommendation.manage", "Manage recommendations"),
        ("search.manage", "Manage search"),
        ("notification.manage", "Manage notifications"),
    ]
    permission_map = {permission.code: permission for permission in db.query(Permission).all()}
    for code, name in permission_specs:
        if code not in permission_map:
            permission_map[code] = Permission(code=code, name=name)
            db.add(permission_map[code])
    db.flush()
    # Keep the remainder of the current demo-data inserts unchanged and end with db.commit().
    db.commit()
```

The seed refactor should preserve current demo content, but make the top-level existence guard explicit and idempotent.

- [ ] **Step 5: Re-run the regression test and the core smoke login test**

Run:

```bash
cd backend && pytest -q \
  tests/test_runtime_bootstrap.py::test_app_startup_does_not_call_create_all \
  tests/test_mysql_harness.py::test_mysql_client_health
```

Expected:
- PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/database.py backend/app/main.py backend/app/core/seed.py backend/tests/test_runtime_bootstrap.py
git commit -m "refactor: remove runtime schema mutation"
```

### Task 5: Upgrade the Test Suite to Transactional MySQL Isolation

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_api_smoke.py`
- Modify: `backend/tests/test_e2e_flow.py`

- [ ] **Step 1: Convert one smoke test to use the shared MySQL client fixture**

```python
# backend/tests/test_api_smoke.py
def test_health_endpoint(mysql_client):
    response = mysql_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the single smoke test to verify the current fixture leaks state across requests**

Run:

```bash
cd backend && pytest -q tests/test_api_smoke.py::test_seeded_admin_login_and_me
```

Expected:
- FAIL because a session-scoped mutable database setup will leak writes between tests once smoke and end-to-end cases share the same underlying state

- [ ] **Step 3: Rework the fixture to use per-test outer transactions with a bound session**

```python
# backend/tests/conftest.py
@pytest.fixture()
def db_session(mysql_engine):
    connection = mysql_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        future=True,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def mysql_client(db_session):
    from app.core.database import get_db
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
```

- [ ] **Step 4: Port the smoke and end-to-end tests off the temporary SQLite helper**

```python
# backend/tests/test_api_smoke.py
def test_seeded_admin_login_and_me(mysql_client):
    login = mysql_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    assert login.status_code == 200
```

```python
# backend/tests/test_e2e_flow.py
def test_marketplace_core_flow(mysql_client):
    admin_token = login(mysql_client, "admin@example.com", "Admin123!")
    seller_token = login(mysql_client, "seller@example.com", "Seller123!")
    buyer_token = login(mysql_client, "buyer@example.com", "Buyer123!")
```

Also remove:
- `import importlib`
- `import os`
- `import sys`
- the old `build_client(tmp_path)` helpers

- [ ] **Step 5: Run the backend test suite**

Run:

```bash
cd backend && pytest -q
```

Expected:
- PASS

- [ ] **Step 6: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_api_smoke.py backend/tests/test_e2e_flow.py
git commit -m "test: migrate backend suite to MySQL transactions"
```

### Task 6: Switch Docker, Makefile, and Docs to the MySQL Workflow

**Files:**
- Modify: `docker-compose.yml`
- Modify: `Makefile`
- Modify: `README.md`

- [ ] **Step 1: Write the compose and developer commands before editing**

```yaml
# docker-compose.yml
services:
  mysql:
    image: mysql:8.4
    environment:
      MYSQL_DATABASE: advanced_marketplace
      MYSQL_USER: marketplace
      MYSQL_PASSWORD: marketplace
      MYSQL_ROOT_PASSWORD: root
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -proot --silent"]
```

```makefile
# Makefile
migrate:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd backend && alembic upgrade head

test:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd backend && pytest -q
```

```md
# README.md
1. Start MySQL
2. Run `make migrate`
3. Run `make api`
4. Run `make frontend`
```

- [ ] **Step 2: Update Compose to run API and worker against MySQL and migrate on startup**

```yaml
# docker-compose.yml
services:
  api:
    command: >-
      sh -lc "if [ ! -x /opt/venv/bin/python ]; then python -m venv /opt/venv; fi
      && . /opt/venv/bin/activate
      && pip install --no-input -e .
      && alembic upgrade head
      && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"
    depends_on:
      mysql:
        condition: service_healthy
```

Set the compose `DATABASE_URL` values to:

```text
mysql+pymysql://marketplace:marketplace@mysql:3306/advanced_marketplace?charset=utf8mb4
```

- [ ] **Step 3: Update the Makefile and README to document the new startup sequence**

```makefile
# Makefile
api:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd backend && uvicorn app.main:app --reload

migrate:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd backend && alembic upgrade head

docker-up:
	$(COMPOSE) up --detach --wait --wait-timeout 300
```

```md
# README.md
## Local development

1. Copy environment files
2. Start MySQL locally or with Docker
3. Run `make migrate`
4. Run `make api`
5. Run `make frontend`

## Docker

- `docker compose up --detach --wait --wait-timeout 300`
- API startup runs `alembic upgrade head` automatically
- MySQL is the primary relational database in both development and test environments
```

While editing `README.md`, remove the existing conflict markers and the stale SQLite-first instructions completely.

- [ ] **Step 4: Verify Compose rendering and the backend tests**

Run:

```bash
docker compose config
cd backend && pytest -q
```

Expected:
- `docker compose config` exits successfully
- backend test suite stays green

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml Makefile README.md
git commit -m "docs: switch runtime workflow to MySQL"
```

### Task 7: Final Verification Sweep

**Files:**
- Modify: `backend/tests/test_api_smoke.py`
- Modify: `backend/tests/test_e2e_flow.py`
- Modify: `README.md`

- [ ] **Step 1: Run migrations on a clean MySQL database**

Run:

```bash
cd backend && alembic upgrade head
```

Expected:
- PASS
- `alembic_version` present

- [ ] **Step 2: Run the backend tests from a clean shell**

Run:

```bash
cd backend && pytest -q
```

Expected:
- PASS

- [ ] **Step 3: Bring up the composed stack**

Run:

```bash
docker compose up --detach --wait --wait-timeout 300
```

Expected:
- MySQL, API, worker, frontend, Redis, MinIO, OpenSearch, and Nginx all become healthy

- [ ] **Step 4: Smoke test the API and login flow**

Run:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"Admin123!"}'
```

Expected:
- health returns `{"status":"ok"}`
- login returns a token payload

- [ ] **Step 5: Commit any final cleanup**

```bash
git add -A
git commit -m "chore: finalize MySQL migration verification"
```
