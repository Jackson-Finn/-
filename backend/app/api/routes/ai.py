from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai import (
    ChatCopilotRequest,
    ChatSummaryRequest,
    ListingCopilotRequest,
    ModerationPreviewRequest,
    ProductDraftRequest,
    PurchaseInsightsRequest,
    SearchAssistRequest,
)
from app.schemas.common import APIResponse
from app.services.intelligence import IntelligenceService


router = APIRouter()


@router.post("/products/draft")
def product_draft(payload: ProductDraftRequest, db: Session = Depends(get_db)):
    result = IntelligenceService(db).ai_product_draft(payload.keywords, payload.category)
    return APIResponse(data=result)


@router.post("/moderation/preview")
def moderation_preview(payload: ModerationPreviewRequest, db: Session = Depends(get_db)):
    result = IntelligenceService(db).ai_moderation_preview(payload.title, payload.description)
    return APIResponse(data=result)


@router.post("/chat/summary")
def chat_summary(payload: ChatSummaryRequest, db: Session = Depends(get_db)):
    result = IntelligenceService(db).ai_chat_summary(payload.session_id)
    return APIResponse(data=result)


@router.post("/listings/copilot")
def listing_copilot(payload: ListingCopilotRequest, db: Session = Depends(get_db)):
    result = IntelligenceService(db).ai_listing_copilot(payload.model_dump())
    return APIResponse(data=result)


@router.post("/search/assist")
def search_assist(payload: SearchAssistRequest, db: Session = Depends(get_db)):
    result = IntelligenceService(db).ai_search_assist(payload.query)
    return APIResponse(data=result)


@router.post("/purchase/insights")
def purchase_insights(payload: PurchaseInsightsRequest, db: Session = Depends(get_db)):
    result = IntelligenceService(db).ai_purchase_insights(payload.product_id)
    return APIResponse(data=result)


@router.post("/chat/copilot")
def chat_copilot(payload: ChatCopilotRequest, db: Session = Depends(get_db)):
    result = IntelligenceService(db).ai_chat_copilot(payload.session_id)
    return APIResponse(data=result)
