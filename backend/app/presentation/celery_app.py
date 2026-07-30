import os

from celery import Celery

EXECUTE_DUMMY_JOB_TASK_NAME = "app.presentation.celery_tasks.execute_dummy_job"

celery = Celery("grounded_transcription_agent", broker=os.environ["CELERY_BROKER_URL"])
celery.conf.update(
    task_serializer="json", accept_content=["json"], task_ignore_result=True
)
celery.conf.imports = ("app.presentation.celery_tasks",)
