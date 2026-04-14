from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.order import OrderCreateRequest, OrderResponse
from app.services.trade import TradeService


router = APIRouter()


@router.post("")
def create_order(payload: OrderCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = TradeService(db).create_order(current_user.id, payload)
    return APIResponse(data=OrderResponse.model_validate(order))


@router.get("")
def list_orders(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    orders = TradeService(db).list_orders(current_user.id)
    return APIResponse(data=[OrderResponse.model_validate(order) for order in orders])


@router.get("/{order_id}")
def get_order(order_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = TradeService(db).get_order(order_id, current_user.id)
    return APIResponse(data=OrderResponse.model_validate(order))


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = TradeService(db).cancel_order(order_id, current_user.id)
    return APIResponse(data=OrderResponse.model_validate(order))


@router.post("/{order_id}/confirm")
def confirm_order(order_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = TradeService(db).confirm_order(order_id, current_user.id)
    return APIResponse(data=OrderResponse.model_validate(order))

