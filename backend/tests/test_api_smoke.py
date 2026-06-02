from sqlalchemy import text


def test_health_endpoint(mysql_client):
    response = mysql_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_seeded_admin_login_and_me(mysql_client):
    login = mysql_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    me = mysql_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "admin@example.com"
    assert "product.audit" in me.json()["data"]["permissions"]


def test_seeded_product_listing_and_search(mysql_client):
    products = mysql_client.get("/api/products")
    assert products.status_code == 200
    assert len(products.json()["data"]) >= 3

    search = mysql_client.get("/api/search/products", params={"keyword": "Switch"})
    assert search.status_code == 200
    payload = search.json()["data"]
    assert payload["total"] >= 1
    assert any("Switch" in item["title"] for item in payload["items"])


def test_anonymous_home_recommendations(mysql_client):
    response = mysql_client.get("/api/recommendations/home")
    assert response.status_code == 200
    assert "items" in response.json()["data"]


def test_admin_recommendation_workbench(mysql_client):
    login = mysql_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    response = mysql_client.get(
        "/api/admin/recommendations/workbench",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["summary"]["materials"] >= 1
    assert len(payload["materials"]) >= 1
    assert "materialTypes" in payload["charts"]


def test_admin_search_reindex_route(mysql_client):
    login = mysql_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    response = mysql_client.post(
        "/api/admin/search/reindex",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] in {"completed", "queued"}
    assert payload["mode"] in {"database-fallback", "opensearch", "celery", "sync-fallback"}
    assert payload["job_id"] >= 1


def test_admin_recommendation_rebuild_route(mysql_client):
    login = mysql_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    response = mysql_client.post(
        "/api/admin/recommendations/rebuild",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] in {"completed", "queued"}
    assert payload["job_id"] >= 1


def test_admin_platform_ops_route(mysql_client):
    login = mysql_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    response = mysql_client.get(
        "/api/admin/platform/ops",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["summary"]["events"] >= 0
    assert "eventTypes" in payload["charts"]
    assert "mode" in payload["search"]
    assert len(payload["readiness"]) >= 4
    assert any(check["name"] == "database" and check["status"] == "READY" for check in payload["readiness"])
    assert "local" in payload["runbook"]
    assert payload["runtime"]["app_env"] in {"development", "container"}


def test_admin_product_list_and_detail_context(mysql_client):
    login = mysql_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    listing = mysql_client.get("/api/admin/products", headers=headers, params={"audit_status": "PENDING"})
    assert listing.status_code == 200
    products = listing.json()["data"]
    assert any(item["audit_status"] == "PENDING" for item in products)
    product_id = products[0]["id"]
    assert "seller_name" in products[0]
    assert "category_name" in products[0]

    detail = mysql_client.get(f"/api/admin/products/{product_id}", headers=headers)
    assert detail.status_code == 200
    payload = detail.json()["data"]
    assert payload["product"]["id"] == product_id
    assert "tasks" in payload
    assert "operations" in payload
    assert any(item["action"] == "product.view" for item in payload["operations"])


def test_request_changes_and_resubmit_flow(mysql_client):
    admin_login = mysql_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    seller_login = mysql_client.post(
        "/api/auth/login",
        json={"email": "seller@example.com", "password": "Seller123!"},
    )
    assert admin_login.status_code == 200
    assert seller_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}
    seller_headers = {"Authorization": f"Bearer {seller_login.json()['data']['access_token']}"}

    listing = mysql_client.get("/api/admin/products", headers=admin_headers, params={"audit_status": "PENDING"})
    assert listing.status_code == 200
    product_id = listing.json()["data"][0]["id"]

    request_changes = mysql_client.post(
        f"/api/admin/products/{product_id}/audit",
        headers=admin_headers,
        json={"decision": "REQUEST_CHANGES", "note": "请补充商品细节"},
    )
    assert request_changes.status_code == 200
    payload = request_changes.json()["data"]
    assert payload["audit_status"] == "CHANGES_REQUESTED"
    assert payload["product_status"] == "NEEDS_REVISION"

    update = mysql_client.put(
        f"/api/products/{product_id}",
        headers=seller_headers,
        json={
            "title": "已补充细节的商品",
            "tags": {"condition": "近新", "keywords": ["支持验机", "补充细节"]},
        },
    )
    assert update.status_code == 200
    assert update.json()["data"]["title"] == "已补充细节的商品"
    assert update.json()["data"]["tags"]["condition"] == "近新"

    mine = mysql_client.get("/api/products/mine", headers=seller_headers)
    assert mine.status_code == 200
    mine_payload = mine.json()["data"]
    assert any(item["id"] == product_id and item["audit_status"] == "CHANGES_REQUESTED" for item in mine_payload)

    resubmit = mysql_client.post(
        f"/api/products/{product_id}/resubmit",
        headers=seller_headers,
    )
    assert resubmit.status_code == 200
    resubmit_payload = resubmit.json()["data"]
    assert resubmit_payload["audit_status"] == "PENDING"
    assert resubmit_payload["product_status"] == "DRAFT"
    assert resubmit_payload["tags"]["condition"] == "近新"


def test_my_products_handles_legacy_null_tags(mysql_client):
    seller_login = mysql_client.post(
        "/api/auth/login",
        json={"email": "seller@example.com", "password": "Seller123!"},
    )
    assert seller_login.status_code == 200
    seller_token = seller_login.json()["data"]["access_token"]
    seller_headers = {"Authorization": f"Bearer {seller_token}"}
    seller_me = mysql_client.get("/api/auth/me", headers=seller_headers)
    assert seller_me.status_code == 200
    seller_id = seller_me.json()["data"]["id"]

    from app.core.database import SessionLocal
    from app.models.entities import Product

    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.seller_id == seller_id).first()
        assert product is not None
        product.tags = None
        db.commit()
    finally:
        db.close()

    mine = mysql_client.get("/api/products/mine", headers=seller_headers)
    assert mine.status_code == 200
    payload = mine.json()["data"]
    assert payload
    assert isinstance(payload[0]["tags"], dict)


