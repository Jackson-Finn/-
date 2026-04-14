from sqlalchemy.orm import Session

from app.models.entities import Appeal, AuditTask, OperationLog, Report


class GovernanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, report: Report) -> Report:
        self.db.add(report)
        self.db.flush()
        return report

    def get_report(self, report_id: int) -> Report | None:
        return self.db.get(Report, report_id)

    def list_reports(self) -> list[Report]:
        return self.db.query(Report).order_by(Report.created_at.desc()).all()

    def create_appeal(self, appeal: Appeal) -> Appeal:
        self.db.add(appeal)
        self.db.flush()
        return appeal

    def get_appeal(self, appeal_id: int) -> Appeal | None:
        return self.db.get(Appeal, appeal_id)

    def list_appeals(self) -> list[Appeal]:
        return self.db.query(Appeal).order_by(Appeal.created_at.desc()).all()

    def create_audit_task(self, task: AuditTask) -> AuditTask:
        self.db.add(task)
        self.db.flush()
        return task

    def get_audit_task(self, task_id: int) -> AuditTask | None:
        return self.db.get(AuditTask, task_id)

    def list_audit_tasks(self) -> list[AuditTask]:
        return self.db.query(AuditTask).order_by(AuditTask.created_at.desc()).all()

    def list_operation_logs(self, limit: int = 20) -> list[OperationLog]:
        return self.db.query(OperationLog).order_by(OperationLog.created_at.desc()).limit(limit).all()

    def list_all_operation_logs(self) -> list[OperationLog]:
        return self.db.query(OperationLog).order_by(OperationLog.created_at.desc()).all()

    def log_operation(self, actor_id: int | None, action: str, details: dict) -> None:
        self.db.add(OperationLog(actor_id=actor_id, action=action, details=details))
