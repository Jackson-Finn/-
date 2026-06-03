from sqlalchemy.orm import Session

from app.core.enums import PresenceStatus
from app.core.errors import AppError
from app.core.realtime import manager
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.catalog import CatalogRepository
from app.repositories.identity import IdentityRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class IdentityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IdentityRepository(db)
        self.catalog_repo = CatalogRepository(db)

    def register(self, payload: RegisterRequest):
        if self.repo.get_user_by_email(payload.email):
            raise AppError("Email already registered", status_code=409)
        user = self.repo.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, payload: LoginRequest) -> str:
        user = self.repo.get_user_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AppError("Invalid credentials", status_code=401)
        return create_access_token(str(user.id))

    def list_users(self):
        return self.repo.list_users()

    def list_roles(self):
        return self.repo.list_roles()

    def list_permissions(self):
        return self.repo.list_permissions()

    def assign_roles(self, user_id: int, role_ids: list[int]) -> None:
        self.repo.assign_roles(user_id, role_ids)
        self.db.commit()

    def get_public_seller(self, user_id: int) -> dict:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise AppError("Seller not found", status_code=404)
        metrics = self.repo.seller_metrics_from_view(user_id) or self.repo.seller_metrics(user_id)
        persona = self._seller_persona(user.id, user.display_name)
        response_time = persona["response_time_minutes"] if metrics["completed_orders"] else max(persona["response_time_minutes"], 35)
        response_rate = min(99, persona["response_rate_base"] + metrics["active_products"] + metrics["completed_orders"])
        trust_score = min(98, persona["trust_score_base"] + metrics["completed_orders"] * 2 + metrics["review_count"])
        average_rating = metrics["average_rating"] or persona["fallback_rating"]
        report_count = int(metrics.get("report_count", 0))
        trust_level = str(metrics.get("trust_level", "MEDIUM"))
        quality_band = str(metrics.get("quality_band", "NEW"))
        return {
            "id": user.id,
            "display_name": user.display_name,
            "email_masked": self._mask_email(user.email),
            "avatar_url": persona["avatar_url"],
            "headline": persona["headline"],
            "bio": persona["bio"],
            "city": persona["city"],
            "response_rate": response_rate,
            "response_time_minutes": response_time,
            "response_summary": f"近 30 天回复率 {response_rate}% ，通常 {response_time} 分钟内回应。",
            "presence_status": self._public_presence_status(user),
            "active_products": metrics["active_products"],
            "total_products": metrics["total_products"],
            "completed_orders": metrics["completed_orders"],
            "average_rating": average_rating,
            "review_count": metrics["review_count"],
            "verification_badges": persona["verification_badges"] if user.status == "ACTIVE" else ["平台用户"],
            "preferred_deal_methods": persona["preferred_deal_methods"],
            "trust_score": trust_score,
            "on_sale_count": metrics["active_products"],
            "trust_highlights": [
                {
                    "title": "信用评分",
                    "detail": f"{trust_score} / 100，数据库按成交、评分与举报量评估为 {trust_level}。",
                },
                {"title": "历史交易", "detail": f"累计完成 {metrics['completed_orders']} 笔交易，当前公开在售 {metrics['active_products']} 件。"},
                {"title": "服务分层", "detail": f"数据库按评价质量将卖家分层为 {quality_band}，用于辅助展示卖家稳定度。"},
                {"title": "治理记录", "detail": f"关联举报 {report_count} 条，平台可追溯交易与申诉记录。"},
            ],
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    def list_public_seller_products(self, user_id: int) -> list[dict]:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise AppError("Seller not found", status_code=404)
        return [self._serialize_product(product) for product in self.repo.list_public_products_by_seller(user_id)]

    @staticmethod
    def _public_presence_status(user) -> str:
        if user.presence_status != PresenceStatus.ONLINE.value:
            return PresenceStatus.OFFLINE.value
        return PresenceStatus.ONLINE.value if manager.is_connected(user.id) else PresenceStatus.OFFLINE.value

    @staticmethod
    def _mask_email(email: str) -> str:
        if "@" not in email:
            return email
        name, domain = email.split("@", 1)
        if len(name) <= 2:
            masked = f"{name[0]}*"
        else:
            masked = f"{name[:2]}***"
        return f"{masked}@{domain}"

    @staticmethod
    def _seller_persona(user_id: int, display_name: str) -> dict:
        personas = {
            2: {
                "avatar_url": "/marketplace/avatars/seller-lc.svg",
                "headline": "数码与影像器材爱好者，偏好把闲置整理干净再出。",
                "bio": f"{display_name} 平时会把设备擦拭、充满电并逐项拍清楚，能当面验机的都会提前约好时间，避免买家来回跑空。",
                "city": "上海",
                "response_time_minutes": 12,
                "response_rate_base": 92,
                "trust_score_base": 85,
                "fallback_rating": 4.9,
                "verification_badges": ["实名认证", "芝麻信用已验证", "平台活跃卖家"],
                "preferred_deal_methods": ["同城面交", "顺丰到付", "地铁站自提"],
                "deal_style": "支持先沟通后下单，数码类商品默认可现场验货。",
            },
            5: {
                "avatar_url": "/marketplace/avatars/seller-qm.svg",
                "headline": "长期整理工作室样品机与耳机设备，更新频率稳定。",
                "bio": f"{display_name} 会把在售商品的配件、磨损位置和寄送方式写清楚，适合想快速判断成色与来源的买家。",
                "city": "深圳",
                "response_time_minutes": 18,
                "response_rate_base": 90,
                "trust_score_base": 84,
                "fallback_rating": 4.8,
                "verification_badges": ["实名认证", "工作室卖家"],
                "preferred_deal_methods": ["顺丰保价", "同城闪送", "预约自提"],
                "deal_style": "偏向快递保价发出，支持视频验机和配件确认。",
            },
            6: {
                "avatar_url": "/marketplace/avatars/seller-yr.svg",
                "headline": "家居与手冲器具整理者，商品保养细节写得比较实。",
                "bio": f"{display_name} 出售的多是自用家居和收藏品，会把使用频率、清洁情况和小瑕疵提前说清楚，避免交易后产生预期落差。",
                "city": "杭州",
                "response_time_minutes": 25,
                "response_rate_base": 89,
                "trust_score_base": 83,
                "fallback_rating": 4.7,
                "verification_badges": ["实名认证", "平台老卖家"],
                "preferred_deal_methods": ["同城面交", "邮寄", "周末自提"],
                "deal_style": "支持先看细节图再决定，家居类商品偏向同城交易。",
            },
        }
        return personas.get(
            user_id,
            {
                "avatar_url": "/marketplace/avatars/seller-default.svg",
                "headline": "认真描述闲置信息，交易节奏稳。",
                "bio": f"{display_name} 会尽量把在售商品的配件、成色和交易方式说清楚。",
                "city": "上海",
                "response_time_minutes": 30,
                "response_rate_base": 88,
                "trust_score_base": 82,
                "fallback_rating": 4.6,
                "verification_badges": ["平台卖家"],
                "preferred_deal_methods": ["邮寄", "同城面交"],
                "deal_style": "交易前可先沟通细节与验货方式。",
            },
        )

    def _serialize_product(self, product) -> dict:
        images = [item.url for item in self.catalog_repo.list_product_images(product.id)]
        seller = self.catalog_repo.get_user(product.seller_id)
        category = self.catalog_repo.get_category(product.category_id)
        tags = product.tags if isinstance(product.tags, dict) else {}
        return {
            "id": product.id,
            "seller_id": product.seller_id,
            "seller_name": seller.display_name if seller else None,
            "category_id": product.category_id,
            "category_name": category.name if category else None,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "product_status": product.product_status,
            "audit_status": product.audit_status,
            "tags": tags,
            "images": images,
            "cover_image": images[0] if images else None,
            "condition_label": str(tags.get("condition_label") or tags.get("condition") or "成色良好"),
            "hero_summary": str(tags.get("hero_summary") or product.description[:72]),
            "updated_at": product.updated_at,
        }
