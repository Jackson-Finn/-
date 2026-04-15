from __future__ import annotations

from urllib.parse import urlparse

from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Product
from app.repositories.catalog import CatalogRepository


class SearchIndexService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CatalogRepository(db)
        self.settings = get_settings()
        parsed = urlparse(self.settings.opensearch_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self.client = OpenSearch(
            hosts=[
                {
                    "host": host,
                    "port": port,
                    "scheme": parsed.scheme or "http",
                }
            ],
            timeout=1,
        )

    def _index_body(self) -> dict:
        return {
            "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}},
            "mappings": {
                "properties": {
                    "product_id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "search_as_you_type"},
                        },
                    },
                    "description": {"type": "text"},
                    "price": {"type": "float"},
                    "seller_id": {"type": "integer"},
                    "category_id": {"type": "integer"},
                    "product_status": {"type": "keyword"},
                    "audit_status": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "cover_image": {"type": "keyword", "index": False},
                    "images": {"type": "keyword", "index": False},
                    "updated_at": {"type": "date"},
                    "created_at": {"type": "date"},
                    "suggest": {"type": "completion"},
                }
            },
        }

    def _serialize_product(self, product: Product) -> dict:
        images = [item.url for item in self.repo.list_product_images(product.id)]
        tags = product.tags.get("keywords", []) if isinstance(product.tags, dict) else []
        return {
            "product_id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "seller_id": product.seller_id,
            "category_id": product.category_id,
            "product_status": product.product_status,
            "audit_status": product.audit_status,
            "tags": [str(tag) for tag in tags],
            "cover_image": images[0] if images else None,
            "images": images,
            "updated_at": product.updated_at.isoformat(),
            "created_at": product.created_at.isoformat(),
            "suggest": {"input": [product.title, *[str(tag) for tag in tags]]},
        }

    def ensure_index(self) -> bool:
        try:
            if not self.client.indices.exists(index=self.settings.opensearch_index):
                self.client.indices.create(index=self.settings.opensearch_index, body=self._index_body())
            return True
        except OpenSearchException:
            return False
        except Exception:
            return False

    def index_product(self, product: Product) -> dict:
        if not self.ensure_index():
            return {"mode": "database-fallback", "indexed": False}
        try:
            self.client.index(
                index=self.settings.opensearch_index,
                id=product.id,
                body=self._serialize_product(product),
                refresh=True,
            )
            return {"mode": "opensearch", "indexed": True}
        except Exception:
            return {"mode": "database-fallback", "indexed": False}

    def delete_product(self, product_id: int) -> dict:
        if not self.ensure_index():
            return {"mode": "database-fallback", "deleted": False}
        try:
            self.client.delete(
                index=self.settings.opensearch_index,
                id=product_id,
                ignore=[404],
                refresh=True,
            )
            return {"mode": "opensearch", "deleted": True}
        except Exception:
            return {"mode": "database-fallback", "deleted": False}

    def search_product_ids(self, keyword: str, limit: int = 24) -> list[int] | None:
        if not keyword.strip() or not self.ensure_index():
            return None
        body = {
            "size": limit,
            "_source": ["product_id"],
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": ["title^4", "title.suggest^3", "description", "tags^2"],
                                "type": "best_fields",
                            }
                        },
                        {"match_phrase_prefix": {"title.suggest": {"query": keyword, "boost": 4}}},
                    ],
                    "minimum_should_match": 1,
                }
            },
        }
        try:
            response = self.client.search(index=self.settings.opensearch_index, body=body)
            return [int(item["_source"]["product_id"]) for item in response.get("hits", {}).get("hits", [])]
        except Exception:
            return None

    def suggest(self, keyword: str, limit: int = 10) -> list[str] | None:
        if not keyword.strip() or not self.ensure_index():
            return None
        body = {
            "suggest": {
                "product-suggest": {
                    "prefix": keyword,
                    "completion": {
                        "field": "suggest",
                        "skip_duplicates": True,
                        "size": limit,
                    },
                }
            }
        }
        try:
            response = self.client.search(index=self.settings.opensearch_index, body=body)
            options = response.get("suggest", {}).get("product-suggest", [{}])[0].get("options", [])
            suggestions: list[str] = []
            seen: set[str] = set()
            for option in options:
                text = option.get("text")
                if text and text not in seen:
                    seen.add(text)
                    suggestions.append(text)
            return suggestions
        except Exception:
            return None

    def reindex_all(self) -> dict:
        products = self.repo.list_products()
        if not self.ensure_index():
            return {
                "status": "completed",
                "mode": "database-fallback",
                "indexed_count": 0,
                "total_products": len(products),
            }

    def health(self) -> dict:
        try:
            available = self.ensure_index()
            if not available:
                return {"mode": "database-fallback", "available": False, "index": self.settings.opensearch_index}
            stats = self.client.indices.stats(index=self.settings.opensearch_index)
            doc_count = (
                stats.get("_all", {})
                .get("primaries", {})
                .get("docs", {})
                .get("count", 0)
            )
            return {
                "mode": "opensearch",
                "available": True,
                "index": self.settings.opensearch_index,
                "document_count": doc_count,
            }
        except Exception:
            return {"mode": "database-fallback", "available": False, "index": self.settings.opensearch_index}
        try:
            self.client.indices.delete(index=self.settings.opensearch_index, ignore=[404])
            self.client.indices.create(index=self.settings.opensearch_index, body=self._index_body())
            for product in products:
                self.client.index(
                    index=self.settings.opensearch_index,
                    id=product.id,
                    body=self._serialize_product(product),
                )
            self.client.indices.refresh(index=self.settings.opensearch_index)
            return {
                "status": "completed",
                "mode": "opensearch",
                "indexed_count": len(products),
                "total_products": len(products),
                "index": self.settings.opensearch_index,
            }
        except Exception:
            return {
                "status": "completed",
                "mode": "database-fallback",
                "indexed_count": 0,
                "total_products": len(products),
            }
