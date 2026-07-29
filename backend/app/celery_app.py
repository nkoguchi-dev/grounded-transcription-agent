import os

from celery import Celery

celery = Celery("grounded_transcription_agent", broker=os.environ["CELERY_BROKER_URL"])
celery.conf.update(
    task_serializer="json", accept_content=["json"], task_ignore_result=True
)
celery.conf.imports = ("app.worker",)
