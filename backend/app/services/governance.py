from sqlalchemy.orm import Session

from app.core.enums import AppealStatus, ReportStatus, TaskStatus
from app.core.errors import AppError
from app.core.events import DomainEvent, EventPublisher
from app.core.realtime import manager
from app.models.entities import Appeal, AuditTask, Report
from app.repositories.governance import GovernanceRepository
from app.schemas.governance import AppealCreateRequest, ReportCreateRequest, ReviewDecisionRequest, TaskDecisionRequest


class GovernanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GovernanceRepository(db)
        self.publisher = EventPublisher(db)

    def submit_report(self, reporter_id: int, payload: ReportCreateRequest):
        report = Report(
            reporter_id=reporter_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            reason=payload.reason,
        )
        self.repo.create_report(report)
        self.publisher.publish(
            DomainEvent(
                event_type="ReportSubmitted",
                aggregate_type="Report",
                aggregate_id=str(report.id),
                payload={"report_id": report.id},
            )
        )
        self.db.commit()
        self.db.refresh(report)
        return report

    def list_reports(self):
        return self.repo.list_reports()

    async def process_report(self, report_id: int, note: str, approved: bool, actor_id: int | None = None):
        report = self.repo.get_report(report_id)
        if not report:
            raise AppError("Report not found", status_code=404)
        if report.status == ReportStatus.PROCESSED.value:
            raise AppError("Report already processed", status_code=409)
        report.status = ReportStatus.PROCESSED.value
        report.decision = note
        task = (
            self.db.query(AuditTask)
            .filter_by(entity_type="REPORT", entity_id=report.id)
            .order_by(AuditTask.created_at.desc())
            .first()
        )
        if task:
            task.status = TaskStatus.COMPLETED.value
            task.payload = {**task.payload, "approved": approved, "note": note}
        self.repo.log_operation(
            actor_id,
            "report.process",
            {"report_id": report.id, "approved": approved, "note": note},
        )
        self.db.commit()
        await manager.push(report.reporter_id, "audit.task.updated", {"entity_type": "REPORT", "entity_id": report.id})
        return report

    def submit_appeal(self, applicant_id: int, payload: AppealCreateRequest):
        report = self.repo.get_report(payload.report_id)
        if not report or report.status != ReportStatus.PROCESSED.value:
            raise AppError("Appeal can only be submitted after report is processed", status_code=400)
        appeal = Appeal(report_id=payload.report_id, applicant_id=applicant_id, reason=payload.reason)
        self.repo.create_appeal(appeal)
        self.repo.create_audit_task(
            AuditTask(
                task_type="APPEAL_REVIEW",
                entity_type="APPEAL",
                entity_id=appeal.id,
                payload={"reason": payload.reason},
                status=TaskStatus.PENDING.value,
            )
        )
        self.repo.log_operation(applicant_id, "appeal.submit", {"appeal_id": appeal.id})
        self.publisher.publish(
            DomainEvent(
                event_type="AppealSubmitted",
                aggregate_type="Appeal",
                aggregate_id=str(appeal.id),
                payload={"appeal_id": appeal.id},
            )
        )
        self.db.commit()
        self.db.refresh(appeal)
        return appeal

    def list_appeals(self):
        return self.repo.list_appeals()

    async def review_appeal(self, appeal_id: int, payload: ReviewDecisionRequest, actor_id: int | None = None):
        appeal = self.repo.get_appeal(appeal_id)
        if not appeal:
            raise AppError("Appeal not found", status_code=404)
        if appeal.status != AppealStatus.PENDING.value:
            raise AppError("Appeal already reviewed", status_code=409)
        appeal.status = AppealStatus.APPROVED.value if payload.approved else AppealStatus.REJECTED.value
        appeal.decision = payload.note
        task = (
            self.db.query(AuditTask)
            .filter_by(entity_type="APPEAL", entity_id=appeal.id)
            .order_by(AuditTask.created_at.desc())
            .first()
        )
        if task:
            task.status = TaskStatus.COMPLETED.value
            task.payload = {**task.payload, "approved": payload.approved, "note": payload.note}
        self.repo.log_operation(
            actor_id,
            "appeal.review",
            {"appeal_id": appeal.id, "approved": payload.approved, "note": payload.note},
        )
        self.db.commit()
        await manager.push(appeal.applicant_id, "audit.task.updated", {"entity_type": "APPEAL", "entity_id": appeal.id})
        return appeal

    def list_audit_tasks(self):
        return self.repo.list_audit_tasks()

    def list_operation_logs(self, limit: int = 20):
        return self.repo.list_operation_logs(limit=limit)

    def report_context(self, report_id: int) -> dict:
        report = self.repo.get_report(report_id)
        if not report:
            raise AppError("Report not found", status_code=404)
        tasks = [
            task
            for task in self.repo.list_audit_tasks()
            if task.entity_type == "REPORT" and task.entity_id == report_id
        ]
        operations = [
            item
            for item in self.repo.list_all_operation_logs()
            if item.details.get("report_id") == report_id
        ]
        return {
            "report": report,
            "tasks": tasks,
            "operations": operations,
        }

    def appeal_context(self, appeal_id: int) -> dict:
        appeal = self.repo.get_appeal(appeal_id)
        if not appeal:
            raise AppError("Appeal not found", status_code=404)
        report = self.repo.get_report(appeal.report_id)
        tasks = [
            task
            for task in self.repo.list_audit_tasks()
            if task.entity_type == "APPEAL" and task.entity_id == appeal_id
        ]
        operations = [
            item
            for item in self.repo.list_all_operation_logs()
            if item.details.get("appeal_id") == appeal_id or item.details.get("report_id") == appeal.report_id
        ]
        return {
            "appeal": appeal,
            "report": report,
            "tasks": tasks,
            "operations": operations,
        }

    async def decide_task(self, task_id: int, payload: TaskDecisionRequest, actor_id: int | None = None):
        task = self.repo.get_audit_task(task_id)
        if not task:
            raise AppError("Audit task not found", status_code=404)
        task.status = TaskStatus.COMPLETED.value
        task.payload = {**task.payload, "approved": payload.approved, "note": payload.note}
        self.repo.log_operation(
            actor_id,
            "audit.task.decide",
            {"task_id": task.id, "approved": payload.approved, "note": payload.note},
        )
        self.db.commit()
        return task
