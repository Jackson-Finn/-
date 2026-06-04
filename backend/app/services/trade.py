from sqlalchemy.orm import Session

from app.core.enums import OrderStatus, ProductStatus, ReviewType
from app.core.errors import AppError
from app.core.events import DomainEvent, EventPublisher
from app.core.realtime import manager
from app.models.entities import Order, RecommendationMaterial, Review
from app.repositories.catalog import CatalogRepository
from app.repositories.trade import TradeRepository
from app.schemas.order import OrderCreateRequest, ReviewCreateRequest


class TradeService:
    def __init__(self, db: Session):
        self.db = db
        self.catalog_repo = CatalogRepository(db)
        self.repo = TradeRepository(db)
        self.publisher = EventPublisher(db)

    def create_order(self, buyer_id: int, payload: OrderCreateRequest):
        product = self.catalog_repo.get_product(payload.product_id)
        if not product:
            raise AppError("Product not found", status_code=404)
        if product.audit_status != "APPROVED" or product.product_status != ProductStatus.ACTIVE.value:
            raise AppError("Product is not available for purchase", status_code=400)
        if product.stock < payload.quantity:
            raise AppError("Insufficient stock", status_code=409)
        order = Order(
            buyer_id=buyer_id,
            seller_id=product.seller_id,
            product_id=product.id,
            total_amount=product.price * payload.quantity,
            status=OrderStatus.CREATED.value,
        )
        self.repo.create_order(order)
        self.repo.add_order_item(order.id, product.id, payload.quantity, product.price)
        product.stock -= payload.quantity
        self.repo.add_material(
            RecommendationMaterial(
                user_id=buyer_id,
                product_id=product.id,
                material_type="ORDER",
                payload={"order_id": order.id},
            )
        )
        self.publisher.publish(
            DomainEvent(
                event_type="OrderCreated",
                aggregate_type="Order",
                aggregate_id=str(order.id),
                payload={"order_id": order.id, "product_id": product.id},
            )
        )
        self.db.commit()
        self.db.refresh(order)
        self.db.refresh(product)
        manager.broadcast(
            "StockUpdated",
            {"product_id": product.id, "stock": product.stock},
        )
        return order

    def list_orders(self, user_id: int):
        return self.repo.list_orders_for_user(user_id)

    def serialize_orders(self, user_id: int) -> list[dict]:
        orders = self.list_orders(user_id)
        review_map = self._reviews_by_order([order.id for order in orders])
        return [self.serialize_order(order, user_id, review_map) for order in orders]

    def get_order(self, order_id: int, user_id: int):
        order = self.repo.get_order(order_id)
        if not order or user_id not in {order.buyer_id, order.seller_id}:
            raise AppError("Order not found", status_code=404)
        return order

    def cancel_order(self, order_id: int, user_id: int):
        order = self.get_order(order_id, user_id)
        if order.buyer_id != user_id or order.status != OrderStatus.CREATED.value:
            raise AppError("Order cannot be cancelled", status_code=400)
        order.status = OrderStatus.CANCELLED.value

        order_items = self.repo.get_order_items(order_id)
        for item in order_items:
            product = self.catalog_repo.get_product(item.product_id)
            if product:
                product.stock += item.quantity

        self.publisher.publish(
            DomainEvent(
                event_type="OrderCancelled",
                aggregate_type="Order",
                aggregate_id=str(order.id),
                payload={"order_id": order.id},
            )
        )
        self.db.commit()
        return order

    def confirm_order(self, order_id: int, user_id: int):
        order = self.get_order(order_id, user_id)
        if order.buyer_id != user_id or order.status != OrderStatus.CREATED.value:
            raise AppError("Order cannot be confirmed", status_code=400)
        order.status = OrderStatus.COMPLETED.value
        self.publisher.publish(
            DomainEvent(
                event_type="OrderCompleted",
                aggregate_type="Order",
                aggregate_id=str(order.id),
                payload={"order_id": order.id, "product_id": order.product_id},
            )
        )
        self.db.commit()
        return order

    def create_review(self, user_id: int, payload: ReviewCreateRequest):
        order = self.repo.get_order(payload.order_id)
        if not order or order.buyer_id != user_id or order.status == OrderStatus.CANCELLED.value:
            raise AppError("Order is not eligible for review", status_code=400)
        saved_reviews: list[Review] = []

        if payload.product_review:
            review, was_created = self._save_review(
                order=order,
                user_id=user_id,
                review_type=ReviewType.PRODUCT.value,
                rating=payload.product_review.rating,
                content=payload.product_review.content,
            )
            saved_reviews.append(review)
            self.repo.add_material(
                RecommendationMaterial(
                    user_id=user_id,
                    product_id=order.product_id,
                    material_type="REVIEW",
                    payload={"rating": payload.product_review.rating, "review_type": ReviewType.PRODUCT.value},
                )
            )
            self.publisher.publish(
                DomainEvent(
                    event_type="ReviewCreated" if was_created else "ReviewUpdated",
                    aggregate_type="Review",
                    aggregate_id=str(review.id),
                    payload={
                        "product_id": order.product_id,
                        "seller_id": order.seller_id,
                        "user_id": user_id,
                        "review_type": review.review_type,
                    },
                )
            )

        if payload.seller_review:
            review, was_created = self._save_review(
                order=order,
                user_id=user_id,
                review_type=ReviewType.SELLER.value,
                rating=payload.seller_review.rating,
                content=payload.seller_review.content,
            )
            saved_reviews.append(review)
            self.publisher.publish(
                DomainEvent(
                    event_type="ReviewCreated" if was_created else "ReviewUpdated",
                    aggregate_type="Review",
                    aggregate_id=str(review.id),
                    payload={
                        "product_id": order.product_id,
                        "seller_id": order.seller_id,
                        "user_id": user_id,
                        "review_type": review.review_type,
                    },
                )
            )

        self.db.commit()
        for review in saved_reviews:
            self.db.refresh(review)
        return saved_reviews

    def list_reviews(self, product_id: int):
        return self.repo.list_reviews_for_product(product_id)

    def list_seller_reviews(self, seller_id: int):
        return self.repo.list_reviews_for_seller(seller_id)

    def serialize_review(self, review: Review) -> dict:
        reviewer = self.catalog_repo.get_user(review.user_id)
        return {
            "id": review.id,
            "order_id": review.order_id,
            "user_id": review.user_id,
            "seller_id": review.seller_id,
            "product_id": review.product_id,
            "review_type": review.review_type or ReviewType.PRODUCT.value,
            "reviewer_name": reviewer.display_name if reviewer else "匿名买家",
            "rating": review.rating,
            "content": review.content,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
        }

    def add_favorite(self, user_id: int, product_id: int):
        if self.repo.has_favorite(user_id, product_id):
            return
        self.repo.create_favorite(user_id, product_id)
        self.repo.add_material(
            RecommendationMaterial(
                user_id=user_id,
                product_id=product_id,
                material_type="FAVORITE",
                payload={},
            )
        )
        self.publisher.publish(
            DomainEvent(
                event_type="FavoriteChanged",
                aggregate_type="Favorite",
                aggregate_id=f"{user_id}:{product_id}",
                payload={"action": "ADD", "product_id": product_id, "user_id": user_id},
            )
        )
        self.db.commit()

    def remove_favorite(self, user_id: int, product_id: int):
        self.repo.delete_favorite(user_id, product_id)
        self.publisher.publish(
            DomainEvent(
                event_type="FavoriteChanged",
                aggregate_type="Favorite",
                aggregate_id=f"{user_id}:{product_id}",
                payload={"action": "REMOVE", "product_id": product_id, "user_id": user_id},
            )
        )
        self.db.commit()

    def list_favorites(self, user_id: int):
        favorites = self.repo.list_favorites(user_id)
        serialized = []
        for favorite in favorites:
            product_summary = self._product_summary_by_id(favorite.product_id)
            if not product_summary:
                continue
            serialized.append(
                {
                    "id": favorite.id,
                    "product_id": favorite.product_id,
                    "created_at": favorite.created_at,
                    "product_summary": product_summary,
                }
            )
        return serialized

    def capture_history(self, user_id: int, product_id: int):
        history = self.repo.capture_history(user_id, product_id)
        self.repo.prune_history(user_id, keep_limit=50)
        self.repo.add_material(
            RecommendationMaterial(
                user_id=user_id,
                product_id=product_id,
                material_type="HISTORY",
                payload={},
            )
        )
        self.publisher.publish(
            DomainEvent(
                event_type="HistoryCaptured",
                aggregate_type="History",
                aggregate_id=str(history.id),
                payload={"product_id": product_id, "user_id": user_id},
            )
        )
        self.db.commit()
        return history

    def recent_history(self, user_id: int):
        entries = self.repo.recent_history(user_id)
        serialized = []
        for entry in entries:
            product_summary = self._product_summary_by_id(entry.product_id)
            if not product_summary:
                continue
            serialized.append(
                {
                    "id": entry.id,
                    "product_id": entry.product_id,
                    "created_at": entry.created_at,
                    "product_summary": product_summary,
                }
            )
        return serialized

    def serialize_order(self, order: Order, user_id: int, review_map: dict[int, dict[str, Review]] | None = None) -> dict:
        review_bucket = review_map.get(order.id, {}) if review_map else {}
        is_review_eligible = order.buyer_id == user_id and order.status != OrderStatus.CANCELLED.value
        return {
            "id": order.id,
            "buyer_id": order.buyer_id,
            "seller_id": order.seller_id,
            "product_id": order.product_id,
            "total_amount": order.total_amount,
            "status": order.status,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "product_summary": self._product_summary_by_id(order.product_id),
            "is_buyer": order.buyer_id == user_id,
            "is_seller": order.seller_id == user_id,
            "can_confirm": order.buyer_id == user_id and order.status == OrderStatus.CREATED.value,
            "can_review_product": is_review_eligible,
            "can_review_seller": is_review_eligible,
            "product_review": self.serialize_review(review_bucket[ReviewType.PRODUCT.value]) if ReviewType.PRODUCT.value in review_bucket else None,
            "seller_review": self.serialize_review(review_bucket[ReviewType.SELLER.value]) if ReviewType.SELLER.value in review_bucket else None,
            "next_actions": self._next_actions(order, user_id, review_bucket),
        }

    def _reviews_by_order(self, order_ids: list[int]) -> dict[int, dict[str, Review]]:
        review_map: dict[int, dict[str, Review]] = {order_id: {} for order_id in order_ids}
        for review in self.repo.list_reviews_for_orders(order_ids):
            review_type = review.review_type or ReviewType.PRODUCT.value
            review_map.setdefault(review.order_id, {})[review_type] = review
        return review_map

    def _save_review(self, order: Order, user_id: int, review_type: str, rating: int, content: str) -> tuple[Review, bool]:
        review = self.repo.find_review(order.id, review_type)
        if review:
            if review.user_id != user_id:
                raise AppError("Review does not belong to current user", status_code=403)
            review.rating = rating
            review.content = content
            self.db.flush()
            return review, False
        review = Review(
            order_id=order.id,
            product_id=order.product_id,
            seller_id=order.seller_id,
            user_id=user_id,
            review_type=review_type,
            rating=rating,
            content=content,
        )
        self.repo.create_review(review)
        return review, True

    @staticmethod
    def _next_actions(order: Order, user_id: int, review_bucket: dict[str, Review]) -> list[str]:
        actions: list[str] = []
        if order.buyer_id != user_id:
            return actions
        if order.status == OrderStatus.CREATED.value:
            actions.append("继续与卖家确认验货和交付方式")
            actions.append("确认无误后完成收货")
        if order.status == OrderStatus.COMPLETED.value:
            actions.append("订单已完成，可回看聊天和评价记录")
        if ReviewType.PRODUCT.value not in review_bucket:
            actions.append("补充商品评价，沉淀给后续买家参考")
        if ReviewType.SELLER.value not in review_bucket:
            actions.append("补充卖家评价，反馈沟通与交付体验")
        return actions[:3]

    def _product_summary_by_id(self, product_id: int) -> dict | None:
        product = self.catalog_repo.get_product(product_id)
        if not product:
            return None
        seller = self.catalog_repo.get_user(product.seller_id)
        category = self.catalog_repo.get_category(product.category_id)
        images = self.catalog_repo.list_product_images(product.id)
        tags = product.tags if isinstance(product.tags, dict) else {}
        detail_sections = tags.get("detail_sections") if isinstance(tags.get("detail_sections"), list) else []
        first_section = detail_sections[0]["body"] if detail_sections and isinstance(detail_sections[0], dict) else product.description
        return {
            "id": product.id,
            "seller_id": product.seller_id,
            "seller_name": seller.display_name if seller else None,
            "category_name": category.name if category else None,
            "title": product.title,
            "price": product.price,
            "product_status": product.product_status,
            "audit_status": product.audit_status,
            "cover_image": images[0].url if images else None,
            "hero_summary": str(tags.get("hero_summary") or first_section[:88]),
            "condition_label": str(tags.get("condition_label") or tags.get("condition") or "成色良好"),
            "updated_at": product.updated_at,
        }
