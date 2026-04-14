from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


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


class ReviewCreateRequest(BaseModel):
    order_id: int
    rating: int = Field(ge=1, le=5)
    content: str

