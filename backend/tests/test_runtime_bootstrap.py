import importlib
import sys

from fastapi.testclient import TestClient


def test_app_startup_does_not_call_create_all(monkeypatch, mysql_engine, mysql_database_url):
    monkeypatch.setenv("DATABASE_URL", mysql_database_url)
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)

    database_module = importlib.import_module("app.core.database")

    def fail_create_all(*args, **kwargs):
        raise AssertionError("create_all should not be called during startup")

    monkeypatch.setattr(database_module.Base.metadata, "create_all", fail_create_all)
    main_module = importlib.import_module("app.main")

    with TestClient(main_module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
