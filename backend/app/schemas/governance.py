from pydantic import BaseModel

from app.schemas.common import TimestampSchema


class ReportCreateRequest(BaseModel):
    target_type: str
    target_id: int
    reason: str


class AppealCreateRequest(BaseModel):
    report_id: int
    reason: str


class ReviewDecisionRequest(BaseModel):
    approved: bool
    note: str


class TaskDecisionRequest(BaseModel):
    approved: bool
    note: str


class ReportResponse(TimestampSchema):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: str
    status: str
    decision: str | None

