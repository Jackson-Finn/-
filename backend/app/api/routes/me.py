from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.enums import OrderStatus
from app.models.entities import BrowseHistory, Favorite, NotificationRead, Notification, Order
from app.repositories.interaction import InteractionRepository
from app.schemas.common import APIResponse


router = APIRouter()


@router.get("/workspace")
def workspace_summary(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    interaction_repo = InteractionRepository(db)
    unread_messages = 0
    for session in interaction_repo.list_sessions(current_user.id):
        unread_messages += interaction_repo.count_unread_notifications_by_target(current_user.id, f"/messages?sessionId={session.id}")
    total_notifications = db.query(Notification).filter_by(user_id=current_user.id).count()
    read_notifications = db.query(NotificationRead).filter_by(user_id=current_user.id).count()
    active_orders = (
        db.query(Order)
        .filter(
            Order.buyer_id == current_user.id,
            Order.status == OrderStatus.CREATED.value,
        )
        .count()
    )
    return APIResponse(
        data={
            "unread_messages": unread_messages,
            "unread_notifications": max(total_notifications - read_notifications, 0),
            "favorites": db.query(Favorite).filter_by(user_id=current_user.id).count(),
            "recent_history": db.query(BrowseHistory).filter_by(user_id=current_user.id).count(),
            "active_orders": active_orders,
        }
    )
