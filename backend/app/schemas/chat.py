from pydantic import BaseModel

from app.schemas.common import TimestampSchema


class ChatSessionCreateRequest(BaseModel):
    product_id: int | None = None
    seller_id: int


class ChatMessageCreateRequest(BaseModel):
    content: str
    request_id: str | None = None


class ChatSessionResponse(TimestampSchema):
    id: int
    product_id: int | None
    buyer_id: int
    seller_id: int


class ChatMessageResponse(TimestampSchema):
    id: int
    session_id: int
    sender_id: int
    content: str
    status: str

