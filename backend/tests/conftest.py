import importlib
import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
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


def _clear_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)


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
        connection.execute(
            text(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO 'marketplace'@'127.0.0.1'")
        )
        connection.execute(
            text(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO 'marketplace'@'localhost'")
        )

    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = mysql_database_url
    alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(alembic_config, "head")
    if previous_database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = previous_database_url

    engine = create_engine(mysql_database_url, future=True)
    yield engine
    engine.dispose()
    admin_engine.dispose()


@pytest.fixture()
def mysql_test_context(mysql_engine, mysql_database_url: str):
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = mysql_database_url

    _clear_app_modules()

    database_module = importlib.import_module("app.core.database")
    main_module = importlib.import_module("app.main")
    jobs_module = importlib.import_module("app.tasks.jobs")

    connection = mysql_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        future=True,
        join_transaction_mode="create_savepoint",
    )

    database_module.SessionLocal = TestingSessionLocal
    main_module.SessionLocal = TestingSessionLocal
    jobs_module.SessionLocal = TestingSessionLocal

    try:
        yield {
            "database_module": database_module,
            "main_module": main_module,
            "session_factory": TestingSessionLocal,
        }
    finally:
        transaction.rollback()
        connection.close()
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url


@pytest.fixture()
def db_session(mysql_test_context) -> Generator[Session, None, None]:
    session = mysql_test_context["session_factory"]()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def mysql_client(mysql_test_context, db_session: Session) -> Generator[TestClient, None, None]:
    database_module = mysql_test_context["database_module"]
    main_module = mysql_test_context["main_module"]
    get_db = database_module.get_db
    app = main_module.app

    def override_get_db() -> Generator[Session, None, None]:
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
