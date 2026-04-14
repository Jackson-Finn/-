import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def build_client(tmp_path: Path) -> TestClient:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'e2e.db'}"
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    module = importlib.import_module("app.main")
    return TestClient(module.app)


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_marketplace_core_flow(tmp_path: Path):
    with build_client(tmp_path) as client:
        admin_token = login(client, "admin@example.com", "Admin123!")
        seller_token = login(client, "seller@example.com", "Seller123!")
        buyer_token = login(client, "buyer@example.com", "Buyer123!")

        create_product = client.post(
            "/api/products",
            headers=auth_header(seller_token),
            json={
                "title": "MacBook Air M2 95新",
                "description": "箱说齐全，电池循环少，适合学生党。",
                "price": 5299,
                "stock": 1,
                "category_id": 1,
            },
        )
        assert create_product.status_code == 200
        product_id = create_product.json()["data"]["id"]
        assert create_product.json()["data"]["audit_status"] == "PENDING"

        pending = client.get("/api/admin/products/pending", headers=auth_header(admin_token))
        assert pending.status_code == 200
        assert any(item["id"] == product_id for item in pending.json()["data"])

        audit = client.post(
            f"/api/admin/products/{product_id}/audit",
            headers=auth_header(admin_token),
            json={"approved": True, "note": "信息完整，允许上架"},
        )
        assert audit.status_code == 200
        assert audit.json()["data"]["audit_status"] == "APPROVED"
        assert audit.json()["data"]["product_status"] == "ACTIVE"

        order = client.post(
            "/api/orders",
            headers=auth_header(buyer_token),
            json={"product_id": product_id, "quantity": 1, "request_id": "req-order-001"},
        )
        assert order.status_code == 200
        order_id = order.json()["data"]["id"]
        assert order.json()["data"]["status"] == "CREATED"

        session = client.post(
            "/api/chat/sessions",
            headers=auth_header(buyer_token),
            json={"product_id": product_id, "seller_id": 2},
        )
        assert session.status_code == 200
        session_id = session.json()["data"]["id"]

        message = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            headers=auth_header(buyer_token),
            json={"content": "这台电脑还能小刀吗？", "request_id": "msg-001"},
        )
        assert message.status_code == 200
        assert message.json()["data"]["content"] == "这台电脑还能小刀吗？"

        complete = client.post(f"/api/orders/{order_id}/confirm", headers=auth_header(buyer_token))
        assert complete.status_code == 200
        assert complete.json()["data"]["status"] == "COMPLETED"

        review = client.post(
            "/api/reviews",
            headers=auth_header(buyer_token),
            json={"order_id": order_id, "rating": 5, "content": "机器很新，沟通高效"},
        )
        assert review.status_code == 200

        report = client.post(
            "/api/reports",
            headers=auth_header(buyer_token),
            json={"target_type": "PRODUCT", "target_id": product_id, "reason": "想测试举报与申诉闭环"},
        )
        assert report.status_code == 200
        report_id = report.json()["data"]["id"]

        process_report = client.post(
            f"/api/admin/reports/{report_id}/process",
            headers=auth_header(admin_token),
            json={"approved": True, "note": "已记录并提醒卖家"},
        )
        assert process_report.status_code == 200
        assert process_report.json()["data"]["status"] == "PROCESSED"

        report_context = client.get(
            f"/api/admin/reports/{report_id}/context",
            headers=auth_header(admin_token),
        )
        assert report_context.status_code == 200
        report_context_data = report_context.json()["data"]
        assert report_context_data["report"]["id"] == report_id
        assert any(task["entity_id"] == report_id for task in report_context_data["tasks"])
        assert any(item["details"].get("note") == "已记录并提醒卖家" for item in report_context_data["operations"])

        appeal = client.post(
            "/api/appeals",
            headers=auth_header(seller_token),
            json={"report_id": report_id, "reason": "已补充更多检测图，申请复核"},
        )
        assert appeal.status_code == 200
        appeal_id = appeal.json()["data"]["id"]

        review_appeal = client.post(
            f"/api/admin/appeals/{appeal_id}/review",
            headers=auth_header(admin_token),
            json={"approved": True, "note": "补充材料充分，申诉通过"},
        )
        assert review_appeal.status_code == 200
        assert review_appeal.json()["data"]["status"] == "APPROVED"

        appeal_context = client.get(
            f"/api/admin/appeals/{appeal_id}/context",
            headers=auth_header(admin_token),
        )
        assert appeal_context.status_code == 200
        appeal_context_data = appeal_context.json()["data"]
        assert appeal_context_data["appeal"]["id"] == appeal_id
        assert appeal_context_data["report"]["id"] == report_id
        assert any(task["entity_id"] == appeal_id for task in appeal_context_data["tasks"])
        assert any(item["details"].get("note") == "补充材料充分，申诉通过" for item in appeal_context_data["operations"])

        recommendations = client.get("/api/recommendations/products/1/related")
        assert recommendations.status_code == 200
        assert "items" in recommendations.json()["data"]
