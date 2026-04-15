from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import AuditStatus, OrderStatus, ProductStatus, ReviewType
from app.models.entities import Order, Permission, Product, Review, Role, User, UserRole


class IdentityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter_by(email=email).first()

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def create_user(self, *, email: str, password_hash: str, display_name: str) -> User:
        user = User(email=email, password_hash=password_hash, display_name=display_name)
        self.db.add(user)
        self.db.flush()
        return user

    def list_users(self) -> list[User]:
        return self.db.query(User).order_by(User.created_at.desc()).all()

    def list_public_products_by_seller(self, seller_id: int) -> list[Product]:
        return (
            self.db.query(Product)
            .filter(
                Product.seller_id == seller_id,
                Product.product_status == ProductStatus.ACTIVE.value,
                Product.audit_status == AuditStatus.APPROVED.value,
            )
            .order_by(Product.updated_at.desc(), Product.created_at.desc())
            .all()
        )

    def seller_metrics(self, seller_id: int) -> dict:
        total_products = self.db.query(func.count(Product.id)).filter(Product.seller_id == seller_id).scalar() or 0
        active_products = (
            self.db.query(func.count(Product.id))
            .filter(
                Product.seller_id == seller_id,
                Product.product_status == ProductStatus.ACTIVE.value,
                Product.audit_status == AuditStatus.APPROVED.value,
            )
            .scalar()
            or 0
        )
        completed_orders = (
            self.db.query(func.count(Order.id))
            .filter(Order.seller_id == seller_id, Order.status == OrderStatus.COMPLETED.value)
            .scalar()
            or 0
        )
        average_rating, review_count = (
            self.db.query(func.avg(Review.rating), func.count(Review.id))
            .filter(
                Review.seller_id == seller_id,
                Review.review_type == ReviewType.SELLER.value,
            )
            .one()
        )
        return {
            "total_products": int(total_products),
            "active_products": int(active_products),
            "completed_orders": int(completed_orders),
            "average_rating": round(float(average_rating or 0), 1),
            "review_count": int(review_count or 0),
        }

    def list_roles(self) -> list[Role]:
        return self.db.query(Role).order_by(Role.id.asc()).all()

    def list_permissions(self) -> list[Permission]:
        return self.db.query(Permission).order_by(Permission.id.asc()).all()

    def assign_roles(self, user_id: int, role_ids: list[int]) -> None:
        self.db.query(UserRole).filter_by(user_id=user_id).delete()
        for role_id in role_ids:
            self.db.add(UserRole(user_id=user_id, role_id=role_id))
