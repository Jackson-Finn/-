from __future__ import annotations

from app.tasks.worker import celery_app


class TaskDispatcher:
    def dispatch_recommendation_rebuild(self, job_id: int) -> tuple[str, str | None]:
        try:
            result = celery_app.send_task(
                "recommendation.rebuild",
                args=[job_id],
                ignore_result=True,
                retry=False,
            )
            return "queued", result.id
        except Exception:
            from app.tasks.jobs import rebuild_recommendations_task

            rebuild_recommendations_task.run(job_id)
            return "completed", None

    def dispatch_search_reindex(self, job_id: int) -> tuple[str, str | None]:
        try:
            result = celery_app.send_task(
                "search.reindex",
                args=[job_id],
                ignore_result=True,
                retry=False,
            )
            return "queued", result.id
        except Exception:
            from app.tasks.jobs import reindex_search_task

            reindex_search_task.run(job_id)
            return "completed", None
