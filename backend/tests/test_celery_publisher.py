from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest
from celery import Celery
from kombu.exceptions import OperationalError

from app.application.jobs.errors import JobDispatchError
from app.presentation.celery_app import EXECUTE_DUMMY_JOB_TASK_NAME
from app.presentation.celery_publisher import CeleryJobPublisher


def test_celery_publisher_returns_external_task_id() -> None:
    celery = Mock(spec=Celery)
    celery.send_task.return_value = SimpleNamespace(id="task-123")

    task_id = CeleryJobPublisher(cast(Celery, celery)).publish("job-123")

    assert task_id == "task-123"
    celery.send_task.assert_called_once_with(
        EXECUTE_DUMMY_JOB_TASK_NAME, args=["job-123"]
    )


def test_celery_publisher_translates_known_broker_error() -> None:
    celery = Mock(spec=Celery)
    celery.send_task.side_effect = OperationalError("redis://secret-host")

    with pytest.raises(JobDispatchError, match="could not be dispatched") as raised:
        CeleryJobPublisher(cast(Celery, celery)).publish("job-123")

    assert isinstance(raised.value.__cause__, OperationalError)


def test_celery_publisher_does_not_translate_unexpected_error() -> None:
    celery = Mock(spec=Celery)
    celery.send_task.side_effect = RuntimeError("programming error")

    with pytest.raises(RuntimeError, match="programming error"):
        CeleryJobPublisher(cast(Celery, celery)).publish("job-123")
