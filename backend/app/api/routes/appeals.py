from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.governance import AppealCreateRequest
from app.services.governance import GovernanceService


router = APIRouter()


@router.post("")
def submit_appeal(payload: AppealCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    appeal = GovernanceService(db).submit_appeal(current_user.id, payload)
    return APIResponse(data={"id": appeal.id, "report_id": appeal.report_id, "status": appeal.status})

