from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import ChatMessage, JobRunLog, Order, Product, RecommendationSnapshot, Report
from app.repositories.catalog import CatalogRepository
from app.repositories.intelligence import IntelligenceRepository
from app.repositories.trade import TradeRepository


class IntelligenceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IntelligenceRepository(db)
        self.catalog_repo = CatalogRepository(db)
        self.trade_repo = TradeRepository(db)

    @staticmethod
    def _product_card(product: Product | None) -> dict:
        if not product:
            return {}
        return {
            "product_id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "product_status": product.product_status,
            "audit_status": product.audit_status,
            "seller_id": product.seller_id,
        }

    def _hydrate_recommendation_items(self, raw_items: list[dict]) -> list[dict]:
        items: list[dict] = []
        for item in raw_items:
            product_id = item.get("product_id") or item.get("id")
            product = self.catalog_repo.get_product(product_id) if product_id else None
            payload = self._product_card(product)
            if payload:
                payload["reason"] = item.get("reason", "Behavior-based recommendation")
                items.append(payload)
        return items

    def recommend_home(self, user_id: int | None):
        snapshot = self.repo.get_snapshot(user_id, "HOME")
        if snapshot:
            return {"items": self._hydrate_recommendation_items(snapshot.payload.get("items", []))}
        products = self.trade_repo.popular_products(limit=6)
        payload = {
            "items": [
                {
                    **self._product_card(product),
                    "reason": "Popular and recent inventory",
                }
                for product in products
            ]
        }
        self.repo.create_snapshot(RecommendationSnapshot(user_id=user_id, scene="HOME", payload=payload))
        self.db.commit()
        return payload

    def recommend_related(self, product_id: int):
        product = self.catalog_repo.get_product(product_id)
        related = [candidate for candidate in self.catalog_repo.list_products() if candidate.id != product_id][:6]
        return {
            "base_product_id": product_id,
            "items": [
                {
                    **self._product_card(item),
                    "reason": f"Related to {product.title}" if product else "Marketplace similarity",
                }
                for item in related
            ],
            "reason": f"Same marketplace scene around {product.title}" if product else "Marketplace fallback recommendation",
        }

    def rebuild_recommendations(self):
        payload = self.recommend_home(user_id=None)
        self.repo.log_job("recommendation_rebuild", "COMPLETED", payload)
        self.db.commit()
        return {"status": "queued", "result": payload}

    def reindex_search(self):
        self.repo.log_job("search_reindex", "COMPLETED", {"mode": "database-fallback"})
        self.db.commit()
        return {"status": "queued", "mode": "database-fallback"}

    def ai_product_draft(self, keywords: list[str], category: str | None):
        result = {
            "title": f"{category or '精选'} {' '.join(keywords[:3])}".strip(),
            "description": f"Auto-generated draft for {', '.join(keywords)}.",
            "highlights": keywords[:5],
        }
        self.repo.log_ai_task("product_draft", str({"keywords": keywords, "category": category}), result)
        self.db.commit()
        return result

    def ai_moderation_preview(self, title: str, description: str):
        risk = "LOW" if "违禁" not in f"{title}{description}" else "HIGH"
        result = {"risk_level": risk, "flags": [] if risk == "LOW" else ["SENSITIVE_TERM"]}
        self.repo.log_ai_task("moderation_preview", title, result)
        self.db.commit()
        return result

    def ai_chat_summary(self, session_id: int):
        messages = (
            self.db.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        joined = " ".join(message.content for message in messages[:6]).strip()
        result = {
            "session_id": session_id,
            "summary": joined[:180] if joined else "No chat content available for summary.",
        }
        self.repo.log_ai_task("chat_summary", f"session:{session_id}", result)
        self.db.commit()
        return result

    def overview(self):
        products = len(self.catalog_repo.list_products())
        pending = len(self.catalog_repo.list_pending_products())
        jobs = self.db.query(JobRunLog).count()
        reports = self.db.query(Report).count()
        orders = self.db.query(Order).count()
        return {"products": products, "pending_audits": pending, "job_count": jobs, "reports": reports, "orders": orders}

    def charts(self):
        order_status = [
            {"name": status or "UNKNOWN", "value": count}
            for status, count in self.db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
        ]
        report_outcome = [
            {"name": status or "UNKNOWN", "value": count}
            for status, count in self.db.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
        ]
        return {
            "orderStatus": order_status,
            "auditQueue": [{"name": "PENDING", "value": len(self.catalog_repo.list_pending_products())}],
            "reportOutcome": report_outcome,
        }
