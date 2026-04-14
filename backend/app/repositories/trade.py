from sqlalchemy.orm import Session

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
        return self.db.query(Review).filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()

    def create_favorite(self, user_id: int, product_id: int) -> Favorite:
        favorite = Favorite(user_id=user_id, product_id=product_id)
        self.db.add(favorite)
        self.db.flush()
        return favorite

    def delete_favorite(self, user_id: int, product_id: int) -> None:
        self.db.query(Favorite).filter_by(user_id=user_id, product_id=product_id).delete()

    def list_favorites(self, user_id: int) -> list[Favorite]:
        return self.db.query(Favorite).filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()

    def capture_history(self, user_id: int, product_id: int) -> BrowseHistory:
        entry = BrowseHistory(user_id=user_id, product_id=product_id)
        self.db.add(entry)
        self.db.flush()
        return entry

    def recent_history(self, user_id: int) -> list[BrowseHistory]:
        return self.db.query(BrowseHistory).filter_by(user_id=user_id).order_by(BrowseHistory.created_at.desc()).limit(20).all()

    def add_material(self, material: RecommendationMaterial) -> None:
        self.db.add(material)

    def popular_products(self, limit: int = 10) -> list[Product]:
        return self.db.query(Product).order_by(Product.created_at.desc()).limit(limit).all()

