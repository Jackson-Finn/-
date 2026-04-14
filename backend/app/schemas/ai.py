from pydantic import BaseModel


class ProductDraftRequest(BaseModel):
    keywords: list[str]
    category: str | None = None


class ModerationPreviewRequest(BaseModel):
    title: str
    description: str


class ChatSummaryRequest(BaseModel):
    session_id: int

