from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.core.enums import AuditDecision
from app.schemas.common import BaseSchema, TimestampSchema


class ProductDetailSection(BaseSchema):
    title: str
    body: str


class ProductSpecItem(BaseSchema):
    label: str
    value: str


class DeliveryOptionItem(BaseSchema):
    label: str
    value: str
    note: str | None = None


class ProductTrustSnapshot(BaseSchema):
    audit_label: str
    audit_note: str
    support_label: str
    support_note: str
    report_entry: str
    dispute_entry: str


class ProductRiskFlag(BaseSchema):
    level: str
    title: str
    detail: str


class ProductCreateRequest(BaseModel):
    title: str
    description: str
    price: float
    category_id: int | None = None
    stock: int = 1
    asset_ids: list[int] = Field(default_factory=list)
    tags: dict = Field(default_factory=dict)


class ProductUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = None
    category_id: int | None = None
    stock: int | None = None
    asset_ids: list[int] | None = None
    tags: dict | None = None


class ProductResponse(TimestampSchema):
    id: int
    seller_id: int
    seller_name: str | None = None
    category_id: int | None
    category_name: str | None = None
    title: str
    description: str
    price: float
    stock: int
    product_status: str
    audit_status: str
    tags: dict = Field(default_factory=dict)
    images: list[str] = Field(default_factory=list)
    cover_image: str | None = None
    hero_summary: str = ""
    condition_label: str = ""
    detail_sections: list[ProductDetailSection] = Field(default_factory=list)
    specs: list[ProductSpecItem] = Field(default_factory=list)
    delivery_options: list[DeliveryOptionItem] = Field(default_factory=list)
    trust_snapshot: ProductTrustSnapshot | None = None
    risk_flags: list[ProductRiskFlag] = Field(default_factory=list)


class ProductSummaryResponse(BaseSchema):
    id: int
    seller_id: int
    seller_name: str | None = None
    category_name: str | None = None
    title: str
    price: float
    product_status: str
    audit_status: str
    cover_image: str | None = None
    hero_summary: str = ""
    condition_label: str = ""
    updated_at: datetime | None = None


class AuditDecisionRequest(BaseModel):
    decision: AuditDecision | None = None
    approved: bool | None = None
    note: str | None = None

    @model_validator(mode="after")
    def normalize_decision(self):
        if self.decision is None and self.approved is not None:
            self.decision = AuditDecision.APPROVE if self.approved else AuditDecision.REJECT
        if self.decision is None:
            raise ValueError("decision is required")
        return self


class SearchSuggestResponse(BaseSchema):
    suggestions: list[str]
