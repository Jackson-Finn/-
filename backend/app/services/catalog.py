from sqlalchemy.orm import Session

from app.core.enums import AuditStatus, ProductStatus, TaskStatus
from app.core.errors import AppError
from app.core.events import DomainEvent, EventPublisher
from app.models.entities import AuditTask, MediaAsset, Product
from app.repositories.catalog import CatalogRepository
from app.repositories.governance import GovernanceRepository
from app.schemas.product import AuditDecisionRequest, ProductCreateRequest, ProductUpdateRequest


class CatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CatalogRepository(db)
        self.gov_repo = GovernanceRepository(db)
        self.publisher = EventPublisher(db)

    def list_products(self, keyword: str | None = None):
        return self.repo.search_products(keyword)

    def suggest(self, keyword: str | None = None):
        return self.repo.search_suggestions(keyword)

    def get_product(self, product_id: int):
        product = self.repo.get_product(product_id)
        if not product:
            raise AppError("Product not found", status_code=404)
        return product

    def create_product(self, seller_id: int, payload: ProductCreateRequest):
        product = Product(
            seller_id=seller_id,
            category_id=payload.category_id,
            title=payload.title,
            description=payload.description,
            price=payload.price,
            stock=payload.stock,
            product_status=ProductStatus.DRAFT.value,
            audit_status=AuditStatus.PENDING.value,
            tags={"source": "manual"},
        )
        self.repo.create_product(product)
        self.gov_repo.create_audit_task(
            AuditTask(
                task_type="PRODUCT_AUDIT",
                entity_type="PRODUCT",
                entity_id=product.id,
                status=TaskStatus.PENDING.value,
                payload={"title": product.title},
            )
        )
        self.publisher.publish(
            DomainEvent(
                event_type="ProductCreated",
                aggregate_type="Product",
                aggregate_id=str(product.id),
                payload={"product_id": product.id, "title": product.title},
            )
        )
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product_id: int, seller_id: int, payload: ProductUpdateRequest):
        product = self.get_product(product_id)
        if product.seller_id != seller_id:
            raise AppError("Only the seller can update this product", status_code=403)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(product, field, value)
        self.publisher.publish(
            DomainEvent(
                event_type="ProductUpdated",
                aggregate_type="Product",
                aggregate_id=str(product.id),
                payload={"product_id": product.id},
            )
        )
        self.db.commit()
        self.db.refresh(product)
        return product

    def off_shelf(self, product_id: int, seller_id: int):
        product = self.get_product(product_id)
        if product.seller_id != seller_id:
            raise AppError("Only the seller can off-shelf this product", status_code=403)
        product.product_status = ProductStatus.OFF_SHELF.value
        self.db.commit()
        return product

    def list_pending(self):
        return self.repo.list_pending_products()

    def audit_product(self, product_id: int, payload: AuditDecisionRequest):
        product = self.get_product(product_id)
        product.audit_status = AuditStatus.APPROVED.value if payload.approved else AuditStatus.REJECTED.value
        product.product_status = ProductStatus.ACTIVE.value if payload.approved else ProductStatus.BLOCKED.value
        task = (
            self.db.query(AuditTask)
            .filter_by(entity_type="PRODUCT", entity_id=product_id)
            .order_by(AuditTask.created_at.desc())
            .first()
        )
        if task:
            task.status = TaskStatus.COMPLETED.value
            task.payload = {**task.payload, "note": payload.note or "", "approved": payload.approved}
        self.publisher.publish(
            DomainEvent(
                event_type="ProductAudited",
                aggregate_type="Product",
                aggregate_id=str(product.id),
                payload={"product_id": product.id, "approved": payload.approved},
            )
        )
        self.db.commit()
        return product

    def upload_init(self, owner_id: int, filename: str, mime_type: str):
        object_key = f"{owner_id}/{filename}"
        asset = MediaAsset(
            owner_id=owner_id,
            object_key=object_key,
            mime_type=mime_type,
            url=f"/media/{object_key}",
            metadata_json={"stage": "init"},
        )
        self.repo.create_media_asset(asset)
        self.db.commit()
        return asset

    def complete_upload(self, asset_id: int, width: int | None = None, height: int | None = None):
        asset = self.db.get(MediaAsset, asset_id)
        if not asset:
            raise AppError("Media asset not found", status_code=404)
        asset.metadata_json = {**asset.metadata_json, "stage": "completed", "width": width, "height": height}
        self.db.commit()
        return asset
