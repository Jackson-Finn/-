from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.governance import ReportCreateRequest, ReportResponse
from app.services.governance import GovernanceService


router = APIRouter()


@router.post("")
def submit_report(payload: ReportCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    report = GovernanceService(db).submit_report(current_user.id, payload)
    return APIResponse(data=ReportResponse.model_validate(report))

