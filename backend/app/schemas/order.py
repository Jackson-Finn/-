from pydantic import BaseModel, Field, model_validator

from app.schemas.common import TimestampSchema
from app.schemas.product import ProductSummaryResponse


class OrderCreateRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    request_id: str | None = None


class OrderResponse(TimestampSchema):
    id: int
    buyer_id: int
    seller_id: int
    product_id: int
    total_amount: float
    status: str
    product_summary: ProductSummaryResponse | None = None
    is_buyer: bool = False
    is_seller: bool = False
    can_confirm: bool = False
    can_review_product: bool = False
    can_review_seller: bool = False
    product_review: "ReviewSnapshotResponse | None" = None
    seller_review: "ReviewSnapshotResponse | None" = None
    next_actions: list[str] = []


class ReviewSnapshotResponse(TimestampSchema):
    id: int
    order_id: int
    product_id: int
    seller_id: int | None = None
    user_id: int
    review_type: str
    rating: int
    content: str


class ReviewContentInput(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str


class ReviewCreateRequest(BaseModel):
    order_id: int
    rating: int | None = Field(default=None, ge=1, le=5)
    content: str | None = None
    product_review: ReviewContentInput | None = None
    seller_review: ReviewContentInput | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_payload(cls, value):
        if not isinstance(value, dict):
            return value
        if value.get("product_review") or value.get("seller_review"):
            return value
        rating = value.get("rating")
        content = value.get("content")
        if rating is not None and content:
            value = dict(value)
            value["product_review"] = {"rating": rating, "content": content}
        return value

    @model_validator(mode="after")
    def validate_reviews(self):
        if not self.product_review and not self.seller_review:
            raise ValueError("At least one review payload is required")
        return self
