from app.core.database import SessionLocal
from app.services.intelligence import IntelligenceService
from app.repositories.intelligence import IntelligenceRepository
from app.tasks.worker import celery_app


def _run_job(job_id: int, runner) -> dict:
    db = SessionLocal()
    repo = IntelligenceRepository(db)
    repo.update_job(job_id, "RUNNING")
    db.commit()
    try:
        result = runner(IntelligenceService(db))
        repo.update_job(
            job_id,
            "COMPLETED",
            {
                **(repo.get_job(job_id).details if repo.get_job(job_id) else {}),
                "result": result,
            },
        )
        db.commit()
        return result
    except Exception as exc:
        repo.update_job(
            job_id,
            "FAILED",
            {
                **(repo.get_job(job_id).details if repo.get_job(job_id) else {}),
                "error": str(exc),
            },
        )
        db.commit()
        raise
    finally:
        db.close()


@celery_app.task(name="search.reindex")
def reindex_search_task(job_id: int) -> dict:
    return _run_job(job_id, lambda service: service.search.reindex_all())


@celery_app.task(name="recommendation.rebuild")
def rebuild_recommendations_task(job_id: int) -> dict:
    return _run_job(job_id, lambda service: service.recommend_home(user_id=None))
