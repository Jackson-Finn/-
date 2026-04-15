from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.enums import AuditStatus, ProductStatus
from app.models.entities import AuditTask, Category, MediaAsset, Product, ProductImage, Report, User


class CatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_product(self, product: Product) -> Product:
        self.db.add(product)
        self.db.flush()
        return product

    def get_product(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def list_products(self) -> list[Product]:
        return self.db.query(Product).order_by(Product.created_at.desc()).all()

    def list_products_by_seller(self, seller_id: int) -> list[Product]:
        return (
            self.db.query(Product)
            .filter(Product.seller_id == seller_id)
            .order_by(Product.updated_at.desc(), Product.created_at.desc())
            .all()
        )

    def list_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        if not product_ids:
            return []
        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        product_map = {product.id: product for product in products}
        return [product_map[product_id] for product_id in product_ids if product_id in product_map]

    def list_pending_products(self) -> list[Product]:
        return self.db.query(Product).filter_by(audit_status="PENDING").order_by(Product.created_at.asc()).all()

    def list_admin_products(
        self,
        keyword: str | None = None,
        audit_status: str | None = None,
        product_status: str | None = None,
        sort: str = "newest",
    ) -> list[Product]:
        query = self.db.query(Product)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(Product.title.ilike(like), Product.description.ilike(like)))
        if audit_status:
            query = query.filter(Product.audit_status == audit_status)
        if product_status:
            query = query.filter(Product.product_status == product_status)

        order_mapping = {
            "oldest": Product.created_at.asc(),
            "price_asc": Product.price.asc(),
            "price_desc": Product.price.desc(),
            "updated_desc": Product.updated_at.desc(),
            "newest": Product.created_at.desc(),
        }
        query = query.order_by(order_mapping.get(sort, Product.created_at.desc()))
        return query.all()

    def search_products(
        self,
        keyword: str | None = None,
        category: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "newest",
    ) -> list[Product]:
        query = self.db.query(Product).filter(
            Product.product_status == ProductStatus.ACTIVE.value,
            Product.audit_status == AuditStatus.APPROVED.value,
        )
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(Product.title.ilike(like), Product.description.ilike(like)))
        if category:
            like = f"%{category}%"
            query = query.join(Category, Category.id == Product.category_id, isouter=True).filter(Category.name.ilike(like))
        if price_min is not None:
            query = query.filter(Product.price >= price_min)
        if price_max is not None:
            query = query.filter(Product.price <= price_max)
        order_mapping = {
            "price_asc": Product.price.asc(),
            "price_desc": Product.price.desc(),
            "updated_desc": Product.updated_at.desc(),
            "newest": Product.created_at.desc(),
        }
        return query.order_by(order_mapping.get(sort, Product.created_at.desc())).all()

    def search_suggestions(self, keyword: str | None = None, limit: int = 10) -> list[str]:
        normalized = (keyword or "").strip().lower()
        products = (
            self.db.query(Product)
            .filter(
                Product.product_status == ProductStatus.ACTIVE.value,
                Product.audit_status == AuditStatus.APPROVED.value,
            )
            .order_by(Product.created_at.desc())
            .all()
        )
        suggestions: list[str] = []
        seen: set[str] = set()
        for product in products:
            candidates = [product.title]
            tags = product.tags.get("keywords", []) if isinstance(product.tags, dict) else []
            candidates.extend(str(tag) for tag in tags)
            for candidate in candidates:
                if not candidate:
                    continue
                if normalized and normalized not in candidate.lower():
                    continue
                if candidate in seen:
                    continue
                seen.add(candidate)
                suggestions.append(candidate)
                if len(suggestions) >= limit:
                    return suggestions
        return suggestions

    def create_media_asset(self, asset: MediaAsset) -> MediaAsset:
        self.db.add(asset)
        self.db.flush()
        return asset

    def get_media_asset(self, asset_id: int) -> MediaAsset | None:
        return self.db.get(MediaAsset, asset_id)

    def list_media_assets(self, asset_ids: list[int]) -> list[MediaAsset]:
        if not asset_ids:
            return []
        return self.db.query(MediaAsset).filter(MediaAsset.id.in_(asset_ids)).all()

    def add_product_image(self, product_id: int, url: str) -> ProductImage:
        image = ProductImage(product_id=product_id, url=url)
        self.db.add(image)
        self.db.flush()
        return image

    def list_product_images(self, product_id: int) -> list[ProductImage]:
        return self.db.query(ProductImage).filter_by(product_id=product_id).order_by(ProductImage.id.asc()).all()

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_category(self, category_id: int | None) -> Category | None:
        if category_id is None:
            return None
        return self.db.get(Category, category_id)

    def list_product_tasks(self, product_id: int) -> list[AuditTask]:
        return (
            self.db.query(AuditTask)
            .filter_by(entity_type="PRODUCT", entity_id=product_id)
            .order_by(AuditTask.created_at.desc())
            .all()
        )

    def list_product_reports(self, product_id: int) -> list[Report]:
        return (
            self.db.query(Report)
            .filter_by(target_type="PRODUCT", target_id=product_id)
            .order_by(Report.created_at.desc())
            .all()
        )
