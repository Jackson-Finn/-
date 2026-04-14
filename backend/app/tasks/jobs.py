from app.tasks.worker import celery_app


@celery_app.task(name="search.reindex")
def reindex_search() -> dict:
    return {"status": "completed", "job": "search.reindex"}


@celery_app.task(name="recommendation.rebuild")
def rebuild_recommendations() -> dict:
    return {"status": "completed", "job": "recommendation.rebuild"}

