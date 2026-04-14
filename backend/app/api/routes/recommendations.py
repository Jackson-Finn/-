from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_optional_current_user
from app.schemas.common import APIResponse
from app.services.intelligence import IntelligenceService


router = APIRouter()


@router.get("/home")
def home_recommendations(db: Session = Depends(get_db), current_user=Depends(get_optional_current_user)):
    payload = IntelligenceService(db).recommend_home(current_user.id if current_user else None)
    return APIResponse(data=payload)


@router.get("/products/{product_id}/related")
def related_recommendations(product_id: int, db: Session = Depends(get_db)):
    payload = IntelligenceService(db).recommend_related(product_id)
    return APIResponse(data=payload)
