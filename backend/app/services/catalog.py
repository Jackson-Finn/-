import json
from io import BytesIO

from fastapi import UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.core.enums import AuditDecision, AuditStatus, ProductStatus, TaskStatus
from app.core.errors import AppError
from app.core.events import DomainEvent, EventPublisher
from app.core.search import SearchIndexService
from app.core.storage import get_storage_service
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
        self.search = SearchIndexService(db)
        self.storage = get_storage_service()

    @staticmethod
    def _tags(product: Product) -> dict:
        return product.tags if isinstance(product.tags, dict) else {}

    @staticmethod
    def _mapping_tags(payload: dict | str | None) -> dict:
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    @staticmethod
    def _condition_label(tags: dict, title: str) -> str:
        explicit = str(tags.get("condition_label") or tags.get("condition") or "").strip()
        if explicit:
            return explicit
        for token in ("全新未拆", "99 新", "95 新", "近全新", "九成新", "八五新", "展示级"):
            if token.replace(" ", "") in title.replace(" ", ""):
                return token
        return "成色良好"

    @staticmethod
    def _detail_sections(product: Product, tags: dict) -> list[dict]:
        sections = tags.get("detail_sections")
        if isinstance(sections, list) and sections:
            return [
                {
                    "title": str(item.get("title") or "商品说明"),
                    "body": str(item.get("body") or "").strip(),
                }
                for item in sections
                if item and str(item.get("body") or "").strip()
            ]
        return [
            {"title": "商品说明", "body": product.description},
        ]

    def _specs(self, product: Product, seller, category, tags: dict) -> list[dict]:
        specs = tags.get("specs")
        if isinstance(specs, list) and specs:
            return [
                {
                    "label": str(item.get("label") or ""),
                    "value": str(item.get("value") or ""),
                }
                for item in specs
                if str(item.get("label") or "").strip() and str(item.get("value") or "").strip()
            ]

        return [
            {"label": "品类", "value": category.name if category else "闲置商品"},
            {"label": "成色", "value": self._condition_label(tags, product.title)},
            {"label": "库存", "value": f"{product.stock} 件"},
            {"label": "发货地", "value": tags.get("ship_from") or "待沟通"},
            {"label": "交易方式", "value": " / ".join(tags.get("deal_methods") or ["邮寄", "同城面交"])},
        ]

    @staticmethod
    def _delivery_options(tags: dict) -> list[dict]:
        options = tags.get("delivery_options")
        if isinstance(options, list) and options:
            return [
                {
                    "label": str(item.get("label") or ""),
                    "value": str(item.get("value") or ""),
                    "note": str(item.get("note") or "").strip() or None,
                }
                for item in options
                if str(item.get("label") or "").strip() and str(item.get("value") or "").strip()
            ]
        return [
            {"label": "发货方式", "value": "支持顺丰或同城面交", "note": "下单前建议先确认时间与验货方式。"},
        ]

    @staticmethod
    def _trust_snapshot(product: Product, tags: dict) -> dict:
        trust = tags.get("trust_snapshot")
        if isinstance(trust, dict) and trust:
            return {
                "audit_label": str(trust.get("audit_label") or "平台已审核"),
                "audit_note": str(trust.get("audit_note") or ""),
                "support_label": str(trust.get("support_label") or "平台协助"),
                "support_note": str(trust.get("support_note") or ""),
                "report_entry": str(trust.get("report_entry") or "可发起举报"),
                "dispute_entry": str(trust.get("dispute_entry") or "支持申诉"),
            }
        return {
            "audit_label": "平台已审核" if product.audit_status == AuditStatus.APPROVED.value else "审核处理中",
            "audit_note": "平台已校验基础信息与图片完整度，建议继续在会话中确认细节。",
            "support_label": "交易协助",
            "support_note": "保留举报、申诉与订单争议处理记录，便于售后复核。",
            "report_entry": "可在详情页直接举报异常信息",
            "dispute_entry": "如沟通与实物不符，可提交申诉材料",
        }

    def _risk_flags(self, product: Product, tags: dict) -> list[dict]:
        flags = tags.get("risk_flags")
        if isinstance(flags, list) and flags:
            return [
                {
                    "level": str(item.get("level") or "low").lower(),
                    "title": str(item.get("title") or ""),
                    "detail": str(item.get("detail") or ""),
                }
                for item in flags
                if str(item.get("title") or "").strip() and str(item.get("detail") or "").strip()
            ]

        default_level = "low" if product.audit_status == AuditStatus.APPROVED.value else "medium"
        return [
            {
                "level": default_level,
                "title": "建议先沟通验货细节",
                "detail": "二手商品存在个体差异，建议在下单前确认配件、瑕疵与交付方式。",
            }
        ]

    def serialize_product(self, product: Product) -> dict:
        images = [item.url for item in self.repo.list_product_images(product.id)]
        seller = self.repo.get_user(product.seller_id)
        category = self.repo.get_category(product.category_id)
        tags = self._tags(product)
        detail_sections = self._detail_sections(product, tags)
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
            "hero_summary": str(tags.get("hero_summary") or detail_sections[0]["body"][:88]),
            "condition_label": self._condition_label(tags, product.title),
            "detail_sections": detail_sections,
            "specs": self._specs(product, seller, category, tags),
            "delivery_options": self._delivery_options(tags),
            "trust_snapshot": self._trust_snapshot(product, tags),
            "risk_flags": self._risk_flags(product, tags),
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        }

    def serialize_product_summary(self, product: Product) -> dict:
        payload = self.serialize_product(product)
        return {
            "id": payload["id"],
            "seller_id": payload["seller_id"],
            "seller_name": payload["seller_name"],
            "category_name": payload["category_name"],
            "title": payload["title"],
            "price": payload["price"],
            "product_status": payload["product_status"],
            "audit_status": payload["audit_status"],
            "cover_image": payload["cover_image"],
            "hero_summary": payload["hero_summary"],
            "condition_label": payload["condition_label"],
            "updated_at": payload["updated_at"],
        }

    def serialize_product_summary_from_view(self, row: dict) -> dict:
        tags = self._mapping_tags(row.get("tags"))
        return {
            "id": row["id"],
            "seller_id": row["seller_id"],
            "seller_name": row.get("seller_name"),
            "category_name": row.get("category_name"),
            "title": row["title"],
            "price": row["price"],
            "product_status": row["product_status"],
            "audit_status": row["audit_status"],
            "cover_image": row.get("cover_image"),
            "hero_summary": row.get("hero_summary") or str(tags.get("hero_summary") or row.get("description") or "")[:88],
            "condition_label": row.get("condition_label") or self._condition_label(tags, row["title"]),
            "updated_at": row.get("updated_at"),
        }

    def list_products(self, keyword: str | None = None):
        if keyword:
            indexed_ids = self.search.search_product_ids(keyword)
            if indexed_ids is not None:
                return self.repo.list_products_by_ids(indexed_ids)
        return self.repo.search_products(keyword)

    def search_products(
        self,
        keyword: str | None = None,
        category: str | None = None,
        condition: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "newest",
        delivery_method: str | None = None,
    ) -> dict:
        products = self.repo.search_products_from_catalog_view(
            keyword=keyword,
            category=category,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
        )
        if condition:
            normalized = condition.replace(" ", "").lower()
            products = [
                product
                for product in products
                if normalized
                in (
                    product.get("condition_label")
                    or self._condition_label(self._mapping_tags(product.get("tags")), product["title"])
                ).replace(" ", "").lower()
            ]
        if delivery_method:
            normalized = delivery_method.strip().lower()
            products = [
                product
                for product in products
                if any(
                    normalized in str(option.get("value") or "").lower()
                    for option in self._delivery_options(self._mapping_tags(product.get("tags")))
                )
            ]

        serialized_items = [self.serialize_product_summary_from_view(product) for product in products]
        category_facets: dict[str, int] = {}
        condition_facets: dict[str, int] = {}
        for item in serialized_items:
            if item.get("category_name"):
                category_facets[item["category_name"]] = category_facets.get(item["category_name"], 0) + 1
            if item.get("condition_label"):
                condition_facets[item["condition_label"]] = condition_facets.get(item["condition_label"], 0) + 1
        return {
            "items": serialized_items,
            "total": len(serialized_items),
            "facets": {
                "categories": [{"label": name, "count": count} for name, count in sorted(category_facets.items())],
                "conditions": [{"label": name, "count": count} for name, count in sorted(condition_facets.items())],
            },
        }

    def list_my_products(self, seller_id: int):
        return self.repo.list_products_by_seller(seller_id)

    def suggest(self, keyword: str | None = None):
        if keyword:
            suggestions = self.search.suggest(keyword)
            if suggestions is not None:
                return suggestions
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
            tags=payload.tags or {"source": "manual"},
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
        self.gov_repo.log_operation(
            seller_id,
            "product.submit",
            {"product_id": product.id, "title": product.title, "audit_status": product.audit_status},
        )
        for asset in self.repo.list_media_assets(payload.asset_ids):
            if asset.owner_id != seller_id:
                raise AppError("You can only attach your own uploaded assets", status_code=403)
            if asset.metadata_json.get("stage") != "completed":
                raise AppError("Media asset is not ready to attach", status_code=409)
            preview_url = asset.metadata_json.get("variants", {}).get("preview", asset.url)
            self.repo.add_product_image(product.id, preview_url)
        self.db.commit()
        self.db.refresh(product)
        self.search.index_product(product)
        return product

    def update_product(self, product_id: int, seller_id: int, payload: ProductUpdateRequest):
        product = self.get_product(product_id)
        if product.seller_id != seller_id:
            raise AppError("Only the seller can update this product", status_code=403)
        for field, value in payload.model_dump(exclude_none=True).items():
            if field == "asset_ids":
                continue
            setattr(product, field, value)
        if payload.asset_ids is not None:
            for asset in self.repo.list_media_assets(payload.asset_ids):
                if asset.owner_id != seller_id:
                    raise AppError("You can only attach your own uploaded assets", status_code=403)
                if asset.metadata_json.get("stage") != "completed":
                    raise AppError("Media asset is not ready to attach", status_code=409)
                existing_urls = {item.url for item in self.repo.list_product_images(product.id)}
                preview_url = asset.metadata_json.get("variants", {}).get("preview", asset.url)
                if preview_url not in existing_urls:
                    self.repo.add_product_image(product.id, preview_url)
        self.publisher.publish(
            DomainEvent(
                event_type="ProductUpdated",
                aggregate_type="Product",
                aggregate_id=str(product.id),
                payload={"product_id": product.id},
            )
        )
        self.gov_repo.log_operation(
            seller_id,
            "product.update",
            {"product_id": product.id, "fields": list(payload.model_dump(exclude_none=True).keys())},
        )
        self.db.commit()
        self.db.refresh(product)
        self.search.index_product(product)
        return product

    def resubmit_product(self, product_id: int, seller_id: int, note: str | None = None):
        product = self.get_product(product_id)
        if product.seller_id != seller_id:
            raise AppError("Only the seller can resubmit this product", status_code=403)
        if product.audit_status != AuditStatus.CHANGES_REQUESTED.value:
            raise AppError("Only products returned for revision can be resubmitted", status_code=409)

        product.audit_status = AuditStatus.PENDING.value
        product.product_status = ProductStatus.DRAFT.value
        self.gov_repo.create_audit_task(
            AuditTask(
                task_type="PRODUCT_AUDIT",
                entity_type="PRODUCT",
                entity_id=product.id,
                status=TaskStatus.PENDING.value,
                payload={"title": product.title, "note": note or "卖家重新提交"},
            )
        )
        self.gov_repo.log_operation(
            seller_id,
            "product.resubmit",
            {"product_id": product.id, "note": note or "", "audit_status": product.audit_status},
        )
        self.publisher.publish(
            DomainEvent(
                event_type="ProductUpdated",
                aggregate_type="Product",
                aggregate_id=str(product.id),
                payload={"product_id": product.id, "event": "resubmit"},
            )
        )
        self.db.commit()
        self.db.refresh(product)
        self.search.index_product(product)
        return product

    def off_shelf(self, product_id: int, seller_id: int):
        product = self.get_product(product_id)
        if product.seller_id != seller_id:
            raise AppError("Only the seller can off-shelf this product", status_code=403)
        product.product_status = ProductStatus.OFF_SHELF.value
        self.gov_repo.log_operation(seller_id, "product.off_shelf", {"product_id": product.id, "source": "seller"})
        self.db.commit()
        self.search.index_product(product)
        return product

    def admin_off_shelf(self, product_id: int, actor_id: int, note: str | None = None):
        product = self.get_product(product_id)
        product.product_status = ProductStatus.OFF_SHELF.value
        self.gov_repo.log_operation(
            actor_id,
            "product.off_shelf",
            {"product_id": product.id, "source": "admin", "note": note or ""},
        )
        self.db.commit()
        self.search.index_product(product)
        return product

    def list_pending(self):
        return self.repo.list_pending_products()

    def audit_product(self, product_id: int, payload: AuditDecisionRequest, actor_id: int | None = None):
        product = self.get_product(product_id)
        if payload.decision == AuditDecision.APPROVE:
            product.audit_status = AuditStatus.APPROVED.value
            product.product_status = ProductStatus.ACTIVE.value
        elif payload.decision == AuditDecision.REJECT:
            product.audit_status = AuditStatus.REJECTED.value
            product.product_status = ProductStatus.BLOCKED.value
        else:
            product.audit_status = AuditStatus.CHANGES_REQUESTED.value
            product.product_status = ProductStatus.NEEDS_REVISION.value
        task = (
            self.db.query(AuditTask)
            .filter_by(entity_type="PRODUCT", entity_id=product_id)
            .order_by(AuditTask.created_at.desc())
            .first()
        )
        if task:
            task.status = TaskStatus.COMPLETED.value
            task.payload = {**task.payload, "note": payload.note or "", "decision": payload.decision.value}
        self.publisher.publish(
            DomainEvent(
                event_type="ProductAudited",
                aggregate_type="Product",
                aggregate_id=str(product.id),
                payload={"product_id": product.id, "decision": payload.decision.value},
            )
        )
        self.gov_repo.log_operation(
            actor_id,
            "product.audit",
            {
                "product_id": product.id,
                "decision": payload.decision.value,
                "note": payload.note or "",
                "audit_status": product.audit_status,
                "product_status": product.product_status,
            },
        )
        self.db.commit()
        self.search.index_product(product)
        return product

    def admin_product_context(self, product_id: int, actor_id: int | None = None) -> dict:
        product = self.get_product(product_id)
        if actor_id is not None:
            self.gov_repo.log_operation(actor_id, "product.view", {"product_id": product.id})
            self.db.commit()

        tasks = self.repo.list_product_tasks(product.id)
        reports = self.repo.list_product_reports(product.id)
        operations = [
            item
            for item in self.gov_repo.list_all_operation_logs()
            if item.details.get("product_id") == product.id
        ]
        return {
            "product": self.serialize_product(product),
            "tasks": tasks,
            "reports": reports,
            "operations": operations,
        }

    def upload_init(self, owner_id: int, filename: str, mime_type: str):
        object_key = self.storage.generate_object_key(owner_id, filename)
        asset = MediaAsset(
            owner_id=owner_id,
            object_key=object_key,
            mime_type=mime_type,
            url=self.storage.public_url(object_key),
            metadata_json={"stage": "init", "original_filename": filename},
        )
        self.repo.create_media_asset(asset)
        self.db.commit()
        return asset

    def upload_file(self, asset_id: int, owner_id: int, file: UploadFile):
        asset = self.repo.get_media_asset(asset_id)
        if not asset:
            raise AppError("Media asset not found", status_code=404)
        if asset.owner_id != owner_id:
            raise AppError("You can only upload to your own media asset", status_code=403)
        saved = self.storage.save_upload(file, asset.object_key)
        asset.url = saved["url"]
        asset.mime_type = file.content_type or asset.mime_type
        asset.metadata_json = {
            **asset.metadata_json,
            "stage": "uploaded",
            "sha256": saved["sha256"],
            "size": saved["size"],
            "storage": saved["storage_backend"],
        }
        self.db.commit()
        return asset

    def complete_upload(self, asset_id: int, owner_id: int, width: int | None = None, height: int | None = None):
        asset = self.repo.get_media_asset(asset_id)
        if not asset:
            raise AppError("Media asset not found", status_code=404)
        if asset.owner_id != owner_id:
            raise AppError("You can only complete your own media asset", status_code=403)

        original_bytes = self.storage.load_bytes(asset.object_key)
        thumb_key, compressed_key, variants_meta = self._generate_variants(
            asset.object_key,
            original_bytes,
            asset.mime_type,
        )
        asset.metadata_json = {
            **asset.metadata_json,
            "stage": "completed",
            "width": width or variants_meta["width"],
            "height": height or variants_meta["height"],
            "variants": {
                "original": asset.url,
                "preview": self.storage.public_url(thumb_key),
                "compressed": self.storage.public_url(compressed_key),
            },
            "variant_sizes": variants_meta["variant_sizes"],
        }
        self.db.commit()
        return asset

    def _generate_variants(self, object_key: str, raw_bytes: bytes, mime_type: str) -> tuple[str, str, dict]:
        try:
            image = Image.open(BytesIO(raw_bytes))
            image.load()
        except Exception as exc:
            raise AppError(f"Uploaded file is not a valid image: {exc}", status_code=400)

        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")

        width, height = image.size
        preview = image.copy()
        preview.thumbnail((480, 480))
        compressed = image.copy()
        compressed.thumbnail((1440, 1440))

        preview_buffer = BytesIO()
        compressed_buffer = BytesIO()
        preview.save(preview_buffer, format="WEBP", quality=82)
        compressed.save(compressed_buffer, format="WEBP", quality=74)

        base = object_key.rsplit(".", 1)[0]
        preview_key = f"{base}-preview.webp"
        compressed_key = f"{base}-compressed.webp"

        self.storage.save_bytes(preview_key, preview_buffer.getvalue(), "image/webp")
        self.storage.save_bytes(compressed_key, compressed_buffer.getvalue(), "image/webp")

        return preview_key, compressed_key, {
            "width": width,
            "height": height,
            "variant_sizes": {
                "preview": {"width": preview.width, "height": preview.height},
                "compressed": {"width": compressed.width, "height": compressed.height},
            },
        }
