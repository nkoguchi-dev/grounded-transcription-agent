from typing import cast

from celery import Celery
from celery.exceptions import CeleryError
from kombu.exceptions import OperationalError

from app.application.jobs.errors import JobDispatchError
from app.presentation.celery_app import EXECUTE_DUMMY_JOB_TASK_NAME


class CeleryJobPublisher:
    def __init__(self, celery: Celery) -> None:
        self._celery = celery

    def publish(self, job_id: str) -> str:
        try:
            task = self._celery.send_task(EXECUTE_DUMMY_JOB_TASK_NAME, args=[job_id])
        except (CeleryError, OperationalError) as error:
            # Queue-library details stop at this adapter boundary; callers only need
            # to know that dispatch failed and must not expose broker diagnostics.
            raise JobDispatchError("The job could not be dispatched") from error
        return cast(str, task.id)
