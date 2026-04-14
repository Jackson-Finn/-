from sqlalchemy.orm import Session

from app.core.enums import OrderStatus, ProductStatus
from app.core.errors import AppError
from app.core.events import DomainEvent, EventPublisher
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
        return order

    def list_orders(self, user_id: int):
        return self.repo.list_orders_for_user(user_id)

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
        if not order or order.buyer_id != user_id or order.status != OrderStatus.COMPLETED.value:
            raise AppError("Order is not eligible for review", status_code=400)
        review = Review(
            order_id=order.id,
            product_id=order.product_id,
            user_id=user_id,
            rating=payload.rating,
            content=payload.content,
        )
        self.repo.create_review(review)
        self.repo.add_material(
            RecommendationMaterial(
                user_id=user_id,
                product_id=order.product_id,
                material_type="REVIEW",
                payload={"rating": payload.rating},
            )
        )
        self.publisher.publish(
            DomainEvent(
                event_type="ReviewCreated",
                aggregate_type="Review",
                aggregate_id=str(review.id),
                payload={"product_id": order.product_id, "user_id": user_id},
            )
        )
        self.db.commit()
        self.db.refresh(review)
        return review

    def list_reviews(self, product_id: int):
        return self.repo.list_reviews_for_product(product_id)

    def add_favorite(self, user_id: int, product_id: int):
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
        return self.repo.list_favorites(user_id)

    def capture_history(self, user_id: int, product_id: int):
        history = self.repo.capture_history(user_id, product_id)
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
        return self.repo.recent_history(user_id)

