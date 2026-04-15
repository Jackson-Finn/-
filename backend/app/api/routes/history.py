from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.services.trade import TradeService


router = APIRouter()


@router.post("/products/{product_id}/view")
def capture_history(product_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    history = TradeService(db).capture_history(current_user.id, product_id)
    return APIResponse(data={"id": history.id, "product_id": history.product_id})


@router.get("/recent")
def recent_history(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    entries = TradeService(db).recent_history(current_user.id)
    return APIResponse(data=entries)
