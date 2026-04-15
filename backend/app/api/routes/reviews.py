from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.order import ReviewCreateRequest
from app.services.trade import TradeService


router = APIRouter()


@router.post("")
def create_review(payload: ReviewCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = TradeService(db)
    reviews = service.create_review(current_user.id, payload)
    return APIResponse(data=[service.serialize_review(review) for review in reviews])


@router.get("/products/{product_id}")
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    service = TradeService(db)
    reviews = service.list_reviews(product_id)
    return APIResponse(data=[service.serialize_review(review) for review in reviews])


@router.get("/sellers/{seller_id}")
def list_seller_reviews(seller_id: int, db: Session = Depends(get_db)):
    service = TradeService(db)
    reviews = service.list_seller_reviews(seller_id)
    return APIResponse(data=[service.serialize_review(review) for review in reviews])
