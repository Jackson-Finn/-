from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class SellerTrustHighlight(BaseSchema):
    title: str
    detail: str


class SellerProfileResponse(TimestampSchema):
    id: int
    display_name: str
    email_masked: str
    avatar_url: str
    headline: str
    bio: str
    city: str
    response_rate: int
    response_time_minutes: int
    response_summary: str
    presence_status: str
    active_products: int
    total_products: int
    completed_orders: int
    average_rating: float
    review_count: int
    verification_badges: list[str] = Field(default_factory=list)
    preferred_deal_methods: list[str] = Field(default_factory=list)
    trust_score: int
    on_sale_count: int
    trust_highlights: list[SellerTrustHighlight] = Field(default_factory=list)


class SellerProductSummary(BaseSchema):
    id: int
    seller_id: int
    seller_name: str | None = None
    category_id: int | None = None
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
    condition_label: str = ""
    hero_summary: str = ""
    updated_at: datetime | None = None
