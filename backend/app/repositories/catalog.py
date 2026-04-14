from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.entities import MediaAsset, Product, ProductImage


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

    def list_pending_products(self) -> list[Product]:
        return self.db.query(Product).filter_by(audit_status="PENDING").order_by(Product.created_at.asc()).all()

    def search_products(self, keyword: str | None = None) -> list[Product]:
        query = self.db.query(Product)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(Product.title.ilike(like), Product.description.ilike(like)))
        return query.order_by(Product.created_at.desc()).all()

    def search_suggestions(self, keyword: str | None = None, limit: int = 10) -> list[str]:
        normalized = (keyword or "").strip().lower()
        products = self.db.query(Product).order_by(Product.created_at.desc()).all()
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

    def add_product_image(self, product_id: int, url: str) -> ProductImage:
        image = ProductImage(product_id=product_id, url=url)
        self.db.add(image)
        self.db.flush()
        return image
