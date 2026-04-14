import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def build_client(tmp_path: Path) -> TestClient:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    module = importlib.import_module("app.main")
    return TestClient(module.app)


def test_health_endpoint(tmp_path: Path):
    with build_client(tmp_path) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_seeded_admin_login_and_me(tmp_path: Path):
    with build_client(tmp_path) as client:
        login = client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "Admin123!"},
        )
        assert login.status_code == 200
        token = login.json()["data"]["access_token"]

        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["data"]["email"] == "admin@example.com"
        assert "product.audit" in me.json()["data"]["permissions"]


def test_seeded_product_listing_and_search(tmp_path: Path):
    with build_client(tmp_path) as client:
        products = client.get("/api/products")
        assert products.status_code == 200
        assert len(products.json()["data"]) >= 3

        search = client.get("/api/search/products", params={"keyword": "Switch"})
        assert search.status_code == 200
        assert any("Switch" in item["title"] for item in search.json()["data"])


def test_anonymous_home_recommendations(tmp_path: Path):
    with build_client(tmp_path) as client:
        response = client.get("/api/recommendations/home")
        assert response.status_code == 200
        assert "items" in response.json()["data"]
