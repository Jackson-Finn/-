from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.enums import ReviewType
from app.models.entities import BrowseHistory, Favorite, Order, OrderItem, Product, RecommendationMaterial, Review


class TradeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, order: Order) -> Order:
        self.db.add(order)
        self.db.flush()
        return order

    def add_order_item(self, order_id: int, product_id: int, quantity: int, unit_price: float) -> OrderItem:
        item = OrderItem(order_id=order_id, product_id=product_id, quantity=quantity, unit_price=unit_price)
        self.db.add(item)
        self.db.flush()
        return item

    def list_orders_for_user(self, user_id: int) -> list[Order]:
        return self.db.query(Order).filter((Order.buyer_id == user_id) | (Order.seller_id == user_id)).order_by(Order.created_at.desc()).all()

    def get_order(self, order_id: int) -> Order | None:
        return self.db.get(Order, order_id)

    def create_review(self, review: Review) -> Review:
        self.db.add(review)
        self.db.flush()
        return review

    def list_reviews_for_product(self, product_id: int) -> list[Review]:
        return (
            self.db.query(Review)
            .filter(
                Review.product_id == product_id,
                or_(Review.review_type == ReviewType.PRODUCT.value, Review.review_type.is_(None)),
            )
            .order_by(Review.created_at.desc())
            .all()
        )

    def list_reviews_for_seller(self, seller_id: int) -> list[Review]:
        return (
            self.db.query(Review)
            .filter(Review.seller_id == seller_id, Review.review_type == ReviewType.SELLER.value)
            .order_by(Review.created_at.desc())
            .all()
        )

    def find_review(self, order_id: int, review_type: str) -> Review | None:
        return self.db.query(Review).filter_by(order_id=order_id, review_type=review_type).first()

    def list_reviews_for_orders(self, order_ids: list[int]) -> list[Review]:
        if not order_ids:
            return []
        return self.db.query(Review).filter(Review.order_id.in_(order_ids)).all()

    def create_favorite(self, user_id: int, product_id: int) -> Favorite:
        favorite = Favorite(user_id=user_id, product_id=product_id)
        self.db.add(favorite)
        self.db.flush()
        return favorite

    def has_favorite(self, user_id: int, product_id: int) -> bool:
        return self.db.query(Favorite).filter_by(user_id=user_id, product_id=product_id).first() is not None

    def delete_favorite(self, user_id: int, product_id: int) -> None:
        self.db.query(Favorite).filter_by(user_id=user_id, product_id=product_id).delete()

    def list_favorites(self, user_id: int) -> list[Favorite]:
        return self.db.query(Favorite).filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()

    def capture_history(self, user_id: int, product_id: int) -> BrowseHistory:
        entry = (
            self.db.query(BrowseHistory)
            .filter_by(user_id=user_id, product_id=product_id)
            .first()
        )
        if entry:
            entry.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            return entry
        entry = BrowseHistory(user_id=user_id, product_id=product_id)
        self.db.add(entry)
        self.db.flush()
        return entry

    def recent_history(self, user_id: int) -> list[BrowseHistory]:
        return (
            self.db.query(BrowseHistory)
            .filter_by(user_id=user_id)
            .order_by(BrowseHistory.updated_at.desc(), BrowseHistory.created_at.desc(), BrowseHistory.id.desc())
            .limit(50)
            .all()
        )

    def prune_history(self, user_id: int, keep_limit: int = 50) -> None:
        stale_entries = (
            self.db.query(BrowseHistory)
            .filter_by(user_id=user_id)
            .order_by(BrowseHistory.updated_at.desc(), BrowseHistory.created_at.desc(), BrowseHistory.id.desc())
            .offset(keep_limit)
            .all()
        )
        for entry in stale_entries:
            self.db.delete(entry)

    def add_material(self, material: RecommendationMaterial) -> None:
        self.db.add(material)

    def popular_products(self, limit: int = 10) -> list[Product]:
        return self.db.query(Product).order_by(Product.created_at.desc()).limit(limit).all()
