from typing import cast

from fastapi.testclient import TestClient

from app.application.jobs.create_job_use_case import CreateJobInput, CreateJobUseCase
from app.application.jobs.get_job_use_case import GetJobUseCase
from app.domain.jobs.model import Job
from app.presentation.api.app import create_api


class StubCreateJobUseCase:
    def execute(self, input_data: CreateJobInput) -> Job:
        return Job.create(input_data.duration_seconds, input_data.should_fail)

    def dispatch(self, job: Job) -> Job:
        return job.with_task_id("task-123")


class StubGetJobUseCase:
    def __init__(self, job: Job | None) -> None:
        self._job = job

    def execute(self, job_id: str) -> Job | None:
        if self._job is not None and self._job.id == job_id:
            return self._job
        return None


def test_create_job_api_contract_is_unchanged() -> None:
    app = create_api(
        cast(CreateJobUseCase, StubCreateJobUseCase()),
        cast(GetJobUseCase, StubGetJobUseCase(None)),
    )

    response = TestClient(app).post(
        "/api/jobs", json={"duration_seconds": 0, "should_fail": False}
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["duration_seconds"] == 0
    assert body["should_fail"] is False
    assert set(body) == {
        "id",
        "status",
        "duration_seconds",
        "should_fail",
        "result",
        "error_message",
        "created_at",
        "started_at",
        "finished_at",
    }


def test_get_job_api_contract_is_unchanged() -> None:
    job = Job.create(duration_seconds=1, should_fail=False).with_task_id("task-123")
    app = create_api(
        cast(CreateJobUseCase, StubCreateJobUseCase()),
        cast(GetJobUseCase, StubGetJobUseCase(job)),
    )
    client = TestClient(app)

    response = client.get(f"/api/jobs/{job.id}")
    missing_response = client.get("/api/jobs/missing")

    assert response.status_code == 200
    assert response.json()["id"] == job.id
    assert response.json()["status"] == "queued"
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Job not found"}
