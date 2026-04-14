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
    review = TradeService(db).create_review(current_user.id, payload)
    return APIResponse(data={"id": review.id, "product_id": review.product_id, "rating": review.rating, "content": review.content})


@router.get("/products/{product_id}")
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    reviews = TradeService(db).list_reviews(product_id)
    return APIResponse(
        data=[
            {"id": review.id, "user_id": review.user_id, "rating": review.rating, "content": review.content}
            for review in reviews
        ]
    )

