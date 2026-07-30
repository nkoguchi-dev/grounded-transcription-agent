from typing import cast

from celery import Celery

from app.presentation.celery_app import EXECUTE_DUMMY_JOB_TASK_NAME


class CeleryJobPublisher:
    def __init__(self, celery: Celery) -> None:
        self._celery = celery

    def publish(self, job_id: str) -> str:
        task = self._celery.send_task(EXECUTE_DUMMY_JOB_TASK_NAME, args=[job_id])
        return cast(str, task.id)
