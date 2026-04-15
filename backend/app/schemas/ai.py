from pydantic import BaseModel


class ProductDraftRequest(BaseModel):
    keywords: list[str]
    category: str | None = None


class ModerationPreviewRequest(BaseModel):
    title: str
    description: str


class ChatSummaryRequest(BaseModel):
    session_id: int


class ListingCopilotRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    keywords: list[str] = []
    condition: str | None = None
    selling_points: list[str] = []
    images: list[str] = []


class SearchAssistRequest(BaseModel):
    query: str


class PurchaseInsightsRequest(BaseModel):
    product_id: int


class ChatCopilotRequest(BaseModel):
    session_id: int
