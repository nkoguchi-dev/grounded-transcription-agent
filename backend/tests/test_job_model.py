import pytest

from app.domain.jobs.model import Job, JobStatus


def test_job_completes_with_a_result() -> None:
    job = Job.create(0, False).start().succeed({"message": "done"})
    assert job.status is JobStatus.SUCCEEDED
    assert job.result == {"message": "done"}
    assert job.finished_at is not None


def test_queued_job_cannot_complete() -> None:
    with pytest.raises(ValueError, match="only running"):
        Job.create(0, False).succeed({})


def test_duration_is_bounded() -> None:
    with pytest.raises(ValueError, match="between 0 and 60"):
        Job.create(61, False)
