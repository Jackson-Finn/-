from pydantic import BaseModel

from app.schemas.common import BaseSchema, TimestampSchema


class ProductCreateRequest(BaseModel):
    title: str
    description: str
    price: float
    category_id: int | None = None
    stock: int = 1


class ProductUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = None
    category_id: int | None = None
    stock: int | None = None


class ProductResponse(TimestampSchema):
    id: int
    seller_id: int
    category_id: int | None
    title: str
    description: str
    price: float
    stock: int
    product_status: str
    audit_status: str
    tags: dict


class AuditDecisionRequest(BaseModel):
    approved: bool
    note: str | None = None


class SearchSuggestResponse(BaseSchema):
    suggestions: list[str]

