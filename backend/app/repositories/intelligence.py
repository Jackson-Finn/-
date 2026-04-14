from sqlalchemy.orm import Session

from app.models.entities import AITaskLog, JobRunLog, RecommendationSnapshot


class IntelligenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_snapshot(self, snapshot: RecommendationSnapshot) -> RecommendationSnapshot:
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    def get_snapshot(self, user_id: int | None, scene: str) -> RecommendationSnapshot | None:
        return (
            self.db.query(RecommendationSnapshot)
            .filter_by(user_id=user_id, scene=scene)
            .order_by(RecommendationSnapshot.updated_at.desc())
            .first()
        )

    def log_job(self, job_name: str, status: str, details: dict) -> JobRunLog:
        job = JobRunLog(job_name=job_name, status=status, details=details)
        self.db.add(job)
        self.db.flush()
        return job

    def log_ai_task(self, task_name: str, prompt: str, result: dict, status: str = "COMPLETED") -> AITaskLog:
        log = AITaskLog(task_name=task_name, prompt=prompt, result=result, status=status)
        self.db.add(log)
        self.db.flush()
        return log
