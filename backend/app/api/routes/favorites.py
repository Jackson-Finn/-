from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.services.trade import TradeService


router = APIRouter()


@router.post("/{product_id}")
def add_favorite(product_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    TradeService(db).add_favorite(current_user.id, product_id)
    return APIResponse(message="Favorite added")


@router.delete("/{product_id}")
def remove_favorite(product_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    TradeService(db).remove_favorite(current_user.id, product_id)
    return APIResponse(message="Favorite removed")


@router.get("")
def list_favorites(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    favorites = TradeService(db).list_favorites(current_user.id)
    return APIResponse(data=[{"id": favorite.id, "product_id": favorite.product_id} for favorite in favorites])

