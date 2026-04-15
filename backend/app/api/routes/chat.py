from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.chat import ChatMessageCreateRequest, ChatSessionCreateRequest, PresenceStatusRequest
from app.schemas.common import APIResponse
from app.services.interaction import InteractionService


router = APIRouter()


@router.post("/sessions")
def create_session(payload: ChatSessionCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = InteractionService(db)
    session = service.create_session(current_user.id, payload)
    return APIResponse(data=service.serialize_session(session, current_user.id))


@router.get("/sessions")
def list_sessions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = InteractionService(db).list_sessions(current_user.id)
    return APIResponse(data=sessions)


@router.get("/sessions/{session_id}/messages")
def list_messages(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    messages = InteractionService(db).list_messages(session_id, current_user.id)
    return APIResponse(data=messages)


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    payload: ChatMessageCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = await InteractionService(db).send_message(session_id, current_user.id, payload.content)
    return APIResponse(data=message)


@router.put("/presence")
def update_presence(payload: PresenceStatusRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    data = InteractionService(db).update_presence(current_user.id, payload.presence_status)
    return APIResponse(data=data)
