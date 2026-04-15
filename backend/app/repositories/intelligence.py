from sqlalchemy.orm import Session

from app.models.entities import AITaskLog, JobRunLog, RecommendationMaterial, RecommendationSnapshot


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

    def list_materials(self, limit: int = 50) -> list[RecommendationMaterial]:
        return (
            self.db.query(RecommendationMaterial)
            .order_by(RecommendationMaterial.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_snapshots(self, limit: int = 20) -> list[RecommendationSnapshot]:
        return (
            self.db.query(RecommendationSnapshot)
            .order_by(RecommendationSnapshot.updated_at.desc())
            .limit(limit)
            .all()
        )

    def list_jobs(self, limit: int = 20) -> list[JobRunLog]:
        return self.db.query(JobRunLog).order_by(JobRunLog.created_at.desc()).limit(limit).all()

    def list_ai_tasks(self, limit: int = 20) -> list[AITaskLog]:
        return self.db.query(AITaskLog).order_by(AITaskLog.created_at.desc()).limit(limit).all()

    def log_job(self, job_name: str, status: str, details: dict) -> JobRunLog:
        job = JobRunLog(job_name=job_name, status=status, details=details)
        self.db.add(job)
        self.db.flush()
        return job

    def get_job(self, job_id: int) -> JobRunLog | None:
        return self.db.get(JobRunLog, job_id)

    def update_job(self, job_id: int, status: str, details: dict | None = None) -> JobRunLog | None:
        job = self.get_job(job_id)
        if not job:
            return None
        job.status = status
        if details is not None:
            job.details = details
        self.db.flush()
        return job

    def log_ai_task(self, task_name: str, prompt: str, result: dict, status: str = "COMPLETED") -> AITaskLog:
        log = AITaskLog(task_name=task_name, prompt=prompt, result=result, status=status)
        self.db.add(log)
        self.db.flush()
        return log
