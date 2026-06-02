import importlib
import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault(
    "TEST_DATABASE_ADMIN_URL",
    "mysql+pymysql://root:root@127.0.0.1:3307/mysql?charset=utf8mb4",
)
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "mysql+pymysql://marketplace:marketplace@127.0.0.1:3307/advanced_marketplace_test?charset=utf8mb4",
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
        connection.execute(
            text(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO 'marketplace'@'127.0.0.1'")
        )
        connection.execute(
            text(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO 'marketplace'@'localhost'")
        )

    engine = create_engine(mysql_database_url, future=True)
    yield engine
    engine.dispose()
    admin_engine.dispose()


@pytest.fixture()
def mysql_client(mysql_engine, mysql_database_url: str) -> Generator[TestClient, None, None]:
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = mysql_database_url

    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)

    database_module = importlib.import_module("app.core.database")
    main_module = importlib.import_module("app.main")
    Base = database_module.Base
    get_db = database_module.get_db
    main_module.ensure_runtime_columns = lambda: None
    app = main_module.app

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
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
