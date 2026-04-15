import importlib
import os
import sys
from base64 import b64decode
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
        tiny_png = b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO6Wn2QAAAAASUVORK5CYII=")

        init_asset = client.post(
            "/api/media/upload-init",
            headers=auth_header(seller_token),
            json={"filename": "macbook.jpg", "mime_type": "image/jpeg"},
        )
        assert init_asset.status_code == 200
        asset_id = init_asset.json()["data"]["id"]

        upload_asset = client.post(
            f"/api/media/{asset_id}/file",
            headers=auth_header(seller_token),
            files={"file": ("macbook.png", tiny_png, "image/png")},
        )
        assert upload_asset.status_code == 200
        assert upload_asset.json()["data"]["metadata"]["stage"] == "uploaded"

        complete_asset = client.post(
            "/api/media/complete",
            headers=auth_header(seller_token),
            json={"asset_id": asset_id, "width": 1200, "height": 900},
        )
        assert complete_asset.status_code == 200
        assert complete_asset.json()["data"]["metadata"]["stage"] == "completed"
        assert complete_asset.json()["data"]["metadata"]["variants"]["preview"].endswith("-preview.webp")
        assert complete_asset.json()["data"]["metadata"]["variants"]["compressed"].endswith("-compressed.webp")

        create_product = client.post(
            "/api/products",
            headers=auth_header(seller_token),
            json={
                "title": "MacBook Air M2 95新",
                "description": "箱说齐全，电池循环少，适合学生党。",
                "price": 5299,
                "stock": 1,
                "category_id": 1,
                "asset_ids": [asset_id],
            },
        )
        assert create_product.status_code == 200
        product_id = create_product.json()["data"]["id"]
        assert create_product.json()["data"]["audit_status"] == "PENDING"
        assert len(create_product.json()["data"]["images"]) == 1

        pending = client.get("/api/admin/products/pending", headers=auth_header(admin_token))
        assert pending.status_code == 200
        assert any(item["id"] == product_id for item in pending.json()["data"])

        product_list = client.get("/api/admin/products", headers=auth_header(admin_token), params={"keyword": "MacBook"})
        assert product_list.status_code == 200
        assert any(item["id"] == product_id for item in product_list.json()["data"])

        product_context_before = client.get(
            f"/api/admin/products/{product_id}",
            headers=auth_header(admin_token),
        )
        assert product_context_before.status_code == 200
        assert product_context_before.json()["data"]["product"]["audit_status"] == "PENDING"

        request_changes = client.post(
            f"/api/admin/products/{product_id}/audit",
            headers=auth_header(admin_token),
            json={"decision": "REQUEST_CHANGES", "note": "请补充更多细节图"},
        )
        assert request_changes.status_code == 200
        assert request_changes.json()["data"]["audit_status"] == "CHANGES_REQUESTED"
        assert request_changes.json()["data"]["product_status"] == "NEEDS_REVISION"

        resubmit_product = client.post(
            f"/api/products/{product_id}/resubmit",
            headers=auth_header(seller_token),
        )
        assert resubmit_product.status_code == 200
        assert resubmit_product.json()["data"]["audit_status"] == "PENDING"

        audit = client.post(
            f"/api/admin/products/{product_id}/audit",
            headers=auth_header(admin_token),
            json={"decision": "APPROVE", "note": "信息完整，允许上架"},
        )
        assert audit.status_code == 200
        assert audit.json()["data"]["audit_status"] == "APPROVED"
        assert audit.json()["data"]["product_status"] == "ACTIVE"

        product_context_after = client.get(
            f"/api/admin/products/{product_id}",
            headers=auth_header(admin_token),
        )
        assert product_context_after.status_code == 200
        after_payload = product_context_after.json()["data"]
        assert after_payload["product"]["audit_status"] == "APPROVED"
        assert any(item["action"] == "product.audit" for item in after_payload["operations"])

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

        session_again = client.post(
            "/api/chat/sessions",
            headers=auth_header(buyer_token),
            json={"product_id": product_id, "seller_id": 2},
        )
        assert session_again.status_code == 200
        assert session_again.json()["data"]["id"] == session_id

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

        orders_after_review = client.get("/api/orders", headers=auth_header(buyer_token))
        assert orders_after_review.status_code == 200
        reviewed_order = next(item for item in orders_after_review.json()["data"] if item["id"] == order_id)
        assert reviewed_order["can_review_product"] is True
        assert reviewed_order["product_review"]["rating"] == 5
        assert reviewed_order["product_review"]["content"] == "机器很新，沟通高效"

        update_review = client.post(
            "/api/reviews",
            headers=auth_header(buyer_token),
            json={"order_id": order_id, "product_review": {"rating": 3, "content": "到手后发现成色一般，已修改评价"}},
        )
        assert update_review.status_code == 200
        assert update_review.json()["data"][0]["rating"] == 3
        assert update_review.json()["data"][0]["content"] == "到手后发现成色一般，已修改评价"

        product_reviews = client.get(f"/api/reviews/products/{product_id}")
        assert product_reviews.status_code == 200
        assert product_reviews.json()["data"][0]["rating"] == 3
        assert product_reviews.json()["data"][0]["content"] == "到手后发现成色一般，已修改评价"

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

        first_history = client.post(
            f"/api/history/products/{product_id}/view",
            headers=auth_header(buyer_token),
        )
        second_history = client.post(
            f"/api/history/products/{product_id}/view",
            headers=auth_header(buyer_token),
        )
        assert first_history.status_code == 200
        assert second_history.status_code == 200
        assert first_history.json()["data"]["id"] == second_history.json()["data"]["id"]

        history_listing = client.get("/api/history/recent", headers=auth_header(buyer_token))
        assert history_listing.status_code == 200
        matching_entries = [item for item in history_listing.json()["data"] if item["product_id"] == product_id]
        assert len(matching_entries) == 1

        off_shelf = client.post(
            f"/api/admin/products/{product_id}/off-shelf",
            headers=auth_header(admin_token),
            json={"note": "演示下架"},
        )
        assert off_shelf.status_code == 200
        assert off_shelf.json()["data"]["product_status"] == "OFF_SHELF"
