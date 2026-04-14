from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.chat import ChatMessageCreateRequest, ChatMessageResponse, ChatSessionCreateRequest, ChatSessionResponse
from app.schemas.common import APIResponse
from app.services.interaction import InteractionService


router = APIRouter()


@router.post("/sessions")
def create_session(payload: ChatSessionCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    session = InteractionService(db).create_session(current_user.id, payload)
    return APIResponse(data=ChatSessionResponse.model_validate(session))


@router.get("/sessions")
def list_sessions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = InteractionService(db).list_sessions(current_user.id)
    return APIResponse(data=[ChatSessionResponse.model_validate(session) for session in sessions])


@router.get("/sessions/{session_id}/messages")
def list_messages(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    messages = InteractionService(db).list_messages(session_id, current_user.id)
    return APIResponse(data=[ChatMessageResponse.model_validate(message) for message in messages])


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    payload: ChatMessageCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = await InteractionService(db).send_message(session_id, current_user.id, payload.content)
    return APIResponse(data=ChatMessageResponse.model_validate(message))