def test_my_products_route_is_not_shadowed_by_product_detail(mysql_client):
    seller_login = mysql_client.post(
        "/api/auth/login",
        json={"email": "seller@example.com", "password": "Seller123!"},
    )
    buyer_login = mysql_client.post(
        "/api/auth/login",
        json={"email": "buyer@example.com", "password": "Buyer123!"},
    )
    assert seller_login.status_code == 200
    assert buyer_login.status_code == 200

    seller_headers = {"Authorization": f"Bearer {seller_login.json()['data']['access_token']}"}
    buyer_headers = {"Authorization": f"Bearer {buyer_login.json()['data']['access_token']}"}

    seller_mine = mysql_client.get("/api/products/mine", headers=seller_headers)
    assert seller_mine.status_code == 200
    assert isinstance(seller_mine.json()["data"], list)
    assert seller_mine.json()["data"]

    buyer_mine = mysql_client.get("/api/products/mine", headers=buyer_headers)
    assert buyer_mine.status_code == 200
    assert buyer_mine.json()["data"] == []


def test_public_seller_profile_and_products(mysql_client):
    seller_login = mysql_client.post(
        "/api/auth/login",
        json={"email": "seller@example.com", "password": "Seller123!"},
    )
    assert seller_login.status_code == 200
    seller_headers = {"Authorization": f"Bearer {seller_login.json()['data']['access_token']}"}
    seller_me = mysql_client.get("/api/auth/me", headers=seller_headers)
    assert seller_me.status_code == 200
    seller_id = seller_me.json()["data"]["id"]

    seller = mysql_client.get(f"/api/users/{seller_id}")
    assert seller.status_code == 200
    payload = seller.json()["data"]
    assert payload["display_name"] == "林川"
    assert payload["avatar_url"].startswith("/marketplace/avatars/")
    assert payload["headline"]
    assert payload["response_summary"]
    assert payload["trust_highlights"]
    assert payload["active_products"] >= 1
    assert payload["trust_score"] >= 1
    assert payload["preferred_deal_methods"]

    products = mysql_client.get(f"/api/users/{seller_id}/products")
    assert products.status_code == 200
    listing = products.json()["data"]
    assert listing
    assert all(item["seller_id"] == seller_id for item in listing)


def test_database_views_and_functions_are_queryable(mysql_client):
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        display_status = db.execute(
            text("SELECT fn_product_display_status('APPROVED', 'ACTIVE', 1)")
        ).scalar_one()
        trust_level = db.execute(
            text("SELECT fn_seller_trust_level(12, 4.8, 0)")
        ).scalar_one()
        active_catalog_count = db.execute(
            text("SELECT COUNT(*) FROM vw_active_product_catalog")
        ).scalar_one()
        seller_summary_count = db.execute(
            text("SELECT COUNT(*) FROM vw_seller_operational_summary")
        ).scalar_one()
        risk_rows = db.execute(
            text("SELECT pending_reports, pending_appeals, pending_audit_tasks FROM vw_admin_risk_overview")
        ).mappings().all()
    finally:
        db.close()

    assert display_status == "ACTIVE"
    assert trust_level == "HIGH"
    assert active_catalog_count >= 1
    assert seller_summary_count >= 1
    assert len(risk_rows) == 1


def test_report_insert_trigger_creates_governance_artifacts(mysql_client):
    from app.core.database import SessionLocal
    from app.models.entities import AuditTask, OperationLog, Report, User

    db = SessionLocal()
    try:
        buyer = db.query(User).filter(User.email == "buyer@example.com").one()
        report = Report(
            reporter_id=buyer.id,
            target_type="PRODUCT",
            target_id=1,
            reason="trigger managed report entry",
        )
        db.add(report)
        db.flush()

        tasks = (
            db.query(AuditTask)
            .filter(AuditTask.entity_type == "REPORT", AuditTask.entity_id == report.id)
            .all()
        )
        logs = [
            item for item in db.query(OperationLog).order_by(OperationLog.id.asc()).all()
            if item.action == "report.submit" and item.details.get("report_id") == report.id
        ]
    finally:
        db.rollback()
        db.close()

    assert len(tasks) == 1
    assert len(logs) == 1
