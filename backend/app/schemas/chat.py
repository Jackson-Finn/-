from pydantic import BaseModel

from app.schemas.common import TimestampSchema
from app.schemas.product import ProductSummaryResponse


class ChatSessionCreateRequest(BaseModel):
    product_id: int | None = None
    seller_id: int


class ChatMessageCreateRequest(BaseModel):
    content: str
    request_id: str | None = None


class PresenceStatusRequest(BaseModel):
    presence_status: str


class ChatSessionResponse(TimestampSchema):
    id: int
    product_id: int | None
    buyer_id: int
    seller_id: int
    product_summary: ProductSummaryResponse | None = None
    counterpart_name: str | None = None
    counterpart_presence_status: str = "OFFLINE"
    last_message_preview: str = ""
    last_message_at: str | None = None
    unread_count: int = 0


class ChatMessageResponse(TimestampSchema):
    id: int
    session_id: int
    sender_id: int
    sender_name: str | None = None
    content: str
    status: str
