from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.services.interaction import InteractionService


router = APIRouter()


@router.get("")
def list_notifications(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = InteractionService(db).list_notifications(current_user.id)
    return APIResponse(data=notifications)


@router.post("/{notification_id}/read")
async def mark_read(notification_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    read = await InteractionService(db).mark_notification_read(current_user.id, notification_id)
    return APIResponse(data={"id": read.id, "notification_id": read.notification_id})
