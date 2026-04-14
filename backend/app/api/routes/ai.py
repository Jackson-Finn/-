from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai import ChatSummaryRequest, ModerationPreviewRequest, ProductDraftRequest
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

